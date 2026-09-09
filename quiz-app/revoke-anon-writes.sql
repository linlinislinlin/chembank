-- ============================================================
-- 安全修复：撤销 anon 对 students / answers / practice_logs 的直接写权限
--
-- 背景：早期为了兼容「浏览器直接用 anon REST 写库」的历史设计，
--       hardening-rls.sql / practice-logs.sql 保留了 anon 对这几张表的
--       insert / update 权限。但现在所有学生写操作都已改走 Edge Function
--       （assignment / practice-log），它们用 service_role 写入，
--       service_role 绕过 RLS，**不受下面撤销影响**。
--
-- 因此这些 anon 写权限现在是「多余的」，并且是一个真实漏洞：
--       学生拿到公开的 anonKey 后，可以直接往 answers 表 insert/update 假数据，
--       污染教师的统计页成绩（甚至伪造别人答案）。
--
-- 本文件做的事：
--   1) REVOKE anon 对 students / answers / practice_logs 的 insert / update
--   2) 删除对应的 anon 写策略（幂等）
--   3) 保留 assignments 的 anon 读/写（作业列表非隐私，实际写入也已走 Edge Function）
--
-- 幂等：可反复执行，不会报错，也不会丢数据。
-- 运行：Supabase 控制台 → SQL Editor → 新建 query → 整段粘贴 → Run。
-- ============================================================

-- ---------- 第一步：撤销 anon 的直接写权限（关键步骤） ----------
revoke insert on public.students from anon;

revoke insert on public.answers from anon;
revoke update on public.answers from anon;

revoke insert on public.practice_logs from anon;
revoke update on public.practice_logs from anon;

-- ---------- 第二步：删除对应的 anon 写策略（幂等） ----------
drop policy if exists "anon can insert students"    on public.students;
drop policy if exists "anon can insert answers"     on public.answers;
drop policy if exists "anon can update answers"     on public.answers;
drop policy if exists "anon insert practice_logs"   on public.practice_logs;
drop policy if exists "anon update practice_logs"   on public.practice_logs;

-- ---------- 校验（可选，跑完看结果） ----------
-- 下面的查询应返回空（说明 anon 已无这些写权限）。
-- select grantee, table_name, privilege_type
-- from information_schema.role_table_grants
-- where grantee = 'anon'
--   and table_name in ('students','answers','practice_logs')
--   and privilege_type in ('INSERT','UPDATE');
