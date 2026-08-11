# 自由刷题（practice）· 进度记录表 SQL

> 在 Supabase 左侧菜单 **SQL Editor** → 新建 query → 把下面整段粘贴进去 → **Run**。
> 只需运行一次；本文件已写成**幂等**（`if not exists` / `add column if not exists` / `drop policy if exists`），
> 重复执行不会报错，也不会丢数据。

## 安全模型（务必理解）

- 学生自由刷题，没有任何登录态，浏览器只持有公开的 `anon` key。
- `practice_logs` 沿用 `answers` 的收紧模型：
  - **anon 只能 insert / update（写），不能 select（读）** —— 彻底堵死“爬别人练习记录”。
  - 也就是说，任何人无法通过 REST 直接读出任何一行练习记录。
- 学生**回看自己的对错历史**，改走带 service_role 的 Edge Function `practice-log`
  （见 `supabase/functions/practice-log/`）。函数用姓名+学号确认“是本人”后，只返回该学生的记录。

## 残余风险（诚实说明）

纯静态 + 无登录，`姓名 + 学号` 只是“弱口令”。任何知道某学生姓名+学号的人，调用
`practice-log` 函数也能拿到该生记录（学生之间通常知道彼此的学号）。要做到“绝对只能本人看”，
必须引入真实登录（Auth / Google SSO），本方案不做。当前已做到的是：**匿名爬库被堵死**。

```sql
-- ============================================================
-- 自由刷题进度记录表 practice_logs（幂等，可反复执行）
-- 依赖：必须先有 public.students 表（由 homework-db.sql 创建）
-- ============================================================

-- 1) 建表（若不存在）
create table if not exists public.practice_logs (
  id           bigserial primary key,
  student_id   bigint not null references public.students(id) on delete cascade,
  question_id  text not null,             -- 来自 data.js 的 q.id（MCQ 或结构题通用）
  qtype        text not null check (qtype in ('mcq','structured')),
  paper        text,                      -- 例如 '12' / '22' / '41'
  year         int,
  session      text,                      -- 例如 'FM' / 'ON'
  qno          text,                      -- 题号，例如 '1' 或 '1(a)(i)'
  correct      boolean not null,          -- 答对(true) / 答错(false)
  answered_at  timestamptz not null default now(),
  -- 同一学生同一题只保留一条：重刷=更新（与 answers 一致）
  unique (student_id, question_id)
);

-- 2) RLS
alter table public.practice_logs enable row level security;

-- 幂等清掉旧策略（若重复运行）
drop policy if exists "anon can read practice_logs"  on public.practice_logs;
drop policy if exists "anon insert practice_logs"    on public.practice_logs;
drop policy if exists "anon update practice_logs"    on public.practice_logs;

-- 写：允许匿名插入与 upsert 更新（前端每答一题落一条）
create policy "anon insert practice_logs" on public.practice_logs for insert with check (true);
create policy "anon update practice_logs" on public.practice_logs for update using (true);

-- 3) 授权：只给 insert/update，不给 select（读彻底关闭）
revoke all on public.practice_logs from anon;
grant usage on schema public to anon;
grant insert, update on public.practice_logs to anon;

-- 4) 为“按学生回看历史”加索引（Edge Function 读取用）
create index if not exists practice_logs_student_ts_idx
  on public.practice_logs(student_id, answered_at desc);
```

## Edge Function：practice-log（回看自己历史的唯一读门）

文件：`quiz-app/supabase/functions/practice-log/index.ts`（参考 stats-edge 的既有模式）。

部署（一次性，需要 Supabase CLI 已登录）：
```bash
cd /Users/tsinglan-school/Desktop/题库/quiz-app
supabase functions deploy practice-log --project-ref jrobrcaiqtfwuomzycui
```
> 无需额外 secret（本函数只用 `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`，
> 这两个由 Supabase 运行时自动注入）。请在 Dashboard → Edge Functions →
> `practice-log` 确认 **Verify JWT = Off**（config.toml 已默认设置）。

部署后得到 URL：
`https://jrobrcaiqtfwuomzycui.functions.supabase.co/practice-log`，
把它填进 `quiz-app/config.js` 的 `practiceEdgeUrl`，再 `python3 quiz-app/build.py` + `./quiz-app/deploy.sh`。
