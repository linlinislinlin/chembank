# 作业系统 · Supabase 建表 SQL

> 在 Supabase 左侧菜单 **SQL Editor** → 新建 query → 把下面整段粘贴进去 → **Run**。
> 只需在创建好的项目里**运行一次**。如果表已存在会报错 `already exists`，说明之前已建过，可忽略。

```sql
-- ============================================================
-- 作业系统三张表：assignments(作业) / students(学生) / answers(作答)
-- 说明：客户端(anon)可读作业列表与写作答；教师通过 anon 直写作业。
-- 学生表让不同学生各自提交(用身份证级唯一约束避免重复)。
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
-- RLS：允许 anon 读作业、读/插按学号区分的学生、读/写作答
-- 简单起见全部开放 select；insert 也放行（本工具是教学内用）。
-- 注意：生产请基于 auth 收紧。此处为了 MVP 易用而放开。
-- ============================================================
alter table public.assignments enable row level security;
alter table public.students enable row level security;
alter table public.answers enable row level security;

create policy "anon can read assignments" on public.assignments for select using (true);
create policy "anon can insert assignments" on public.assignments for insert with check (true);

create policy "anon can read students" on public.students for select using (true);
create policy "anon can insert students" on public.students for insert with check (true);

create policy "anon can read answers" on public.answers for select using (true);
create policy "anon can insert answers" on public.answers for insert with check (true);
create policy "anon can update answers" on public.answers for update using (true);

-- 可选：给 anon 授基础权限（若上面报权限错误再放开）
grant usage on schema public to anon;
grant select, insert, update on public.assignments, public.students, public.answers to anon;
```
