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

  function assignmentUrl() {
    const url = (cfg.assignmentEdgeUrl || "").replace(/\/+$/, "");
    if (!url) throw new Error("作业接口未配置（config.js 的 assignmentEdgeUrl）");
    return url;
  }

  async function callAssignment(payload) {
    const resp = await fetch(assignmentUrl(), {
      method: "POST",
      headers: { "content-type": "text/plain" },
      body: JSON.stringify(payload),
    });
    const data = await resp.json().catch(() => ({}));
    if (resp.status === 401 || resp.status === 403) {
      throw new Error(data.error || "教师口令错误或无权访问");
    }
    if (!resp.ok) throw new Error(data.error || ("作业接口错误（HTTP " + resp.status + "）"));
    return data;
  }

  async function createAssignment(input, teacherToken) {
    const data = await callAssignment({
      action: "create",
      teacher_token: teacherToken,
      title: input.title,
      instructions: input.instructions || "",
      due_at: input.dueAt || null,
      show_answers_after_submit: input.showAnswers !== false,
      show_explanations_after_submit: input.showExplanations !== false,
      questions: input.questions || [],
      programme: input.programme === "ig" ? "ig" : "as",
    });
    return data.assignment;
  }

  async function takeAssignment(id) {
    const data = await callAssignment({ action: "take", assignment_id: id });
    return data.assignment;
  }

  async function submitAssignment(input) {
    return callAssignment({
      action: "submit",
      assignment_id: input.assignmentId,
      name: input.name,
      student_no: input.studentNo,
      class_name: input.className || "",
      teacher_token: input.teacherToken || "",
      answers: input.answers || [],
    });
  }

  async function getSubmissionResult(input) {
    return callAssignment({
      action: "result",
      assignment_id: input.assignmentId,
      name: input.name,
      student_no: input.studentNo,
      class_name: input.className || "",
      teacher_token: input.teacherToken || "",
    });
  }

  async function listAssignments() {
    const c = ready(); if (!c) throw new Error("Supabase 未配置");
    let { data, error } = await c.from("assignments")
      .select("id, title, question_ids, question_snapshot, created_at, due_at, instructions, status, programme")
      .order("created_at", { ascending: false });
    if (error) {
      const retry = await c.from("assignments")
        .select("id, title, question_ids, created_at, due_at")
        .order("created_at", { ascending: false });
      if (retry.error) throw retry.error;
      return retry.data || [];
    }
    return data || [];
  }

  async function getAssignment(id) {
    return takeAssignment(id);
  }

  async function readTeacherStats(assignmentId, teacherToken) {
    const url = (cfg.statsEdgeUrl || "").replace(/\/+$/, "");
    if (!url) throw new Error("教师统计接口未配置（config.js 的 statsEdgeUrl）");
    if (!teacherToken) throw new Error("缺少教师口令");
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
    return { rows: data.rows || [], submissions: data.submissions || [] };
  }

  return {
    ready, createAssignment, listAssignments, getAssignment,
    takeAssignment, submitAssignment, getSubmissionResult, readTeacherStats,
  };
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
