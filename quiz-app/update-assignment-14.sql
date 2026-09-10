-- ============================================================
-- 归类 + 改名：把已发布的 ID 14（IGCSE 2.4 离子键作业）
-- 归到「2 Atoms, elements and compounds → 2.4 Ions and ionic bonds」
--
-- 为什么用 SQL：安全修复后 anon 对 public.assignments 已无 update 权限，
-- 且 assignment Edge Function 只有 create / take / result / submit，
-- 没有改名接口。所以改名只能在 Supabase 控制台跑 SQL。
--
-- 运行：Supabase 控制台 → SQL Editor → New query → 整段粘贴 → Run
-- 幂等：可反复执行。
-- ============================================================

-- ---------- 第 1 步：看现在长什么样 ----------
select id, title, programme, status, instructions
from public.assignments
where id = 14;

-- ---------- 第 2 步：改名 + 写作业说明 ----------
update public.assignments
set
  title = 'IGCSE 2.4 Ions and ionic bonds',
  instructions = 'CIE 0620 IGCSE Chemistry (Extended) · Unit 2 Atoms, elements and compounds · 2.4 Ions and ionic bonds · 15 questions · 23 marks · Suggested time: 30 minutes. Section A: 9 multiple-choice questions (9 marks). Section B: structured questions (14 marks). A Periodic Table may be used.'
where id = 14;

-- ---------- 第 3 步：确认结果 ----------
-- 标题应变成 IGCSE 2.4 Ions and ionic bonds；
-- 如果这里返回 0 行，说明 ID 14 已被删除 —— 告诉 AI，改为重新发布。
select id, title, programme, status
from public.assignments
where id = 14;
