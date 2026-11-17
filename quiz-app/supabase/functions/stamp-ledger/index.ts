// Supabase Edge Function: stamp-ledger
//
// 上课表现印章账本（老师手动加章）。与「幸运转盘」stamp 完全独立。
//
//   teacherAdd     — 教师给一个/多个学生加章（可批量，小组活动一次全加）
//   teacherSummary — 教师读全部学生的累计章数
//   teacherHistory — 教师读最近盖章流水（用于撤销误操作）
//   teacherUndo    — 教师撤销某笔盖章记录
//   studentStatus  — 学生查自己的累计章数与历史（姓名+学号弱鉴权）
//
// 鉴权模型（与 practice-log / comments / stamp 一致）：
//   教师操作走 TEACHER_TOKEN（存项目 secrets）；学生查自己走「姓名+学号」。
//   匿名无法写库（表对 anon 全关，写全走本函数）。
//
// 调用方式：POST {stampLedgerEdgeUrl}
//   headers: { "content-type": "text/plain" }
//   body: JSON.stringify({
//     action, teacher_token?,
//     entries?: [{ name, student_no, class_name, delta?, reason?, note? }],
//     name?, student_no?, class_name?,
//     ledger_id?, limit?
//   })
//
// 部署（一次性）：
//   supabase functions deploy stamp-ledger --project-ref jrobrcaiqtfwuomzycui
//   （TEACHER_TOKEN 已在项目 secrets 里，与 stats-edge / assignment / stamp 共用；
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

function teacherOk(token: unknown): boolean {
  const t = clean(token);
  return !!TEACHER_TOKEN && tokEq(t, TEACHER_TOKEN);
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

async function resolveStudent(name: string, studentNo: string, className: string) {
  const found = await findStudent(name, studentNo);
  if (found) return found;
  const { data: inserted, error } = await supabase
    .from("students")
    .insert({ name, student_no: studentNo, class_name: className || null })
    .select("id")
    .single();
  if (error) {
    const again = await findStudent(name, studentNo);
    if (again) return again;
    throw new Error(error.message);
  }
  return inserted;
}

type StudentEmbed = { name?: string; student_no?: string; class_name?: string } | null;

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { status: 204, headers: CORS });
  }
  if (req.method !== "POST") return json(405, { error: "method not allowed" });

  let body: Record<string, unknown>;
  try { body = await req.json(); } catch { body = {}; }

  const action = clean(body.action);

  try {
    // ---- 教师：给一个/多个学生加章 ----
    if (action === "teacherAdd") {
      if (!teacherOk(body.teacher_token)) return json(401, { error: "unauthorized" });
      const entries = Array.isArray(body.entries) ? body.entries : [];
      if (!entries.length) return json(400, { error: "missing entries" });

      const out: Record<string, unknown>[] = [];
      for (const e of entries) {
        const name = clean((e as Record<string, unknown>).name);
        const sno = clean((e as Record<string, unknown>).student_no);
        const cn = clean((e as Record<string, unknown>).class_name);
        const delta = Number((e as Record<string, unknown>).delta ?? 1);
        const reason = clean((e as Record<string, unknown>).reason) || "回答问题";
        const note = clean((e as Record<string, unknown>).note);
        if (!name || !sno) continue;
        if (!Number.isFinite(delta) || delta === 0) continue;

        const stu = await resolveStudent(name, sno, cn);
        const { data: row, error } = await supabase
          .from("stamp_ledger")
          .insert({ student_id: stu.id, type: "award", delta, reason, note: note || null })
          .select("id, type, delta, reason, note, created_at")
          .single();
        if (error) throw new Error(error.message);
        out.push({
          id: Number(row.id),
          name,
          student_no: sno,
          class_name: cn,
          type: row.type,
          delta: Number(row.delta),
          reason: row.reason,
          note: row.note,
          created_at: row.created_at,
        });
      }
      return json(200, { added: out.length, rows: out });
    }

    // ---- 教师：兑换（扣章并记录换成了什么）----
    if (action === "teacherRedeem") {
      if (!teacherOk(body.teacher_token)) return json(401, { error: "unauthorized" });
      const entries = Array.isArray(body.entries) ? body.entries : [];
      if (!entries.length) return json(400, { error: "missing entries" });

      const out: Record<string, unknown>[] = [];
      const skipped: Record<string, unknown>[] = [];
      for (const e of entries) {
        const name = clean((e as Record<string, unknown>).name);
        const sno = clean((e as Record<string, unknown>).student_no);
        const cn = clean((e as Record<string, unknown>).class_name);
        const stamps = Number((e as Record<string, unknown>).stamps ?? 4);
        const item = clean((e as Record<string, unknown>).item) || "Redeemed";
        if (!name || !sno) continue;
        if (!Number.isFinite(stamps) || stamps <= 0) continue;

        const stu = await resolveStudent(name, sno, cn);
        // 查余额，不足则跳过
        const { data: balanceRows } = await supabase
          .from("stamp_ledger")
          .select("delta")
          .eq("student_id", stu.id);
        const balance = (balanceRows ?? []).reduce((s, r) => s + Number(r.delta ?? 0), 0);
        if (balance < stamps) {
          skipped.push({ name, student_no: sno, balance, needed: stamps });
          continue;
        }
        const { data: row, error } = await supabase
          .from("stamp_ledger")
          .insert({ student_id: stu.id, type: "redeem", delta: -stamps, reason: item, note: null })
          .select("id, type, delta, reason, note, created_at")
          .single();
        if (error) throw new Error(error.message);
        out.push({
          id: Number(row.id),
          name,
          student_no: sno,
          class_name: cn,
          type: row.type,
          delta: Number(row.delta),
          reason: row.reason,
          note: row.note,
          created_at: row.created_at,
        });
      }
      return json(200, { redeemed: out.length, rows: out, skipped });
    }

    // ---- 教师：读全部学生累计章数 ----
    if (action === "teacherSummary") {
      if (!teacherOk(body.teacher_token)) return json(401, { error: "unauthorized" });
      const { data: rows, error } = await supabase
        .from("stamp_ledger")
        .select("student_id, delta, students(name, student_no, class_name)");
      if (error) return json(500, { error: error.message });

      const map = new Map<string, { student_id: number; name: string; student_no: string; class_name: string; total: number }>();
      for (const r of rows ?? []) {
        const stu = r.students as StudentEmbed;
        const key = stu?.student_no ?? String(r.student_id);
        if (!map.has(key)) {
          map.set(key, {
            student_id: Number(r.student_id),
            name: stu?.name ?? "",
            student_no: stu?.student_no ?? "",
            class_name: stu?.class_name ?? "",
            total: 0,
          });
        }
        map.get(key)!.total += Number(r.delta ?? 0);
      }
      const students = Array.from(map.values()).sort((a, b) =>
        (a.class_name || "").localeCompare(b.class_name || "") ||
        (a.student_no || "").localeCompare(b.student_no || ""));
      return json(200, { students });
    }

    // ---- 教师：最近盖章流水（撤销用，支持分页）----
    if (action === "teacherHistory") {
      if (!teacherOk(body.teacher_token)) return json(401, { error: "unauthorized" });
      const limit = Math.min(Number(body.limit) || 50, 500);
      const offset = Math.max(Number(body.offset) || 0, 0);

      // 总数（用于翻页）
      const { count } = await supabase
        .from("stamp_ledger")
        .select("id", { count: "exact", head: true });

      const { data: rows, error } = await supabase
        .from("stamp_ledger")
        .select("id, type, delta, reason, note, created_at, students(name, student_no, class_name)")
        .order("id", { ascending: false })
        .range(offset, offset + limit - 1);
      if (error) return json(500, { error: error.message });

      const history = (rows ?? []).map((r) => {
        const stu = r.students as StudentEmbed;
        return {
          id: Number(r.id),
          name: stu?.name ?? "",
          student_no: stu?.student_no ?? "",
          class_name: stu?.class_name ?? "",
          type: r.type,
          delta: Number(r.delta ?? 0),
          reason: r.reason,
          note: r.note,
          created_at: r.created_at,
        };
      });
      return json(200, { history, total: count ?? 0, offset, limit });
    }

    // ---- 教师：撤销某笔盖章 ----
    if (action === "teacherUndo") {
      if (!teacherOk(body.teacher_token)) return json(401, { error: "unauthorized" });
      const ledgerId = Number(body.ledger_id);
      if (!ledgerId) return json(400, { error: "missing ledger_id" });
      const { data: row } = await supabase
        .from("stamp_ledger")
        .delete()
        .eq("id", ledgerId)
        .select("id")
        .maybeSingle();
      return json(200, { ok: true, deleted: !!row });
    }

    // ---- 学生：查自己的累计章数与历史 ----
    if (action === "studentStatus") {
      const name = clean(body.name);
      const studentNo = clean(body.student_no);
      if (!name || !studentNo) return json(400, { error: "missing name or student_no" });

      const stu = await findStudent(name, studentNo);
      if (!stu) return json(200, { total: 0, history: [] });

      const { data: rows, error } = await supabase
        .from("stamp_ledger")
        .select("id, type, delta, reason, note, created_at")
        .eq("student_id", stu.id)
        .order("id", { ascending: false });
      if (error) return json(500, { error: error.message });

      const history = (rows ?? []).map((r) => ({
        type: r.type,
        delta: Number(r.delta ?? 0),
        reason: r.reason,
        note: r.note,
        created_at: r.created_at,
      }));
      const total = history.reduce((s, h) => s + h.delta, 0);
      return json(200, { total, history });
    }

    return json(400, { error: "unknown action" });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return json(500, { error: msg });
  }
});
