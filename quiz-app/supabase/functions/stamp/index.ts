// Supabase Edge Function: stamp
//
// 幸运转盘抽奖系统。
//   status      — 学生查自己某份作业的抽奖状态（是否已交、是否达标、是否已抽、结果）
//   draw        — 学生抽奖（服务端加密随机；必须已达标且未抽过）
//   teacherList — 教师拉全部抽奖记录（含姓名/学号/对奖码/是否已兑）
//   redeem      — 教师对奖（标记已盖章）
//   configGet   — 教师读概率配置
//   configSet   — 教师改概率配置
//
// 防作弊：概率与随机数都在服务端；学生端拿不到概率、改不了结果；
//         (assignment, student) 唯一约束 + 必须达标，刷不动、重复抽不了。
//
// 鉴权模型（与 practice-log / comments 一致）：纯静态无真登录，
// 「姓名+学号」是弱口令；教师操作走 TEACHER_TOKEN（存项目 secrets）。
//
// 调用方式：POST {stampEdgeUrl}
//   headers: { "content-type": "text/plain" }
//   body: JSON.stringify({ action, assignment_id?, name?, student_no?, class_name?, teacher_token?, draw_id?, prize_miss?, prize_1?, prize_2?, prize_3?, threshold_pct?, enabled? })
//
// 部署（一次性）：
//   supabase functions deploy stamp --project-ref jrobrcaiqtfwuomzycui
//   （TEACHER_TOKEN 已在项目 secrets 里，与 stats-edge / assignment 共用；
//     config.toml 已默认 verify_jwt = false）

import { createClient } from "jsr:@supabase/supabase-js@2";

const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

const TEACHER_TOKEN = Deno.env.get("TEACHER_TOKEN") ?? "";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function json(status: number, payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { ...CORS, "content-type": "application/json" },
  });
}

const clean = (s: unknown): string => String(s ?? "").trim();

function tokEq(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function teacherOk(token: unknown): boolean {
  const t = clean(token);
  return !!TEACHER_TOKEN && tokEq(t, TEACHER_TOKEN);
}

async function resolveStudent(name: string, studentNo: string, className: string) {
  const { data: found } = await supabase
    .from("students")
    .select("id")
    .eq("name", name)
    .eq("student_no", studentNo)
    .maybeSingle();
  if (found) return found;
  const { data: inserted, error } = await supabase
    .from("students")
    .insert({ name, student_no: studentNo, class_name: className || null })
    .select("id")
    .single();
  if (error) {
    const again = await supabase
      .from("students")
      .select("id")
      .eq("name", name)
      .eq("student_no", studentNo)
      .maybeSingle();
    if (again) return again;
    throw new Error(error.message);
  }
  return inserted;
}

const DEFAULT_CONFIG = {
  prize_miss: 20, prize_1: 60, prize_2: 15, prize_3: 5,
  threshold_pct: 60, enabled: true,
};

async function loadConfig() {
  const { data } = await supabase
    .from("stamp_config")
    .select("*")
    .eq("id", 1)
    .maybeSingle();
  return data ?? DEFAULT_CONFIG;
}

// 归一化权重（允许教师填的数字不严格等于 100，按比例缩放）
function weights(cfg: Record<string, unknown>): number[] {
  const raw = [
    Number(cfg.prize_miss ?? 0),
    Number(cfg.prize_1 ?? 0),
    Number(cfg.prize_2 ?? 0),
    Number(cfg.prize_3 ?? 0),
  ].map((n) => (Number.isFinite(n) && n > 0 ? n : 0));
  const total = raw.reduce((a, b) => a + b, 0);
  if (total <= 0) return [0.25, 0.5, 0.15, 0.1];
  return raw.map((n) => n / total);
}

const PRIZES = ["miss", "1", "2", "3"] as const;

function pickPrize(w: number[]): string {
  const arr = new Uint32Array(1);
  crypto.getRandomValues(arr);
  const r = arr[0] / 4294967296; // [0, 1)
  let acc = 0;
  for (let i = 0; i < w.length; i++) {
    acc += w[i];
    if (r < acc) return PRIZES[i];
  }
  return "3";
}

const CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"; // 去掉易混的 0/O/1/I/L
function genCode(): string {
  const arr = new Uint32Array(6);
  crypto.getRandomValues(arr);
  let s = "";
  for (let i = 0; i < 6; i++) s += CODE_ALPHABET[arr[i] % CODE_ALPHABET.length];
  return s;
}

// 给学生的公开配置（只含概率/分数线/开关，无任何秘密）
function publicConfig(cfg: Record<string, unknown>) {
  return {
    enabled: cfg.enabled !== false,
    threshold: Number(cfg.threshold_pct ?? 60) || 0,
    prizes: {
      miss: Number(cfg.prize_miss ?? 0),
      "1": Number(cfg.prize_1 ?? 0),
      "2": Number(cfg.prize_2 ?? 0),
      "3": Number(cfg.prize_3 ?? 0),
    },
  };
}

interface SubmissionRow { score?: unknown; total_score?: unknown; accuracy?: unknown }

async function eligibility(assignmentId: number, studentId: number, cfg: Record<string, unknown>) {
  const { data: sub } = await supabase
    .from("submissions")
    .select("score, total_score, accuracy")
    .eq("assignment_id", assignmentId)
    .eq("student_id", studentId)
    .maybeSingle();
  const row = sub as SubmissionRow | null;

  const threshold = Number(cfg.threshold_pct ?? 60) || 0;
  if (!row) {
    return { submitted: false, eligible: false, accuracy: null, total: null, threshold };
  }
  const total = Number(row.total_score ?? 0) || 0;
  const accuracy = Number(row.accuracy ?? 0) || 0;
  // 没有自动判分的 MCQ（total_score = 0）时，退化为「交了即可抽」。
  const eligible = total > 0 ? accuracy >= threshold : true;
  return { submitted: true, eligible, accuracy, total, threshold };
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { status: 204, headers: CORS });
  }
  if (req.method !== "POST") return json(405, { error: "method not allowed" });

  let body: Record<string, unknown>;
  try { body = await req.json(); } catch { body = {}; }

  const action = clean(body.action);

  try {
    // ---- 教师：读全部抽奖记录 ----
    if (action === "teacherList") {
      if (!teacherOk(body.teacher_token)) return json(401, { error: "unauthorized" });
      const limit = Math.min(Number(body.limit) || 500, 2000);
      const { data: rows, error } = await supabase
        .from("stamp_draws")
        .select("id, assignment_id, prize, redeem_code, redeemed, redeemed_at, drawn_at, students(name, student_no, class_name)")
        .order("id", { ascending: false })
        .limit(limit);
      if (error) return json(500, { error: error.message });
      const draws = (rows ?? []).map((r) => {
        const stu = r.students as { name?: string; student_no?: string; class_name?: string } | null;
        return {
          id: Number(r.id),
          assignment_id: Number(r.assignment_id),
          prize: r.prize,
          redeem_code: r.redeem_code,
          redeemed: r.redeemed === true,
          redeemed_at: r.redeemed_at,
          drawn_at: r.drawn_at,
          name: stu?.name ?? "",
          student_no: stu?.student_no ?? "",
          class_name: stu?.class_name ?? "",
        };
      });
      return json(200, { draws });
    }

    // ---- 教师：对奖（标记已盖章）----
    if (action === "redeem") {
      if (!teacherOk(body.teacher_token)) return json(401, { error: "unauthorized" });
      const drawId = Number(body.draw_id);
      if (!drawId) return json(400, { error: "missing draw_id" });
      const { data: d, error } = await supabase
        .from("stamp_draws")
        .update({ redeemed: true, redeemed_at: new Date().toISOString() })
        .eq("id", drawId)
        .select("id, redeemed")
        .maybeSingle();
      if (error) return json(500, { error: error.message });
      return json(200, { ok: true, draw: d });
    }

    // ---- 教师：读配置 ----
    if (action === "configGet") {
      if (!teacherOk(body.teacher_token)) return json(401, { error: "unauthorized" });
      const cfg = await loadConfig();
      return json(200, {
        prize_miss: Number(cfg.prize_miss),
        prize_1: Number(cfg.prize_1),
        prize_2: Number(cfg.prize_2),
        prize_3: Number(cfg.prize_3),
        threshold_pct: Number(cfg.threshold_pct),
        enabled: cfg.enabled !== false,
      });
    }

    // ---- 教师：改配置 ----
    if (action === "configSet") {
      if (!teacherOk(body.teacher_token)) return json(401, { error: "unauthorized" });
      const num = (v: unknown, fallback: number) => {
        const n = Number(v);
        return Number.isFinite(n) ? n : fallback;
      };
      const { data: cfg, error } = await supabase
        .from("stamp_config")
        .update({
          prize_miss: num(body.prize_miss, 20),
          prize_1: num(body.prize_1, 60),
          prize_2: num(body.prize_2, 15),
          prize_3: num(body.prize_3, 5),
          threshold_pct: num(body.threshold_pct, 60),
          enabled: body.enabled !== false,
          updated_at: new Date().toISOString(),
        })
        .eq("id", 1)
        .select("*")
        .maybeSingle();
      if (error) return json(500, { error: error.message });
      return json(200, { ok: true, config: cfg });
    }

    // ---- 学生：查状态 ----
    if (action === "status") {
      const assignmentId = Number(body.assignment_id);
      const name = clean(body.name);
      const studentNo = clean(body.student_no);
      if (!assignmentId) return json(400, { error: "missing assignment_id" });
      if (!name || !studentNo) return json(400, { error: "missing name or student_no" });

      const stu = await resolveStudent(name, studentNo, clean(body.class_name));
      const cfg = await loadConfig();
      const elig = await eligibility(assignmentId, Number(stu.id), cfg);

      const { data: existing } = await supabase
        .from("stamp_draws")
        .select("id, prize, redeem_code, redeemed, drawn_at")
        .eq("assignment_id", assignmentId)
        .eq("student_id", stu.id)
        .maybeSingle();

      return json(200, {
        config: publicConfig(cfg),
        submitted: elig.submitted,
        eligible: elig.eligible,
        accuracy: elig.accuracy,
        total: elig.total,
        threshold: elig.threshold,
        already_drawn: !!existing,
        draw: existing
          ? { prize: existing.prize, redeem_code: existing.redeem_code, redeemed: existing.redeemed === true, drawn_at: existing.drawn_at }
          : null,
      });
    }

    // ---- 学生：抽奖 ----
    if (action === "draw") {
      const assignmentId = Number(body.assignment_id);
      const name = clean(body.name);
      const studentNo = clean(body.student_no);
      if (!assignmentId) return json(400, { error: "missing assignment_id" });
      if (!name || !studentNo) return json(400, { error: "missing name or student_no" });

      const stu = await resolveStudent(name, studentNo, clean(body.class_name));
      const cfg = await loadConfig();
      if (cfg.enabled === false) return json(403, { error: "The lucky draw is currently closed." });

      const elig = await eligibility(assignmentId, Number(stu.id), cfg);
      if (!elig.submitted) return json(403, { error: "You must submit the homework before you can draw." });
      if (!elig.eligible) {
        return json(403, {
          error: `You need ${Number(cfg.threshold_pct ?? 60)}% to draw. Your accuracy is ${elig.accuracy}%.`,
          accuracy: elig.accuracy, threshold: elig.threshold,
        });
      }

      const { data: existing } = await supabase
        .from("stamp_draws")
        .select("id, prize, redeem_code, redeemed, drawn_at")
        .eq("assignment_id", assignmentId)
        .eq("student_id", stu.id)
        .maybeSingle();
      if (existing) {
        return json(200, {
          already_drawn: true,
          prize: existing.prize,
          redeem_code: existing.redeem_code,
          redeemed: existing.redeemed === true,
          drawn_at: existing.drawn_at,
          config: publicConfig(cfg),
        });
      }

      const prize = pickPrize(weights(cfg));
      const code = genCode();

      const { data: inserted, error } = await supabase
        .from("stamp_draws")
        .insert({
          assignment_id: assignmentId,
          student_id: stu.id,
          prize,
          redeem_code: code,
        })
        .select("id, prize, redeem_code, redeemed, drawn_at")
        .single();
      if (error) {
        // 并发/重复点击：撞唯一约束时，读回已存在的那行，避免多抽。
        const { data: again } = await supabase
          .from("stamp_draws")
          .select("id, prize, redeem_code, redeemed, drawn_at")
          .eq("assignment_id", assignmentId)
          .eq("student_id", stu.id)
          .maybeSingle();
        if (again) {
          return json(200, {
            already_drawn: true,
            prize: again.prize,
            redeem_code: again.redeem_code,
            redeemed: again.redeemed === true,
            drawn_at: again.drawn_at,
            config: publicConfig(cfg),
          });
        }
        return json(500, { error: error.message });
      }

      return json(200, {
        already_drawn: false,
        prize: inserted.prize,
        redeem_code: inserted.redeem_code,
        redeemed: false,
        drawn_at: inserted.drawn_at,
        config: publicConfig(cfg),
      });
    }

    return json(400, { error: "unknown action" });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return json(500, { error: msg });
  }
});
