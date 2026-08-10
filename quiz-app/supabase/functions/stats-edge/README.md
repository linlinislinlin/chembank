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
#    注意：secrets set 的语法是 NAME=VALUE（不是 --env-name），且先 cd 到 quiz-app/
#    确保能找到 quiz-app/supabase/config.toml 与函数目录。
cd /Users/tsinglan-school/Desktop/题库/quiz-app
supabase secrets set TEACHER_TOKEN='一套只有老师知道的随机长口令' --project-ref <你的项目ref>

# 2) 部署函数
#    文件 quiz-app/supabase/config.toml 已为该函数设置 verify_jwt = false
#    （这是让浏览器 CORS 预检 OPTIONS 不被网关 500 的关键）。
#    部署前请确保 config.toml 存在。
supabase functions deploy stats-edge --project-ref <你的项目ref>
```

> 项目 ref 是 Supabase URL 里 `https://<ref>.supabase.co` 中间那串短 id
> （例如你的 `jrobrcaiqtfwuomzycui`）。

部署完会返回一个 URL，形如：
`https://<ref>.functions.supabase.co/stats-edge`

> ⚠️ 若重新部署后浏览器仍报 `Preflight response ... Status code: 500`，
> 请到 Supabase Dashboard → Edge Functions → 该函数 → **JWT 验证(Verify JWT)必须为「关闭/Off」**。
> 若显示「开启/On」，在 Dashboard 里把它关掉（或先跑到官网 `.functions.supabase.co` 面板点一下），
> 否则带自定义头的跨域 POST 会在网关层被 500 拦截。

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
