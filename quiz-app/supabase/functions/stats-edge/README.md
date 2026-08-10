# stats-edge · 教师统计安全读取接口（Supabase Edge Function）

安全收紧（`../hardening-rls.sql`）撤销了 `students` / `answers` 对 anon 的
`select` 权限，所以**学生和老师用 anon key 都再也没法直接 REST 读到这两张表**
（这正好堵死了数据爬取）。但老师端 stats.html 因此也需要一个新的读法 ——
本函数就是那个「唯一读门」：浏览器先把口令发给这个函数，函数校验后再用
`service_role` 查表返回，`service_role` 只存在 Supabase secrets 里，浏览器拿不到。

## 一、需要你手动做的事（一次性）

前置：本机装有 `supabase` CLI 并已登录（`supabase login`），且已创建好
Supabase 项目（就是你在 config.js 里填 url/anonKey 的那个）。

```bash
# 1) 把真正的教师密钥写进 Supabase secrets（不要和前端 statsToken 相同更安全）
supabase secrets set --env-name TEACHER_TOKEN --project-ref <你的项目ref> '一套只有老师知道的随机长口令'

# 2) 部署函数（--no-verify-jwt：因为本函数自己用 x-teacher-token 鉴权，不依赖 Supabase JWT）
supabase functions deploy stats-edge --project-ref <你的项目ref> --no-verify-jwt
```

> 项目 ref 是 Supabase URL 里 `https://<ref>.supabase.co` 中间那串短 id。

部署完会返回一个 URL，形如：
`https://<ref>.functions.supabase.co/stats-edge`

## 二、把 URL 填进前端 config.js

打开 `quiz-app/config.js`：

```js
statsToken:   "改成你想要的任意前端口令",   // 只挡“顺手点开”，非安全边界
statsEdgeUrl: "https://<ref>.functions.supabase.co/stats-edge",  // 部署返回值
```

改完后重新跑 `python3 quiz-app/build.py` 再部署 GitHub Pages（deploy.sh）。

## 三、安全边界，务必理解

| 主体 | 能读到什么 |
| --- | --- |
| 学生 / 任意路人（只拿到公开 anon key） | `students`/`answers` **读不到**（REST 返回空/报错） |
| 拿到 `statsEdgeUrl` 的人，**不知道** `TEACHER_TOKEN` | 调用函数 → **401**，读不到 |
| 拿到 `statsEdgeUrl` + `TEACHER_TOKEN`（仅部署者与真老师） | 能读到某次作业的作答统计 |

- `TEACHER_TOKEN` 是**真正的安全管理钥**，只在 Supabase secrets 里，绝不下发前端。
- `config.js` 的 `statsToken` 是**明文前端口令**，任何学生都能在浏览器里看到，
  它只能挡“顺手点开统计页”的人，**不能当作安全边界**。
