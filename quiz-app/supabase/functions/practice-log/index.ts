// Supabase Edge Function: practice-log
//
// 用途：自由刷题页 practice.html 的“唯一读门”。
//   - resolveStudent：用 service_role 幂等地找/建学生，返回稳定 student_id。
//     （因为 hardening 已撤销 anon 对 students 的 select，前端的 ensureStudent
//       里“查重”部分会失败，回看由本函数负责解析身份。）
//   - getHistory：确认姓名+学号后，用 service_role 返回该学生最近的练习记录。
//
// 背景：practice_logs 表对 anon 只开 insert/update（不能 select），所以浏览器
//       无法直接 REST 读任何记录。回看自己历史必须走本函数；函数用 service_role
//       绕过 RLS 只读属于该学生的行。
//
// 鉴权模型（诚实说明）：纯静态无登录，本函数用「姓名+学号」确认“这是本人” ——
//   它只是弱口令，不是强认证。已知晓某人姓名+学号的人可读其记录（学生之间常互知学号）。
//   它的价值是：把「匿名爬 whole 表」堵死（REST 读关闭），同时让学生能回看自己。
//   要做到绝对只能本人看，需引入真实登录，超出本方案范围。
//
// 调用方式（与 stats-edge 一致，避免 CORS 预检）：
//   POST {practiceEdgeUrl}
//     headers: { "content-type": "text/plain" }
//     body(文本): JSON.stringify({ "action":"resolveStudent", "name":..., "student_no":... })
//              或 JSON.stringify({ "action":"getHistory", "name":..., "student_no":..., "limit":N })
//
// 返回：
//   resolveStudent -> { "student": { id, name, student_no, class_name } }
//   getHistory    -> { "rows": [ { question_id, qtype, paper, year, session, qno, correct, answered_at } ] }
//   auth 失败时 401，缺字段 400，服务端错误 500。
//
// 部署（一次性）：见 quiz-app/practice-logs.sql 末尾说明。

import { createClient } from "jsr:@supabase/supabase-js@2";

const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  // service_role 绕过 RLS。此密钥只存于 Supabase secrets，绝不放进前端。
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

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

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { status: 204, headers: CORS });
  }
  if (req.method !== "POST") {
    return json(405, { error: "method not allowed" });
  }

  let body: Record<string, unknown>;
  try { body = await req.json(); } catch { body = {}; }

  const action = clean(body.action);
  const name = clean(body.name);
  const studentNo = clean(body.student_no);

  if (action === "resolveStudent") {
    if (!name || !studentNo) return json(400, { error: "missing name or student_no" });
    const { data: found } = await supabase
      .from("students").select("id, name, student_no, class_name")
      .eq("name", name).eq("student_no", studentNo).maybeSingle();
    if (found) return json(200, { student: found });

    const { data: inserted, error: insErr } = await supabase
      .from("students").insert({ name, student_no: studentNo, class_name: null })
      .select("id, name, student_no, class_name").single();
    if (insErr) {
      // 并发下撞唯一键：再查一次
      const { data: again } = await supabase
        .from("students").select("id, name, student_no, class_name")
        .eq("name", name).eq("student_no", studentNo).maybeSingle();
      if (again) return json(200, { student: again });
      return json(500, { error: insErr.message });
    }
    return json(200, { student: inserted });
  }

  if (action === "getHistory") {
    if (!name || !studentNo) return json(400, { error: "missing name or student_no" });
    const limit = Math.max(1, Math.min(500, Math.floor(Number(body.limit) || 200)));

    const { data: stu } = await supabase
      .from("students").select("id").eq("name", name).eq("student_no", studentNo).maybeSingle();
    if (!stu) return json(401, { error: "unknown student (check name / student number)" });

    const { data: rows, error: rowsErr } = await supabase
      .from("practice_logs")
      .select("question_id, qtype, paper, year, session, qno, correct, answered_at")
      .eq("student_id", stu.id)
      .order("answered_at", { ascending: false })
      .limit(limit);
    if (rowsErr) return json(500, { error: rowsErr.message });
    return json(200, { rows: rows ?? [] });
  }

  return json(400, { error: "unknown action" });
});
