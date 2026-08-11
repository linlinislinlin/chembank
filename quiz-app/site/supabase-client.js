// Supabase 客户端封装（作业系统）
// - 通过 CDN 加载 supabase-js（无需打包器）
// - createClient 后暴露作业/学生/作答的常用操作
window.HomeworkDB = (() => {
  const cfg = window.SUPABASE_CONFIG || {};
  let client = null;

  function ready() {
    if (client) return client;
    if (!cfg.url || cfg.url.indexOf("你的项目") !== -1 || !cfg.anonKey || cfg.anonKey.indexOf("你的 anon") !== -1) {
      return null; // 未配置
    }
    client = window.supabase.createClient(cfg.url, cfg.anonKey);
    return client;
  }

  // ---- 作业 ----
  async function createAssignment(title, questionIds, dueAt) {
    const c = ready(); if (!c) throw new Error("Supabase 未配置");
    const { data, error } = await c.from("assignments").insert({
      title, question_ids: questionIds, due_at: dueAt || null
    }).select().single();
    if (error) throw error;
    return data;
  }

  async function listAssignments() {
    const c = ready(); if (!c) throw new Error("Supabase 未配置");
    const { data, error } = await c.from("assignments").select("*").order("created_at", { ascending: false });
    if (error) throw error;
    return data || [];
  }

  async function getAssignment(id) {
    const c = ready(); if (!c) throw new Error("Supabase 未配置");
    const { data, error } = await c.from("assignments").select("*").eq("id", id).maybeSingle();
    if (error) throw error;
    return data;
  }

  // ---- 学生（按 姓名+学号 幂等）----
  async function ensureStudent(name, studentNo, className) {
    const c = ready(); if (!c) throw new Error("Supabase 未配置");
    // 先查是否已存在
    const { data: found } = await c.from("students")
      .select("*").eq("name", name).eq("student_no", studentNo).maybeSingle();
    if (found) return found;
    // 不存在则插入；并发下重复插由 unique 兜底，冲突则再查一次
    const { data, error } = await c.from("students").insert({
      name, student_no: studentNo, class_name: className || null
    }).select().single();
    if (error) {
      const again = await c.from("students")
        .select("*").eq("name", name).eq("student_no", studentNo).maybeSingle();
      if (again) return again;
      throw error;
    }
    return data;
  }

  // ---- 作答（upsert：同一学生作业题重复交=更新）----
  async function recordAnswer(assignmentId, studentId, questionId, chosen, correct) {
    const c = ready(); if (!c) throw new Error("Supabase 未配置");
    const { error } = await c.from("answers").upsert({
      assignment_id: assignmentId,
      student_id: studentId,
      question_id: questionId,
      chosen, correct,
      answered_at: new Date().toISOString(),
    }, { onConflict: "assignment_id,student_id,question_id" });
    if (error) throw error;
  }

  // ---- 统计查询（教师端）----
  // ⚠️ 安全收紧后，anon 已无法直接 select students/answers（REST 返回空/报错）。
  //    教师读取统计改走 Supabase Edge Function（stats-edge）：
  //    - 用每次请求携带的服务端密钥（x-teacher-token）在函数内鉴权
  //    - 函数用 service_role 查库（绕开 RLS），浏览器拿不到 service_role
  //    返回结构与原 REST 一致：[ { ...answer字段, students:{name,student_no,class_name} } ]
  async function readTeacherStats(assignmentId, teacherToken) {
    const cfg = window.SUPABASE_CONFIG || {};
    const url = (cfg.statsEdgeUrl || "").replace(/\/+$/, "");
    if (!url) throw new Error("教师统计接口未配置（config.js 的 statsEdgeUrl）");
    if (!teacherToken) throw new Error("缺少教师口令");
    // 用 text/plain + body 携带口令，避免自定义 header 触发浏览器 CORS 预检
    // （否则 Supabase Edge Function 的 OPTIONS 预检可能被网关 500 拦截）。
    const resp = await fetch(url, {
      method: "POST",
      headers: { "content-type": "text/plain" },
      body: JSON.stringify({ assignment_id: assignmentId, teacher_token: teacherToken }),
    });
    if (resp.status === 401 || resp.status === 403) {
      throw new Error("教师口令错误或无权访问");
    }
    if (!resp.ok) {
      throw new Error("统计接口错误（HTTP " + resp.status + "）");
    }
    const data = await resp.json();
    return data.rows || [];
  }

  return { ready, createAssignment, listAssignments, getAssignment, ensureStudent, recordAnswer, readTeacherStats };
})();

// ---- 自由刷题（practice.html）专用封装 ----
// 安全模型：practice_logs 表对 anon 只开 insert/update（不能 select），
// 读回自己历史必须走 practice-log Edge Function（用姓名+学号鉴权，service_role 只读本人行）。
window.PracticeDB = (() => {
  const cfg = window.SUPABASE_CONFIG || {};

  // 调 Edge Function（text/plain + body，避免 CORS 预检，与 stats-edge 一致）
  async function callEdge(payload) {
    const url = (cfg.practiceEdgeUrl || "").replace(/\/+$/, "");
    if (!url) throw new Error("练习同步接口未配置（config.js 的 practiceEdgeUrl）");
    const resp = await fetch(url, {
      method: "POST",
      headers: { "content-type": "text/plain" },
      body: JSON.stringify(payload),
    });
    const data = await resp.json().catch(() => ({}));
    if (resp.status === 401 || resp.status === 403) throw new Error("身份校验失败，请核对姓名+学号");
    if (!resp.ok) throw new Error(data.error || ("练习接口错误（HTTP " + resp.status + "）"));
    return data;
  }

  // 幂等地找/建学生，返回 { id, name, student_no, class_name }
  async function resolveStudent(name, studentNo) {
    const d = await callEdge({ action: "resolveStudent", name, student_no: studentNo });
    return d.student;
  }

  // 读取该学生最近的练习记录（仅本人；同时本地也会再兜一层 localStorage）
  async function readHistory(name, studentNo, limit) {
    const d = await callEdge({ action: "getHistory", name, student_no: studentNo, limit: limit || 200 });
    return d.rows || [];
  }

  // 直接写入一条练习记录（anon insert/upsert 到 practice_logs）：
  // 每答一题同步一条；同一学生同一题重刷 = 更新（unique(student_id, question_id)）。
  async function recordPractice(studentId, log) {
    const c = ready();
    if (!c) throw new Error("Supabase 未配置");
    const { error } = await c.from("practice_logs").upsert({
      student_id: studentId,
      question_id: log.question_id,
      qtype: log.qtype,
      paper: log.paper || null,
      year: log.year || null,
      session: log.session || null,
      qno: log.qno || null,
      correct: log.correct,
      answered_at: new Date().toISOString(),
    }, { onConflict: "student_id,question_id" });
    if (error) throw error;
  }

  return { resolveStudent, readHistory, recordPractice };
})();
