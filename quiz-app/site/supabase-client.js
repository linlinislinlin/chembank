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
    if (!url) throw new Error("Homework service is not configured");
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
      throw new Error(data.error || "Wrong teacher token or no access");
    }
    if (!resp.ok) throw new Error(data.error || ("Homework service error (HTTP " + resp.status + ")"));
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

  // 老师清除「某个学生在某份作业」的作答记录（让他重做）。
  // dryRun=true 只预演（返回会删多少行），不传或 false 才真删。
  async function clearStudentAttempt(assignmentId, studentId, teacherToken, dryRun) {
    return callAssignment({
      action: "clearAttempt",
      assignment_id: assignmentId,
      student_id: studentId,
      dry_run: dryRun === true,
      teacher_token: teacherToken || "",
    });
  }

  // 老师用 Tester 试跑后，清除自己在**这一份作业**下的记录，以便再走一遍学生流程。
  // 只影响 Tester 预览账号，不动任何真实学生数据（后端还会再校验一次口令）。
  async function resetTesterAttempt(assignmentId, teacherToken) {
    return callAssignment({
      action: "resetTester",
      assignment_id: assignmentId,
      teacher_token: teacherToken || "",
    });
  }

  async function listAssignments() {
    const c = ready(); if (!c) throw new Error("Cloud service is not configured");
    // 列表页只拉元数据：不取 question_snapshot（每份作业的完整题面，体积大，
    // 作业越攒越多会让统计页/布置页首屏越来越慢）。快照改由
    // getAssignmentSnapshot() 在真正打开某一份作业时按需获取。
    let { data, error } = await c.from("assignments")
      .select("id, title, question_ids, created_at, due_at, instructions, status, programme")
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

  // 按需拉取单份作业的题面快照（列表页不再携带，避免整体变慢）。
  async function getAssignmentSnapshot(id) {
    const c = ready(); if (!c) throw new Error("Cloud service is not configured");
    const { data, error } = await c.from("assignments")
      .select("question_snapshot")
      .eq("id", id)
      .maybeSingle();
    if (error) return [];
    return (data && Array.isArray(data.question_snapshot)) ? data.question_snapshot : [];
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
    ready, createAssignment, listAssignments, getAssignment, getAssignmentSnapshot,
    takeAssignment, submitAssignment, getSubmissionResult, readTeacherStats, resetTesterAttempt,
    clearStudentAttempt,
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
    if (!url) throw new Error("Practice sync is not configured");
    const resp = await fetch(url, {
      method: "POST",
      headers: { "content-type": "text/plain" },
      body: JSON.stringify(payload),
    });
    const data = await resp.json().catch(() => ({}));
    if (resp.status === 401 || resp.status === 403) throw new Error("Could not confirm this name and student number");
    if (!resp.ok) throw new Error(data.error || ("Practice service error (HTTP " + resp.status + ")"));
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

  async function recordPractice(input, log) {
    return callEdge({
      action: "record",
      name: input.name,
      student_no: input.studentNo,
      class_name: input.className || "",
      log: log || {},
    });
  }

  return { resolveStudent, readHistory, recordPractice };
})();
