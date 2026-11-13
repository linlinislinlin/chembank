-- 学生讨论区（评论 + 点赞 + 回复）建表
-- 依赖：public.students（由 homework-db.sql 创建，已存在）
create table if not exists public.question_comments (
  id          bigserial primary key,
  question_id text not null,
  student_id  bigint not null references public.students(id) on delete cascade,
  parent_id   bigint references public.question_comments(id) on delete cascade,
  body        text not null,
  created_at  timestamptz not null default now(),
  deleted     boolean not null default false
);

create index if not exists qc_question_idx
  on public.question_comments(question_id, id);

create table if not exists public.comment_likes (
  comment_id  bigint not null references public.question_comments(id) on delete cascade,
  student_id  bigint not null references public.students(id) on delete cascade,
  created_at  timestamptz not null default now(),
  primary key (comment_id, student_id)
);

alter table public.question_comments enable row level security;
alter table public.comment_likes enable row level security;

revoke all on public.question_comments from anon, authenticated;
revoke all on public.comment_likes from anon, authenticated;
