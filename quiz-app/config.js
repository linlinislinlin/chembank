// ============================================================
// Supabase 接入配置（作业系统）
//
// 在 Supabase 创建好项目后：
//   Project Settings(齿轮) → API → 复制下面的值填进来
//     - Project URL:      https://你的项目.supabase.co
//     - anon public key:  eyJhbGci...（一长串 jwt）
//
// 注意：这是「发布到公开仓库/GitHub Pages」的页面。
//       anon key 本身公开是 Supabase 官方允许的（它只暴露你给 anon 的权限），
//       但请不要把 service_role key 填进来！（service_role 拥有完全权限）
// ============================================================
window.SUPABASE_CONFIG = {
  url: "https://jrobrcaiqtfwuomzycui.supabase.co",
  anonKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impyb2JyY2FpcXRmd3VvbXp5Y3VpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODYzMTE4ODksImV4cCI6MjEwMTg4Nzg4OX0.gasJCYN8SSoj0gQRatf3Q7nqTMhoJhPzx5clWLDDfPU",

  // ---- 教师端（stats.html / assign.html）配置 ----
  // 🔒 安全边界说明：教师口令（TEACHER_TOKEN）**绝不放在本文件**，
  //    只存在 Supabase 的 secrets 里。老师在登录框里输入口令后，由
  //    stats-edge / assignment Edge Function 用 service_role 校验。
  //    前端不再保存、也不再本地比对任何教师口令（学生无法从源码拿到）。
  //
  //  - statsEdgeUrl：部署 stats-edge 函数后自动获得，形如
  //    https://<project-ref>.functions.supabase.co/stats-edge
  //    留空表示尚未部署，stats.html 会提示“接口未配置”。
  statsEdgeUrl: "https://jrobrcaiqtfwuomzycui.supabase.co/functions/v1/stats-edge",
  assignmentEdgeUrl: "https://jrobrcaiqtfwuomzycui.supabase.co/functions/v1/assignment",

  // ---- 自由刷题（practice.html）配置 ----
  // 回看自己的练习记录走 Edge Function practice-log（service_role + 姓名+学号鉴权）。
  // 部署见 quiz-app/practice-logs.sql 与 supabase/functions/practice-log/。
  // 留空表示尚未部署：practice 页会降级为"仅本地(localStorage)记录"，读写同步上不去但仍可用。
  practiceEdgeUrl: "https://jrobrcaiqtfwuomzycui.supabase.co/functions/v1/practice-log",
};
