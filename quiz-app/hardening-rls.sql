-- ============================================================
-- 作业系统 · 安全加固（收紧 anon 读取权限）· v2
--
-- ⚠️⚠️ 已过时 / 勿再单独执行 ⚠️⚠️
-- 本文件是早期「v1 → v2」过渡期的加固脚本。它的授权部分会
-- **重新授予** anon 对 answers 的 update、students 的 insert、
-- assignments 的 insert（见文件末尾），这与最终安全模型冲突：
--   - homework-v2.sql     已经 REVOKE 了这些写权限（更严格）
--   - revoke-anon-writes.sql 又进一步撤销了 students/answers/
--     practice_logs 的 anon 写权限
-- 因此若你**再次执行本文件**，会把这些已撤销的写权限重新加回来，
-- 重新打开「学生用 anonKey 直接往 answers 表写假数据」的漏洞。
--
-- 正确的执行顺序（新部署时）：
--   1) homework-db.sql        建表
--   2) homework-v2.sql        增量列 + 收紧
--   3) practice-logs.sql      练习记录表
--   4) revoke-anon-writes.sql 最终撤销 anon 写权限
-- 本文件保留仅作历史参考，不要重复执行。
--
-- 背景：原 homework-db.sql 给了 anon 对 students/answers 的
--       select 权限（`grant select, insert, update ... to anon`），
--       并且 RLS 策略是 `for select using (true)`，导致任何拿到
--       公开 Supabase URL + anonKey 的人都能读出所有学生姓名/学号
--       + 每条作答（隐私泄露）。
--
-- v2 相对 v1 的关键修正：除了撤销 RLS 里的读策略，还必须
--  **REVOKE 表级别的 select 权限**，否则 PostgREST 仍能以 anon
--   身份读到全部行（v1 只 drop 策略、只 grant insert/update，
--    没撤销 select，所以没堵住）。
--
-- 本文件做的事（历史）：
--  1) 强制开启三张表的 RLS
--  2) 撤销所有旧的读/写策略，只留安全模型需要的
--  3) REVOKE anon 对 students / answers 的 SELECT（关键）
--  4) 保留 anon 的 insert（学生提交）+ answers 的 update（upsert）
--  5) assignments 维持可读可写（作业列表非隐私）
--
-- 幂等：本文件可反复执行，不会重复报错，也不会 drop 表 / 丢数据。
-- 运行：Supabase 控制台 → SQL Editor → 新建 query → 整段粘贴 → Run。
-- ============================================================

-- ---------- 第一步：确保 RLS 已开启（重复执行无副作用） ----------
alter table public.assignments enable row level security;
alter table public.students   enable row level security;
alter table public.answers    enable row level security;

-- ---------- 第二步：撤销既有策略（幂等：存在才删） ----------
drop policy if exists "anon can read students"     on public.students;
drop policy if exists "anon can read answers"      on public.answers;
drop policy if exists "anon can insert students"   on public.students;
drop policy if exists "anon can insert answers"    on public.answers;
drop policy if exists "anon can update answers"    on public.answers;
drop policy if exists "anon can read assignments"  on public.assignments;
drop policy if exists "anon can insert assignments" on public.assignments;

-- ---------- 第三步：撤销 anon 对隐私表的 SELECT 权限（关键步骤）----------
-- v1 漏了这一步，导致仍能读取全部数据。
revoke select on public.students from anon;
revoke select on public.answers  from anon;

-- ---------- 第四步：按安全模型重建策略 ----------
-- 学生表：只允许 anon 插入（学生提交身份所需），禁止 anon 读取。
create policy "anon can insert students" on public.students for insert with check (true);

-- 作答表：学生作答必须能写：
--  - insert：首次提交答案
--  - update（using true）：recordAnswer 的 upsert 撞唯一键时转 UPDATE；
--    因 anon 无会话身份、RLS 无法按行为区分匿名用户，只能维持全放开
--    update，但已彻底关闭 select（读）。想要"只能改自己的行"需引入
--    登录态，纯静态 + anon REST 做不到，属已知权衡。
create policy "anon can insert answers" on public.answers for insert with check (true);
create policy "anon can update answers" on public.answers for update using (true);

-- 作业表：保持可读可写（homework 页要读作业、assign 页要读写作业；
--         作业标题/题号非隐私）。题目内容在公开 data.js，不受影响。
create policy "anon can read assignments"  on public.assignments for select using (true);
create policy "anon can insert assignments" on public.assignments for insert with check (true);

-- ---------- 第五步：授权（仅确保需要的权限存在） ----------
grant usage on schema public to anon;
-- 只给 anon：students(insert)、answers(insert, update)、assignments(select, insert)
grant select, insert on public.assignments to anon;
grant insert on public.students to anon;
grant insert, update on public.answers to anon;
