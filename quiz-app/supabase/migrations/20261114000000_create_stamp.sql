-- 幸运转盘抽奖系统建表（stamp）
-- 依赖：public.assignments / public.students / public.submissions（均已存在）
-- 幂等：可反复执行。
-- 运行：Supabase → SQL Editor → 整段粘贴 → Run。
-- 然后部署 Edge Function `stamp`（见 supabase/functions/stamp/）。

-- ---------- 概率配置（单行，id 恒为 1）----------
-- 档位：谢谢参与(miss) / 1章 / 2章 / 3章，数值为百分比，后台可调。
create table if not exists public.stamp_config (
  id            smallint primary key default 1,
  prize_miss    numeric not null default 20,
  prize_1       numeric not null default 60,
  prize_2       numeric not null default 15,
  prize_3       numeric not null default 5,
  threshold_pct numeric not null default 60,   -- 达此准确率(%)才可抽
  enabled       boolean not null default true,
  updated_at    timestamptz not null default now(),
  constraint stamp_config_single_row check (id = 1)
);

-- ---------- 抽奖记录（一次作业 = 一行，防重复抽）----------
create table if not exists public.stamp_draws (
  id            bigserial primary key,
  assignment_id bigint not null references public.assignments(id) on delete cascade,
  student_id    bigint not null references public.students(id) on delete cascade,
  prize         text not null,                 -- 'miss' | '1' | '2' | '3'
  redeem_code   text not null unique,          -- 对奖码（老师兑奖用）
  redeemed      boolean not null default false,
  redeemed_at   timestamptz,
  drawn_at      timestamptz not null default now(),
  unique (assignment_id, student_id)           -- 防重复抽
);

create index if not exists stamp_draws_student_idx on public.stamp_draws(student_id, id);
create index if not exists stamp_draws_assignment_idx on public.stamp_draws(assignment_id, id);

alter table public.stamp_config enable row level security;
alter table public.stamp_draws enable row level security;

-- 匿名/普通用户完全不能碰这两张表，一切操作走 stamp Edge Function。
revoke all on public.stamp_config from anon, authenticated;
revoke all on public.stamp_draws from anon, authenticated;

-- 写入默认概率（谢谢参与 20 · 1章 60 · 2章 15 · 3章 5 · 分数线 60%）
insert into public.stamp_config (id, prize_miss, prize_1, prize_2, prize_3, threshold_pct, enabled)
values (1, 20, 60, 15, 5, 60, true)
on conflict (id) do nothing;
