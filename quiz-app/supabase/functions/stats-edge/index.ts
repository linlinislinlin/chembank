// Supabase Edge Function: stats-edge
//
// 用途：教师端统计页 stats.html 读取统计数据的安全入口。
// 背景：安全收紧后，anon 已不能 select students/answers（REST 返回空/报错）。
//       教师浏览器同样用的是 anon key，无法再直接读这两张表。
//       因此由本函数充当「唯一读门」——用请求头携带的服务端密钥鉴权，
//       再用 service_role 查表（service_role 绕开 RLS，且绝不下发到浏览器）。
//
// 部署（一次性，需 Supabase CLI）：
//   supabase secrets set --env-name TEACHER_TOKEN --project-ref <ref> '你的教师密钥'
//   supabase functions deploy stats-edge --project-ref <ref> --no-verify-jwt
//   部署后把返回的 URL 填进 quiz-app/config.js 的 statsEdgeUrl。
//
// 调用：POST {statsEdgeUrl}/run
//   headers: { "content-type": "application/json", "x-teacher-token": "<TEACHER_TOKEN>" }
//   body:    { "assignment_id": <bigint> }
// 返回：
//   { "rows": [ { ...answer字段..., "students": { "name", "student_no", "class_name" } } ] }
//   与前端原来的 Supabase REST 联表返回结构保持一致，stats.html 无需改渲染逻辑。

import { createClient } from "jsr:@supabase/supabase-js@2";

const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  // service_role 绕过 RLS。此密钥只存于 Supabase secrets，绝不放进前端。
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

const TEACHER_TOKEN = Deno.env.get("TEACHER_TOKEN") ?? "";

Deno.serve(async (req: Request) => {
  const cors = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-teacher-token",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
  };
  if (req.method === "OPTIONS") {
    return new Response("ok", { status: 204, headers: cors });
  }
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "method not allowed" }), { status: 405, headers: { ...cors, "content-type": "application/json" } });
  }

  // 鉴权：校验服务端密钥（恒定时间比较，避免时序侧信道）
  const token = req.headers.get("x-teacher-token") ?? "";
  if (!TEACHER_TOKEN || !tokEq(token, TEACHER_TOKEN)) {
    return new Response(JSON.stringify({ error: "unauthorized" }), { status: 401, headers: { ...cors, "content-type": "application/json" } });
  }

  let body: { assignment_id?: number | string | null };
  try { body = await req.json(); } catch { body = {}; }
  const assignmentId = body.assignment_id;
  if (assignmentId == null) {
    return new Response(JSON.stringify({ error: "missing assignment_id" }), { status: 400, headers: { ...cors, "content-type": "application/json" } });
  }

  const { data: rows, error } = await supabase
    .from("answers")
    .select("*, students(name, student_no, class_name)")
    .eq("assignment_id", assignmentId);

  if (error) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500, headers: { ...cors, "content-type": "application/json" } });
  }
  return new Response(JSON.stringify({ rows: rows ?? [] }), { status: 200, headers: { ...cors, "content-type": "application/json" } });
});

// 恒定时间字符串比较，防止时序攻击
function tokEq(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}
