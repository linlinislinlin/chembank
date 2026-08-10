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
