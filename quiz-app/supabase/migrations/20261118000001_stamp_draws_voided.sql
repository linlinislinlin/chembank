-- 抽奖对奖增强：
--   1) stamp_draws 加 voided 列（失效：违规/迟交，不给章）
--   2) 记录「对奖时自动加的章数」到 stamp_ledger（由 stamp 函数写入）
-- 幂等：可反复执行。
alter table public.stamp_draws
  add column if not exists voided boolean not null default false;

create index if not exists stamp_draws_voided_idx on public.stamp_draws(voided, id);
