-- ============================================================
-- 学生讨论区（评论 + 点赞 + 回复）建表 SQL
-- 依赖：必须先有 public.students 表（由 homework-db.sql 创建）
-- 幂等：可反复执行，不删表、不丢已有评论。
-- 运行：Supabase → SQL Editor → 整段粘贴 → Run。
--
-- 安全模型：
--   - 两张表对 anon / authenticated 完全关闭（revoke all，无任何 RLS 策略）。
--   - 所有读写都走 Edge Function `comments`（service_role 绕过 RLS）。
--   - 评论公开给学生看，但服务端只下发「学号后4位」，绝不返回姓名。
-- ============================================================

-- 1) 评论表（评论 + 回复合一：parent_id 为空 = 顶层评论，非空 = 回复）
create table if not exists public.question_comments (
  id          bigserial primary key,
  question_id text not null,             -- 来自 data.js 的 q.id
  student_id  bigint not null references public.students(id) on delete cascade,
  parent_id   bigint references public.question_comments(id) on delete cascade,
  body        text not null,
  created_at  timestamptz not null default now(),
  deleted     boolean not null default false   -- 教师软删（不当评论）
);

create index if not exists qc_question_idx
  on public.question_comments(question_id, id);

-- 2) 点赞表（一人对一条评论只能点一次，可取消）
create table if not exists public.comment_likes (
  comment_id  bigint not null references public.question_comments(id) on delete cascade,
  student_id  bigint not null references public.students(id) on delete cascade,
  created_at  timestamptz not null default now(),
  primary key (comment_id, student_id)
);

-- 3) RLS 开启 + 彻底关闭 anon / authenticated 的直接访问（读写全走 Edge Function）
alter table public.question_comments enable row level security;
alter table public.comment_likes enable row level security;

revoke all on public.question_comments from anon, authenticated;
revoke all on public.comment_likes from anon, authenticated;
