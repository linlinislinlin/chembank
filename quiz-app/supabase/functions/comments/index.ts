// Supabase Edge Function: comments
//
// 学生讨论区（评论 + 点赞 + 回复），按题目组织。
//   list   — 读某题的评论树 + 点赞数（无需鉴权；带身份时额外标出"我点过"）
//   post   — 发评论 / 回复（姓名+学号弱鉴权，服务端幂等找/建学生）
//   like   — 点赞 / 取消（姓名+学号弱鉴权）
//   delete — 教师软删（teacher_token）
//
// 隐私约定：评论只下发「学号后4位」，绝不返回姓名；任何前端都拿不到 name。
// 鉴权模型（与 practice-log 一致的诚实说明）：纯静态无真登录，「姓名+学号」
// 是弱口令、非强认证；但已做到——匿名无法写库（表对 anon 全关，写全走本函数）。
//
// 调用方式：POST {commentsEdgeUrl}
//   headers: { "content-type": "text/plain" }
//   body: JSON.stringify({ action, question_id?, name?, student_no?, body?, parent_id?, comment_id?, like?, teacher_token? })
//
// 部署（一次性）：
//   supabase functions deploy comments --project-ref jrobrcaiqtfwuomzycui
//   （TEACHER_TOKEN 已在项目 secrets 里，与 stats-edge / assignment 共用；
//     config.toml 已默认 verify_jwt = false）

import { createClient } from "jsr:@supabase/supabase-js@2";

const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

const TEACHER_TOKEN = Deno.env.get("TEACHER_TOKEN") ?? "";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function json(status: number, payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { ...CORS, "content-type": "application/json" },
  });
}

const clean = (s: unknown): string => String(s ?? "").trim();

function tokEq(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

// 只暴露学号后4位（大写），绝不返回姓名。
function last4(s: unknown): string {
  const str = String(s ?? "");
  return str ? str.slice(-4).toUpperCase() : "????";
}

async function findStudent(name: string, studentNo: string) {
  const { data } = await supabase
    .from("students")
    .select("id")
    .eq("name", name)
    .eq("student_no", studentNo)
    .maybeSingle();
  return data;
}

async function resolveStudent(name: string, studentNo: string) {
  const found = await findStudent(name, studentNo);
  if (found) return found;
  const { data: inserted, error } = await supabase
    .from("students")
    .insert({ name, student_no: studentNo, class_name: null })
    .select("id")
    .single();
  if (error) {
    const again = await findStudent(name, studentNo);
    if (again) return again;
    throw new Error(error.message);
  }
  return inserted;
}

async function likeCounts(commentIds: number[]): Promise<Map<number, number>> {
  const m = new Map<number, number>();
  if (!commentIds.length) return m;
  const { data } = await supabase
    .from("comment_likes")
    .select("comment_id")
    .in("comment_id", commentIds);
  for (const row of data ?? []) {
    const n = Number(row.comment_id);
    m.set(n, (m.get(n) ?? 0) + 1);
  }
  return m;
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { status: 204, headers: CORS });
  }
  if (req.method !== "POST") return json(405, { error: "method not allowed" });

  let body: Record<string, unknown>;
  try { body = await req.json(); } catch { body = {}; }

  const action = clean(body.action);

  try {
    // ---- 读评论树 ----
    if (action === "list") {
      const questionId = clean(body.question_id);
      if (!questionId) return json(400, { error: "missing question_id" });

      const { data: rows, error } = await supabase
        .from("question_comments")
        // 显式指定外键名，避免 comment_likes 同时关联两张表导致的嵌入歧义
        .select("id, question_id, parent_id, body, created_at, students!question_comments_student_id_fkey(student_no)")
        .eq("question_id", questionId)
        .eq("deleted", false)
        .order("id", { ascending: true });
      if (error) return json(500, { error: error.message });

      const ids = (rows ?? []).map((r) => Number(r.id));
      const likes = await likeCounts(ids);

      // 带身份时标出"我点过哪些"（只查不建，读操作不产生新学生行）
      const myLikes = new Set<number>();
      const name = clean(body.name);
      const studentNo = clean(body.student_no);
      if (name && studentNo) {
        const stu = await findStudent(name, studentNo);
        if (stu) {
          const { data: mine } = await supabase
            .from("comment_likes")
            .select("comment_id")
            .eq("student_id", stu.id)
            .in("comment_id", ids);
          for (const row of mine ?? []) myLikes.add(Number(row.comment_id));
        }
      }

      const comments = (rows ?? []).map((r) => {
        const n = Number(r.id);
        const stu = r.students as { student_no?: string } | null;
        return {
          id: n,
          question_id: r.question_id,
          parent_id: r.parent_id == null ? null : Number(r.parent_id),
          body: r.body,
          created_at: r.created_at,
          student_no: last4(stu && stu.student_no),
          likes: likes.get(n) ?? 0,
          liked_by_me: myLikes.has(n),
        };
      });
      return json(200, { comments });
    }

    // ---- 发评论 / 回复 ----
    if (action === "post") {
      const questionId = clean(body.question_id);
      const name = clean(body.name);
      const studentNo = clean(body.student_no);
      const text = clean(body.body).slice(0, 2000);
      const parentId = body.parent_id == null ? null : Number(body.parent_id);
      if (!questionId) return json(400, { error: "missing question_id" });
      if (!name || !studentNo) return json(400, { error: "missing name or student_no" });
      if (!text) return json(400, { error: "empty comment" });

      // 回复必须挂在同题的某条评论下
      if (parentId != null) {
        const { data: parent } = await supabase
          .from("question_comments")
          .select("id, question_id")
          .eq("id", parentId)
          .maybeSingle();
        if (!parent || parent.question_id !== questionId) {
          return json(400, { error: "invalid parent_id" });
        }
      }

      const stu = await resolveStudent(name, studentNo);
      const { data: c, error } = await supabase
        .from("question_comments")
        .insert({ question_id: questionId, student_id: stu.id, parent_id: parentId, body: text })
        .select("id, question_id, parent_id, body, created_at")
        .single();
      if (error || !c) return json(500, { error: error?.message || "insert failed" });

      return json(200, {
        comment: {
          id: Number(c.id),
          question_id: c.question_id,
          parent_id: c.parent_id == null ? null : Number(c.parent_id),
          body: c.body,
          created_at: c.created_at,
          student_no: last4(studentNo),
          likes: 0,
          liked_by_me: false,
        },
      });
    }

    // ---- 点赞 / 取消 ----
    if (action === "like") {
      const commentId = Number(body.comment_id);
      const name = clean(body.name);
      const studentNo = clean(body.student_no);
      const want = body.like === true;
      if (!commentId) return json(400, { error: "missing comment_id" });
      if (!name || !studentNo) return json(400, { error: "missing name or student_no" });

      const stu = await resolveStudent(name, studentNo);
      const { data: existing } = await supabase
        .from("comment_likes")
        .select("comment_id")
        .eq("comment_id", commentId)
        .eq("student_id", stu.id)
        .maybeSingle();

      if (want && !existing) {
        const { error } = await supabase
          .from("comment_likes")
          .insert({ comment_id: commentId, student_id: stu.id });
        if (error) return json(500, { error: error.message });
      } else if (!want && existing) {
        const { error } = await supabase
          .from("comment_likes")
          .delete()
          .eq("comment_id", commentId)
          .eq("student_id", stu.id);
        if (error) return json(500, { error: error.message });
      }

      const counts = await likeCounts([commentId]);
      return json(200, { likes: counts.get(commentId) ?? 0, liked_by_me: want });
    }

    // ---- 教师审核：拉全部评论流（无需逐题找 ID）----
    if (action === "moderate") {
      const token = clean(body.teacher_token);
      if (!TEACHER_TOKEN || !tokEq(token, TEACHER_TOKEN)) {
        return json(401, { error: "unauthorized" });
      }
      const limit = Math.min(Number(body.limit) || 200, 1000);
      const { data: rows, error } = await supabase
        .from("question_comments")
        .select("id, question_id, parent_id, body, created_at, students!question_comments_student_id_fkey(student_no)")
        .eq("deleted", false)
        .order("id", { ascending: false })
        .limit(limit);
      if (error) return json(500, { error: error.message });

      const ids = (rows ?? []).map((r) => Number(r.id));
      const likes = await likeCounts(ids);

      const comments = (rows ?? []).map((r) => {
        const stu = r.students as { student_no?: string } | null;
        return {
          id: Number(r.id),
          question_id: r.question_id,
          parent_id: r.parent_id == null ? null : Number(r.parent_id),
          body: r.body,
          created_at: r.created_at,
          student_no: last4(stu && stu.student_no),
          likes: likes.get(Number(r.id)) ?? 0,
        };
      });
      return json(200, { comments });
    }

    // ---- 教师软删 ----
    if (action === "delete") {
      const token = clean(body.teacher_token);
      if (!TEACHER_TOKEN || !tokEq(token, TEACHER_TOKEN)) {
        return json(401, { error: "unauthorized" });
      }
      const commentId = Number(body.comment_id);
      if (!commentId) return json(400, { error: "missing comment_id" });
      const { error } = await supabase
        .from("question_comments")
        .update({ deleted: true })
        .eq("id", commentId);
      if (error) return json(500, { error: error.message });
      return json(200, { ok: true });
    }

    return json(400, { error: "unknown action" });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return json(500, { error: msg });
  }
});
