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

  // ---- 统计查询 ----
  async function getAssignmentStats(assignmentId) {
    const c = ready(); if (!c) throw new Error("Supabase 未配置");
    const { data: answers, error } = await c.from("answers")
      .select("*, students(name, student_no, class_name)")
      .eq("assignment_id", assignmentId);
    if (error) throw error;
    return answers || [];
  }

  return { ready, createAssignment, listAssignments, getAssignment, ensureStudent, recordAnswer, getAssignmentStats };
})();
