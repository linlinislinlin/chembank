-- ============================================================
-- 作业系统 v2 · 增量（考试模式：先交再看答案 + 服务端判分）
--
-- 依赖：先有 homework-db.sql 的 assignments / students / answers。
-- 幂等：可反复执行，不删表、不丢已有作业。
-- 运行：Supabase → SQL Editor → 整段粘贴 → Run。
--
-- 然后部署 Edge Function `assignment`（见 supabase/functions/assignment/）。
-- ============================================================

-- ---------- assignments：说明、状态、交后是否显示答案、公开题面快照 ----------
alter table public.assignments
  add column if not exists instructions text,
  add column if not exists status text not null default 'published',
  add column if not exists show_answers_after_submit boolean not null default true,
  add column if not exists show_explanations_after_submit boolean not null default true,
  add column if not exists question_snapshot jsonb not null default '[]'::jsonb,
  add column if not exists programme text not null default 'as';

-- 旧行补默认值（若某列刚加上来已有 default，这里无害）
update public.assignments
   set status = coalesce(status, 'published')
 where status is null;

-- ---------- 标准答案（anon 完全不能读）----------
create table if not exists public.assignment_answer_keys (
  assignment_id bigint not null references public.assignments(id) on delete cascade,
  question_id   text not null,
  qtype         text not null default 'mcq',
  ms_answer     text,
  ms_img        text,
  marks         numeric,
  primary key (assignment_id, question_id)
);

alter table public.assignment_answer_keys enable row level security;

-- ---------- 整卷提交汇总 ----------
create table if not exists public.submissions (
  id            bigserial primary key,
  assignment_id bigint not null references public.assignments(id) on delete cascade,
  student_id    bigint not null references public.students(id) on delete cascade,
  submitted_at  timestamptz not null default now(),
  score         numeric not null default 0,
  total_score   numeric not null default 0,
  accuracy      numeric not null default 0,
  unique (assignment_id, student_id)
);

alter table public.submissions enable row level security;

-- ---------- answers：结构题可暂不自动判 ----------
alter table public.answers alter column correct drop not null;
alter table public.answers add column if not exists score numeric;

-- ---------- 收紧 anon：作业创建/判分/读答案都走 Edge Function ----------
revoke select on public.assignment_answer_keys from anon, authenticated;
revoke insert, update, delete on public.assignment_answer_keys from anon, authenticated;

revoke select, insert, update, delete on public.submissions from anon, authenticated;

-- 学生不能再自己写 correct（防改分）。作答改由 assignment-submit 用 service_role 写入。
revoke insert, update, select on public.answers from anon, authenticated;

-- 布置作业改走 assignment-create，避免任何人往 assignments 插行。
revoke insert, update, delete on public.assignments from anon, authenticated;
-- 仍允许 anon 读作业元数据（标题/题号/公开快照，不含标准答案）
grant select on public.assignments to anon;

-- 学生身份仍可由 practice-log / assignment 函数用 service_role 写入；
-- 前端不再直接 insert students（ensureStudent 已不可靠）。
revoke select on public.students from anon, authenticated;
-- 保留 insert 以免旧页立刻坏掉；新页不再用它。
grant insert on public.students to anon;

drop policy if exists "anon can insert assignments" on public.assignments;
drop policy if exists "anon can insert answers" on public.answers;
drop policy if exists "anon can update answers" on public.answers;

-- keys / submissions：无 anon 策略 = 全拒（RLS 开着且没有 policy）
drop policy if exists "anon can read keys" on public.assignment_answer_keys;
drop policy if exists "anon can read submissions" on public.submissions;
