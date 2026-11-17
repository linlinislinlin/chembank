-- 印章账本：加 type 列（award 发章 / redeem 兑换扣章）
-- 幂等：可反复执行。
alter table public.stamp_ledger
  add column if not exists type text not null default 'award';

create index if not exists stamp_ledger_type_idx on public.stamp_ledger(type, id);
