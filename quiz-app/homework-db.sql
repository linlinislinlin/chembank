# 作业系统 · Supabase 建表 SQL

> 在 Supabase 左侧菜单 **SQL Editor** → 新建 query → 把下面整段粘贴进去 → **Run**。
> 只需在创建好的项目里**运行一次**。如果表已存在会报错 `already exists`，说明之前已建过，可忽略。

```sql
-- ============================================================
-- 作业系统三张表：assignments(作业) / students(学生) / answers(作答)
-- 说明：学生端可读作业列表、可写入学生与作答；作业列表对 anon 开放。
-- 学生表让不同学生各自提交(用身份证级唯一约束避免重复)。
--
-- ⚠️ 安全：建表后请务必再运行 hardening-rls.sql，
--    它会撤销 students / answers 的 anon select（防隐私泄露）。
--    教师端统计改走带密钥校验的 Edge Function，见 hardening-rls.sql 说明。
-- ============================================================

-- 1) 作业表
create table public.assignments (
  id          bigserial primary key,
  title       text not null,
  question_ids jsonb not null default '[]'::jsonb,  -- 题目 id 数组，来自 quiz-app/src/data.js 的 q.id
  created_at  timestamptz not null default now(),
  due_at      timestamptz
);

-- 2) 学生表
create table public.students (
  id          bigserial primary key,
  name        text not null,
  student_no  text not null,      -- 学号
  class_name  text,               -- 班级/组，可空
  created_at  timestamptz not null default now(),
  unique (name, student_no)       -- 同一姓名+学号视为同一学生
);

-- 3) 作答表
create table public.answers (
  id            bigserial primary key,
  assignment_id bigint not null references public.assignments(id) on delete cascade,
  student_id    bigint not null references public.students(id) on delete cascade,
  question_id   text not null,             -- 来自 data.js 的 q.id
  chosen        text not null,             -- 学生选的 A/B/C/D
  correct       boolean not null,          -- 是否答对
  answered_at   timestamptz not null default now(),
  -- 同一学生同一作业同一题只允许一条记录（重复交=更新）
  unique (assignment_id, student_id, question_id)
);

-- ============================================================
-- RLS：按「作业可读可写、学生/作答只写不读」的收紧模型建立策略。
--  - assignments：anon 保持 select+insert（homework/assign 页所需；非隐私）
--  - students  ：anon 仅 insert（学生提交身份），禁止 select
--  - answers   ：anon 仅 insert + update（作答写入与重复提交的 upsert），
--                禁止 select（读他人作答 → 堵死）
--
-- ⚠️ 新版安全模型已内置到下面这段里。若你之前已经在用旧的
--    “anon 全开放 select”版本，请**再运行一次 hardening-rls.sql**，
--    它会幂等地撤销旧的 select 策略、重建为上面这个收紧模型。
-- ============================================================
alter table public.assignments enable row level security;
alter table public.students enable row level security;
alter table public.answers enable row level security;

create policy "anon can read assignments" on public.assignments for select using (true);
create policy "anon can insert assignments" on public.assignments for insert with check (true);

create policy "anon can insert students" on public.students for insert with check (true);

create policy "anon can insert answers" on public.answers for insert with check (true);
create policy "anon can update answers" on public.answers for update using (true);

-- 授权（不授予 students/answers 的 select：读这两张表被彻底关闭）
grant usage on schema public to anon;
grant select, insert on public.assignments to anon;
grant insert on public.students to anon;
grant insert, update on public.answers to anon;
```
