-- ============================================================
-- 作业系统 · 安全加固（收紧 anon 读取权限）
--
-- 背景：原 homework-db.sql 里 students / answers 两张表对 anon
--       完全开放 select（`for select using (true)`），导致任何拿到
--       公开 Supabase URL + anonKey 的人都能通过 REST 读出
--       所有学生姓名/学号 + 每条作答记录（隐私泄露）。
--
-- 本文件做三件事：
--  1) 撤销 students / answers 的 anon select 权限（读他人数据 → 堵死）
--  2) 保留 students / answers 的 anon insert（学生作答仍能写入）
--  3) 保留 answers 的 anon update（recordAnswer 的 upsert(onConflict)
--     在撞唯一键时需要执行 UPDATE，缺了它会断掉学生重复提交）
--     assignments 维持原样（作业标题/题号非隐私，homework/assign 页需要读，
--     题目 id 本身在公开 data.js 里）。
--
-- 安全边界说明（务必读）：
--  - 收紧后「用 anon key 直接 REST select students/answers」会返回空/报错。
--  - 教师端 stats.html 靠一个标注了口令的接口（Supabase Edge Function）
--    读取统计数据；该接口用 service_role + 服务端密钥鉴权，绕开 RLS。
--    详见 quiz-app/supabase/functions/stats-edge/README.md。
--
-- 幂等性：本段可反复执行，不会重复报错，也不会 drop 表 / 丢数据。
-- 运行：Supabase 控制台 → SQL Editor → 新建 query → 整段粘贴 → Run。
-- ============================================================

-- ---------- 第一步：确保 RLS 已开启（重复执行无副作用） ----------
alter table public.assignments enable row level security;
alter table public.students   enable row level security;
alter table public.answers    enable row level security;

-- ---------- 第二步：撤销旧策略（幂等：存在才删）
-- 无论之前用的是旧的“全开放 select”版本，还是新版 homework-db.sql，
-- 这里都先把本文件要管理的策略整体摘掉，再按安全模型重建。
drop policy if exists "anon can read students" on public.students;
drop policy if exists "anon can read answers"  on public.answers;
drop policy if exists "anon can insert students" on public.students;
drop policy if exists "anon can insert answers"  on public.answers;
drop policy if exists "anon can update answers"  on public.answers;
drop policy if exists "anon can read assignments"  on public.assignments;
drop policy if exists "anon can insert assignments" on public.assignments;

-- ---------- 第三步：按收紧后的模型重建策略 ----------

-- 学生表：只允许 anon 插入（学生提交身份所需），禁止 anon 读取。
create policy "anon can insert students" on public.students for insert with check (true);

-- 作答表：学生作答必须能写：
--  - insert：首次提交答案
--  - update（using true）：recordAnswer 的 upsert 撞唯一键时转 UPDATE；
--    因 anon 无会话身份、RLS 无法区分“是不是自己的行”，只能维持全放开
--    update，但已彻底关闭 select（读）。想要“只允许改自己的行”需引入
--    登录态，纯静态 + anon REST 做不到，属已知权衡。由此彻底关闭读。
create policy "anon can insert answers" on public.answers for insert with check (true);
create policy "anon can update answers" on public.answers for update using (true);

-- 作业表：保持可读可写（homework 页要读作业、assign 页要读写作业；
--         作业标题/题号非隐私）。题目内容在公开 data.js，不受影响。
create policy "anon can read assignments"  on public.assignments for select using (true);
create policy "anon can insert assignments" on public.assignments for insert with check (true);

-- ---------- 第四步：授权（幂等；直接 REVOKE 会导致报错，故只需确保
--          需要的权限存在，缺失时授权一下即可） ----------
grant usage on schema public to anon;
-- 仅给 anon：students(insert)、answers(insert, update)、assignments(select, insert)
grant select, insert on public.assignments to anon;
grant insert on public.students to anon;
grant insert, update on public.answers to anon;
