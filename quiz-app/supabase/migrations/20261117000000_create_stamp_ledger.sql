-- 上课表现印章账本建表（stamp-ledger）
-- 老师手动加章 / 学生查自己的章。与「幸运转盘」stamp 完全独立。
-- 幂等：可反复执行。
-- 运行：Supabase → SQL Editor → 整段粘贴 → Run。
-- 然后部署 Edge Function `stamp-ledger`（见 supabase/functions/stamp-ledger/）。

-- ---------- 盖章流水（每一笔都记，不存总数）----------
create table if not exists public.stamp_ledger (
  id         bigserial primary key,
  student_id bigint not null references public.students(id) on delete cascade,
  delta      int not null default 1,          -- 通常是 +1，改错时可为负
  reason     text not null default '回答问题', -- 回答问题 / 小组活动 / 作业优秀 / 其他
  note       text,
  created_at timestamptz not null default now()
);

create index if not exists stamp_ledger_student_idx on public.stamp_ledger(student_id, id);
create index if not exists stamp_ledger_created_idx on public.stamp_ledger(created_at desc);

alter table public.stamp_ledger enable row level security;

-- 匿名/普通用户完全不能碰这张表，一切操作走 stamp-ledger Edge Function。
revoke all on public.stamp_ledger from anon, authenticated;
