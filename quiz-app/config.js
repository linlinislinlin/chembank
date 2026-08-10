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
  anonKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impyb2JyY2FpcXRmd3VvbXp5Y3VpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODYzMTE4ODksImV4cCI6MjEwMTg4Nzg4OX0.gasJCYN8SSoj0gQRatf3Q7nqTMhoJhPzx5clWLDDfPU"
};
