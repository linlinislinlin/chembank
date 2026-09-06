// Supabase Edge Function: assignment
//
// 作业考试模式的唯一服务端入口。
//   create — 教师口令；写入作业 + 公开题面快照 + 私有标准答案
//   take   — 学生开卷；只返回题面（无 ms_answer / ms_img）
//   submit — 学生交卷；服务端判 MCQ，写 answers + submissions，再按开关返回答案
//   result — 已交过则返回上次成绩（不可改卷）
//
// POST，content-type: text/plain，body 为 JSON 字符串（避免 CORS 预检）。
//
// 部署：
//   supabase functions deploy assignment --project-ref jrobrcaiqtfwuomzycui
//   TEACHER_TOKEN 已在项目 secrets 里（与 stats-edge 共用）。

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

type IncomingQ = {
  id?: unknown;
  type?: unknown;
  marks?: unknown;
  year?: unknown;
  session?: unknown;
  paper?: unknown;
  question?: unknown;
  topics?: unknown;
  figures?: unknown;
  paper_img?: unknown;
  body?: unknown;
  ms_answer?: unknown;
  ms_img?: unknown;
};

function publicQuestion(q: IncomingQ) {
  const id = clean(q.id);
  const qtype = clean(q.type) === "structured" ? "structured" : "mcq";
  const figures = Array.isArray(q.figures)
    ? q.figures.map((x) => clean(x)).filter(Boolean)
    : [];
  const topics = Array.isArray(q.topics)
    ? q.topics.map((x) => clean(x)).filter(Boolean)
    : [];
  return {
    id,
    type: qtype,
    marks: q.marks == null || q.marks === "" ? 1 : Number(q.marks) || 1,
    year: q.year ?? null,
    session: q.session ?? null,
    paper: q.paper ?? null,
    question: q.question ?? null,
    topics,
    figures,
    paper_img: clean(q.paper_img) || null,
    body: clean(q.body).slice(0, 400) || null,
  };
}

function keyRow(assignmentId: number, q: IncomingQ, pub: ReturnType<typeof publicQuestion>) {
  return {
    assignment_id: assignmentId,
    question_id: pub.id,
    qtype: pub.type,
    ms_answer: pub.type === "mcq" ? clean(q.ms_answer).toUpperCase() : null,
    ms_img: pub.type === "structured" ? (clean(q.ms_img) || null) : null,
    marks: pub.marks,
  };
}

async function resolveStudent(name: string, studentNo: string, className: string) {
  const { data: found } = await supabase
    .from("students")
    .select("id, name, student_no, class_name")
    .eq("name", name)
    .eq("student_no", studentNo)
    .maybeSingle();
  if (found) return found;
  const { data: inserted, error } = await supabase
    .from("students")
    .insert({ name, student_no: studentNo, class_name: className || null })
    .select("id, name, student_no, class_name")
    .single();
  if (error) {
    const { data: again } = await supabase
      .from("students")
      .select("id, name, student_no, class_name")
      .eq("name", name)
      .eq("student_no", studentNo)
      .maybeSingle();
    if (again) return again;
    throw new Error(error.message);
  }
  return inserted;
}

async function loadAssignment(id: number) {
  const { data, error } = await supabase
    .from("assignments")
    .select("*")
    .eq("id", id)
    .maybeSingle();
  if (error) throw new Error(error.message);
  return data;
}

function publicAssignment(ass: Record<string, unknown>) {
  const snap = Array.isArray(ass.question_snapshot) ? ass.question_snapshot : [];
  return {
    id: ass.id,
    title: ass.title,
    instructions: ass.instructions || "",
    due_at: ass.due_at,
    status: ass.status || "published",
    programme: String(ass.programme || "as").toLowerCase() === "ig" ? "ig" : "as",
    show_answers_after_submit: ass.show_answers_after_submit !== false,
    show_explanations_after_submit: ass.show_explanations_after_submit !== false,
    questions: snap,
  };
}

async function buildResult(
  ass: Record<string, unknown>,
  studentId: number,
  includeKeys: boolean,
) {
  const { data: sub } = await supabase
    .from("submissions")
    .select("*")
    .eq("assignment_id", ass.id)
    .eq("student_id", studentId)
    .maybeSingle();
  if (!sub) return null;

  const { data: answers } = await supabase
    .from("answers")
    .select("question_id, chosen, correct, score")
    .eq("assignment_id", ass.id)
    .eq("student_id", studentId);

  let keys: Record<string, { ms_answer: string | null; ms_img: string | null; qtype: string; marks: number }> = {};
  if (includeKeys) {
    const { data: keyRows } = await supabase
      .from("assignment_answer_keys")
      .select("question_id, ms_answer, ms_img, qtype, marks")
      .eq("assignment_id", ass.id);
    for (const k of keyRows || []) {
      keys[k.question_id] = k;
    }
  }

  const snap = Array.isArray(ass.question_snapshot) ? ass.question_snapshot : [];
  if (!includeKeys) {
    return {
      already_submitted: true,
      review: false,
      assignment: { id: ass.id, title: ass.title },
      submitted_at: sub.submitted_at,
      items: [],
    };
  }
  const items = (answers || []).map((a) => {
    const q = snap.find((x: { id?: string }) => x.id === a.question_id) || { id: a.question_id };
    const k = keys[a.question_id];
    const item: Record<string, unknown> = {
      question_id: a.question_id,
      chosen: a.chosen,
      is_correct: a.correct,
      score: a.score,
      marks: (q as { marks?: number }).marks ?? k?.marks ?? 1,
      type: (q as { type?: string }).type || k?.qtype || "mcq",
    };
    if (includeKeys && k) {
      if (ass.show_answers_after_submit !== false && k.ms_answer) item.ms_answer = k.ms_answer;
      if (ass.show_explanations_after_submit !== false && k.ms_img) item.ms_img = k.ms_img;
    }
    return item;
  });

  return {
    already_submitted: true,
    review: true,
    assignment: publicAssignment(ass),
    score: Number(sub.score),
    total_score: Number(sub.total_score),
    accuracy: Number(sub.accuracy),
    submitted_at: sub.submitted_at,
    items,
  };
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { status: 204, headers: CORS });
  }
  if (req.method !== "POST") return json(405, { error: "method not allowed" });

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    body = {};
  }

  const action = clean(body.action);

  try {
    if (action === "create") {
      const token = clean(body.teacher_token);
      if (!TEACHER_TOKEN || !tokEq(token, TEACHER_TOKEN)) {
        return json(401, { error: "unauthorized" });
      }
      const title = clean(body.title);
      const questions = Array.isArray(body.questions) ? (body.questions as IncomingQ[]) : [];
      if (!title) return json(400, { error: "missing title" });
      if (!questions.length) return json(400, { error: "missing questions" });

      const pubs = questions.map(publicQuestion).filter((q) => q.id);
      if (!pubs.length) return json(400, { error: "no valid question ids" });

      const dueAt = clean(body.due_at) || null;
      const programme = clean(body.programme).toLowerCase() === "ig" ? "ig" : "as";
      const { data: ass, error } = await supabase
        .from("assignments")
        .insert({
          title,
          instructions: clean(body.instructions) || null,
          question_ids: pubs.map((q) => q.id),
          question_snapshot: pubs,
          due_at: dueAt,
          status: "published",
          programme,
          show_answers_after_submit: body.show_answers_after_submit !== false,
          show_explanations_after_submit: body.show_explanations_after_submit !== false,
        })
        .select("id, title, programme")
        .single();
      if (error || !ass) return json(500, { error: error?.message || "insert failed" });

      const keys = questions.map((q, i) => keyRow(ass.id, q, pubs[i]));
      const { error: keyErr } = await supabase.from("assignment_answer_keys").insert(keys);
      if (keyErr) return json(500, { error: keyErr.message });

      return json(200, { assignment: ass });
    }

    if (action === "take") {
      const id = Number(body.assignment_id);
      if (!id) return json(400, { error: "missing assignment_id" });
      const ass = await loadAssignment(id);
      if (!ass) return json(404, { error: "Assignment not found or has been deleted" });
      const pub = publicAssignment(ass);
      if (!pub.questions.length && Array.isArray(ass.question_ids) && ass.question_ids.length) {
        return json(409, {
          error: "This assignment was created with the old homework tool. Please ask your teacher to create it again.",
        });
      }
      return json(200, { assignment: pub });
    }

    if (action === "result" || action === "submit") {
      const id = Number(body.assignment_id);
      const name = clean(body.name);
      const studentNo = clean(body.student_no);
      if (!id) return json(400, { error: "missing assignment_id" });
      if (!name || !studentNo) return json(400, { error: "missing name or student_no" });

      const ass = await loadAssignment(id);
      if (!ass) return json(404, { error: "Assignment not found or has been deleted" });

      const isTester = studentNo === "TESTER" || name.toLowerCase() === "tester";
      if (isTester) {
        const token = clean(body.teacher_token);
        if (!TEACHER_TOKEN || !tokEq(token, TEACHER_TOKEN)) {
          return json(401, { error: "Tester is for teachers only" });
        }
      }

      const stu = await resolveStudent(name, studentNo, clean(body.class_name));
      const showKeys = ass.show_answers_after_submit !== false || ass.show_explanations_after_submit !== false;

      if (action === "result") {
        const existing = await buildResult(ass, stu.id, showKeys);
        return json(200, existing || { already_submitted: false, assignment: publicAssignment(ass) });
      }

      const existing = await buildResult(ass, stu.id, false);
      if (existing) return json(200, existing);

      const snap = Array.isArray(ass.question_snapshot) ? ass.question_snapshot : [];
      const incoming = Array.isArray(body.answers) ? (body.answers as { question_id?: unknown; chosen?: unknown }[]) : [];
      const byQ = new Map(incoming.map((a) => [clean(a.question_id), clean(a.chosen)]));

      for (const q of snap) {
        const chosen = byQ.get(q.id) || "";
        if (!chosen) return json(400, { error: "Please answer every question before submitting." });
      }

      const { data: keyRows, error: keyErr } = await supabase
        .from("assignment_answer_keys")
        .select("question_id, qtype, ms_answer, ms_img, marks")
        .eq("assignment_id", id);
      if (keyErr) return json(500, { error: keyErr.message });
      const keys = new Map((keyRows || []).map((k) => [k.question_id, k]));

      let score = 0;
      let total = 0;
      let graded = 0;
      let ok = 0;
      const rows = [];

      for (const q of snap) {
        const key = keys.get(q.id);
        const chosen = byQ.get(q.id) || "";
        const marks = Number(key?.marks ?? q.marks ?? 1) || 1;
        const qtype = key?.qtype || q.type || "mcq";
        let correct: boolean | null = null;
        let qScore = 0;
        if (qtype === "mcq" && key?.ms_answer) {
          total += marks;
          graded += 1;
          correct = chosen.toUpperCase() === String(key.ms_answer).toUpperCase();
          if (correct) {
            qScore = marks;
            score += marks;
            ok += 1;
          }
        }
        rows.push({
          assignment_id: id,
          student_id: stu.id,
          question_id: q.id,
          chosen,
          correct,
          score: qScore,
          answered_at: new Date().toISOString(),
        });
      }

      const accuracy = graded ? Math.round((ok / graded) * 1000) / 10 : 0;

      const { error: ansErr } = await supabase.from("answers").upsert(rows, {
        onConflict: "assignment_id,student_id,question_id",
      });
      if (ansErr) return json(500, { error: ansErr.message });

      const { error: subErr } = await supabase.from("submissions").insert({
        assignment_id: id,
        student_id: stu.id,
        score,
        total_score: total,
        accuracy,
      });
      if (subErr) return json(500, { error: subErr.message });

      return json(200, await buildResult(ass, stu.id, showKeys));
    }

    return json(400, { error: "unknown action" });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return json(500, { error: msg });
  }
});
