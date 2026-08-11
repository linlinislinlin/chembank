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

  // ---- 教师端（stats.html）配置 ----
  // 🔓 重要提醒：下面两个值都被打包进「公开的 GitHub Pages」前端，
  //    任何学生都能在浏览器里看到它们。它们只能挡“顺手点进来看”的人，
  //    **不能当作安全边界**。真正挡住数据泄露的是两道防线：
  //      1) hardening-rls.sql：撤销了 students/answers 的 anon 读取（REST 直接 select 返回空）
  //      2) stats-edge Edge Function：用 service_role + 服务端密钥 TEACHER_TOKEN 校验，
  //         TEACHER_TOKEN 只存在 Supabase 的 secrets 里，绝不出现在本文件。
  //
  //  - statsToken：仅用于 stats.html 前端登录界面做一次“顺手校验”，
  //    可改成任意你想要的字符串（改完记得部署后生效）。
  //  - statsEdgeUrl：部署 stats-edge 函数后自动获得，形如
  //    https://<project-ref>.functions.supabase.co/stats-edge
  //    留空表示尚未部署，stats.html 会提示“接口未配置”。
  statsToken: "123456",
  statsEdgeUrl: "https://jrobrcaiqtfwuomzycui.supabase.co/functions/v1/stats-edge",

  // ---- 自由刷题（practice.html）配置 ----
  // 回看自己的练习记录走 Edge Function practice-log（service_role + 姓名+学号鉴权）。
  // 部署见 quiz-app/practice-logs.sql 与 supabase/functions/practice-log/。
  // 留空表示尚未部署：practice 页会降级为"仅本地(localStorage)记录"，读写同步上不去但仍可用。
  practiceEdgeUrl: "https://jrobrcaiqtfwuomzycui.supabase.co/functions/v1/practice-log",
};
