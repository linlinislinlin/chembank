// Supabase Edge Function: stats-edge
//
// 用途：教师端统计页 stats.html 读取统计数据的安全入口。
// 背景：安全收紧后，anon 已不能 select students/answers（REST 返回空/报错）。
//       教师浏览器同样用的是 anon key，无法再直接读这两张表。
//       因此由本函数充当「唯一读门」——校验服务端密钥后再用 service_role 查表
//       （service_role 绕开 RLS，且绝不下发到浏览器）。
//
// 调用方式（重要）：
//   前端 POST 到 statsEdgeUrl，格式如下 —— 把口令放在 body 的 teacher_token，
//   content-type 用 text/plain。这样是「简单请求」，浏览器不会触发 CORS 预检
//   （OPTIONS），从而避开 Supabase Edge Function 网关在预检阶段的 500 问题。
//   POST {statsEdgeUrl}
//     headers: { "content-type": "text/plain" }
//     body:    JSON.stringify({ "assignment_id": <bigint>, "teacher_token": "<TEACHER_TOKEN>" })
//
// 返回：
//   { "rows": [ { ...answer字段..., "students": { "name", "student_no", "class_name" } } ] }
//   与前端原来的 Supabase REST 联表返回结构保持一致，stats.html 无需改渲染逻辑。
//
// 部署（一次性，需 Supabase CLI）：
//   cd quiz-app
//   supabase secrets set TEACHER_TOKEN='你的教师密钥' --project-ref <ref>
//   supabase functions deploy stats-edge --project-ref <ref>
//   （quiz-app/supabase/config.toml 已为它配置 verify_jwt = false）

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

  let body: { assignment_id?: number | string | null; teacher_token?: string };
  try { body = await req.json(); } catch { body = {}; }

  // 鉴权：校验服务端密钥（恒定时间比较，避免时序侧信道）。
  // 口令放在 POST body 的 teacher_token 字段里，而不是自定义 header，
  // 这样前端用 text/plain 简单请求即可避免触发浏览器 CORS 预检（OPTIONS 500 问题）。
  const token = body.teacher_token ?? "";
  if (!TEACHER_TOKEN || !tokEq(token, TEACHER_TOKEN)) {
    return new Response(JSON.stringify({ error: "unauthorized" }), { status: 401, headers: { ...cors, "content-type": "application/json" } });
  }

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
