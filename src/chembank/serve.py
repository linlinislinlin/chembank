"""Local-web interactive "tile selector" for ChemBank handouts.

Lets a user open a local browser page, see every question of a pick as a small
thumbnail card with a keep-checkbox, uncheck the questions they do not want, and
export a *pruned* handout. The export builds a new pick dict containing only the
kept questions and re-runs the existing assembler (``chembank.assemble``) so LO
grouping, answer-section pairing and continuous numbering (第1题..第N题) are all
preserved — nothing is reimplemented here.

Deliberately stdlib-only (http.server, urllib.parse, json, pathlib, threading)
so it stays as dependency-light as the rest of the package. Binds 127.0.0.1 by
default and is intended for local offline use.

Numbering consistency
---------------------
The API reports each question with a ``seq`` number that matches assemble's
handout-internal sequential numbers (1,2,3… across all LO groups). To keep that
guarantee, the server reuses assemble's own grouping primitives (``_group_questions``
etc.) rather than duplicating the ordering. The export path only *filters* the
question list before handing it back to ``render_tiles``, which does all
grouping/renumbering, so the pruned handout is always internally consistent.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from chembank.assemble import (
    _group_questions,
    _lo_text,
    _paper_figure,
    _primary_lo,
    render_tiles,
    resolve_asset_path,
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8975
DEFAULT_PICK = "build/pick.json"
DEFAULT_VAULT = "vault"
HANDOUTS_DIR = "vault/handouts"

# Suffix appended to a pruned handout so the original is never overwritten.
PRUNED_SUFFIX = "-pruned.md"


# --------------------------------------------------------------------------- #
# Reusable logic (testable without sockets)
# --------------------------------------------------------------------------- #
def _session_label(question: dict[str, Any]) -> str | None:
    session = question.get("session")
    if session is None:
        return None
    text = str(session).strip()
    return text.upper() if text else None


def _caption(seq: int, question: dict[str, Any]) -> str:
    """Human caption ``#seq · 2021 MJ · Q7 · 1 分 · LO 5.1-2``."""
    bits = [f"#{seq}"]
    year = question.get("year")
    session = _session_label(question)
    if year is not None and session:
        bits.append(f"{year} {session}")
    elif year is not None:
        bits.append(str(year))
    original = question.get("question")
    if original is not None and str(original).strip():
        bits.append(f"Q{original}")
    marks = question.get("marks")
    if isinstance(marks, int):
        bits.append(f"{marks} 分")
    primary = _primary_lo(question)
    if primary:
        bits.append(f"LO {primary}")
    return " · ".join(bits)


# Image content types served by the /assets route, keyed by lowercase suffix.
_ASSET_CONTENT_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def assets_root(vault_root: Path) -> Path:
    """The directory to which /assets paths are resolved (default) and relative.

    ``resolve_asset_path`` finds figures inside the target vault root *and* its
    known sibling vaults (``vault``, ``vault-structured``, ``vault-practical``),
    all of which live under the same parent. That parent is the natural assets
    root: emitting a subpath relative to it (e.g. ``vault/assets/x.png`` or
    ``vault-structured/assets/y.png``) lets the browser reach every vault during
    page rendering, while still staying safely inside one filesystem subtree.
    """
    return vault_root.parent


def image_subpath(question: dict[str, Any], vault_root: Path) -> str | None:
    """Return the ``/assets``-style subpath (no leading slash) for a thumbnail.

    Uses assemble's own figure resolution so it matches the handout's asset,
    then makes the path relative to :func:`assets_root` so the emitted subpath
    is exactly what the /assets route can re-resolve. Returns None when there is
    no resolvable figure.
    """
    paper_fig = _paper_figure(question)
    if not paper_fig:
        return None
    asset_path = resolve_asset_path(paper_fig, vault_root=vault_root)
    if asset_path is None:
        return None
    return _relative_subpath(asset_path, assets_root(vault_root))


def _relative_subpath(asset_path: Path, root: Path) -> str | None:
    """Posix subpath of ``asset_path`` relative to ``root``, or None if outside."""
    try:
        return asset_path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


def _resolve_asset_subpath(subpath: str, vault_root: Path) -> Path | None:
    """Resolve a ``/assets`` subpath to a real file strictly inside the roots.

    The subpath is normalized against :func:`assets_root`; any ``..`` that would
    escape the root is rejected (None) so traversal attempts never read outside
    the vault tree. Returns the resolved on-disk path when it exists and is a
    regular file within the allowed root, else None.
    """
    root = assets_root(vault_root).resolve()
    subpath = subpath.replace("\\", "/").lstrip("/")
    candidate = (root / subpath).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if candidate.is_file() and candidate.suffix.lower() in _ASSET_CONTENT_TYPES:
        return candidate
    return None


def image_url(question: dict[str, Any], vault_root: Path) -> str | None:
    """Relative ``/assets/<subpath>`` URL for the paper thumbnail, or None.

    The page is loaded over ``http://127.0.0.1`` where absolute ``file://``
    URLs are blocked by the browser, so we emit a server-relative URL that the
    /assets route serves as bytes. Returns None when there is no figure.
    """
    subpath = image_subpath(question, vault_root)
    if subpath is None:
        return None
    return "/assets/" + subpath


def _ordered_questions(pick: dict[str, Any]) -> list[dict[str, Any]]:
    """Questions in the exact order assemble will render them (grouped by LO)."""
    questions = list(pick.get("questions") or [])
    groups = _group_questions(questions)
    return [q for _lo, _text, group in groups for q in group]


def pick_payload(pick: dict[str, Any], vault_root: Path) -> dict[str, Any]:
    """Build the ``/api/pick`` response body (lightweight tile cards)."""
    questions = list(pick.get("questions") or [])
    ordered = _ordered_questions(pick)
    primary = {id(q): (_primary_lo(q), _lo_text(q, _primary_lo(q))) for q in questions}

    cards: list[dict[str, Any]] = []
    for seq, q in enumerate(ordered, start=1):
        lo, lo_text = primary.get(id(q), ("", ""))
        cards.append(
            {
                "seq": seq,
                "primary_lo": lo,
                "lo_text": lo_text,
                "id": q.get("id"),
                "year": q.get("year"),
                "session": q.get("session"),
                "paper": q.get("paper"),
                "question": q.get("question"),
                "marks": q.get("marks"),
                "ms_answer": q.get("ms_answer"),
                "syllabus_codes": q.get("syllabus_codes") or [],
                "figures": q.get("figures") or [],
                "image_url": image_url(q, vault_root),
                "caption": _caption(seq, q),
            }
        )

    return {
        "title": str(pick.get("title") or (pick.get("rules") or {}).get("title") or "Handout"),
        "slug": str(pick.get("slug") or ""),
        "question_count": len(questions),
        "questions": cards,
    }


def prune_pick(
    pick: dict[str, Any],
    keep_seq: set[int],
    vault_root: Path,
    out_dir: str | Path,
) -> tuple[dict[str, Any], Path]:
    """Build a pruned pick dict and write the pruned handout via ``render_tiles``.

    ``keep_seq`` are the 1-based handout seq numbers the user kept (as shown in
    the page). The output pick copies ``rules``/``title``/``slug`` from the
    original and retains only the kept originals in their original order; the
    assembler then re-groups and renumbers from 1, so the exported handout has
    continuous 第1题..第N题 with no gaps. Returns ``(new_pick, out_path)``.
    """
    questions = list(pick.get("questions") or [])
    ordered = _ordered_questions(pick)
    keep_by_id = set()
    for seq in keep_seq:
        if 1 <= seq <= len(ordered):
            keep_by_id.add(id(ordered[seq - 1]))

    kept = [q for q in questions if id(q) in keep_by_id]
    new_pick = {
        "schema_version": pick.get("schema_version"),
        "generated_at": pick.get("generated_at"),
        "source_corpus_dir": pick.get("source_corpus_dir"),
        "corpus_question_count": pick.get("corpus_question_count"),
        "rules": dict(pick.get("rules") or {}),
        "slug": str(pick.get("slug") or "handout"),
        "title": pick.get("title"),
        "question_count": len(kept),
        "questions": kept,
    }

    suffix = str(out_dir / f"{new_pick['slug']}{PRUNED_SUFFIX}")
    render_tiles(new_pick, vault_root=vault_root, out_path=suffix)
    return new_pick, Path(suffix)


def parse_keep(csv: str | None) -> set[int]:
    """Parse the ``keep=1,3,5`` query value into a set of 1-based seq numbers."""
    if not csv:
        return set()
    nums: set[int] = set()
    for token in str(csv).split(","):
        token = token.strip()
        if not token:
            continue
        try:
            v = int(token)
        except ValueError:
            continue
        if v >= 1:
            nums.add(v)
    return nums


def locate_pick(file_arg: str | None, *, cwd: Path) -> Path:
    """Resolve a pick JSON path (explicit arg or default) against CWD."""
    if not file_arg:
        return cwd / DEFAULT_PICK
    p = Path(file_arg)
    if not p.is_absolute():
        p = cwd / p
    return p


def locate_vault(vault_arg: str | None, *, cwd: Path) -> Path:
    if not vault_arg:
        return cwd / DEFAULT_VAULT
    p = Path(vault_arg)
    if not p.is_absolute():
        p = cwd / p
    return p


def locate_out_dir(vault_root: Path) -> Path:
    """Directory where pruned handouts are written (``<vault>/handouts``)."""
    return vault_root / "handouts"


def load_pick_file(pick_path: Path) -> dict[str, Any]:
    """Load + validate a pick JSON, raising ValueError on missing/malformed."""
    if not pick_path.is_file():
        raise ValueError(f"Pick file not found: {pick_path}")
    try:
        data = json.loads(pick_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
        raise ValueError(f"Invalid pick JSON {pick_path}: {e}") from e
    if not isinstance(data, dict):
        raise ValueError(f"Pick file {pick_path} must contain a JSON object")
    return data


# --------------------------------------------------------------------------- #
# HTTP handler
# --------------------------------------------------------------------------- #
class SelectorHandler(BaseHTTPRequestHandler):
    """Handle GET / (page), /api/pick, /api/export; anything else → 404 JSON."""

    server_version = "ChemBankSelector/1.0"

    # Injected at construction (class attrs are overridden by the server's
    # handler_class initialization so runtime config flows through cleanly).
    vault_root = Path(DEFAULT_VAULT)
    out_dir = Path(HANDOUTS_DIR)
    cwd = Path.cwd()

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _query(self) -> dict[str, list[str]]:
        return parse_qs(urlparse(self.path).query)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path == "/":
            self._serve_index()
        elif path == "/api/pick":
            self._handle_pick()
        elif path == "/api/export":
            self._handle_export()
        elif path.startswith("/assets/"):
            self._handle_asset(path[len("/assets/"):])
        else:
            self._send_json(404, {"ok": False, "error": "not found"})

    def _handle_asset(self, subpath: str) -> None:
        """Serve an image from the vault/source tree over http.

        ``subpath`` is the URL-decoded portion following ``/assets/``. It is
        normalized against :func:`assets_root` so sibling-vault assets (e.g.
        ``vault-structured/assets/...``) resolve too, and any traversal that
        escapes the root is rejected before touching the filesystem.
        """
        asset_path = _resolve_asset_subpath(subpath, self.vault_root)
        if asset_path is None:
            self._send_json(404, {"ok": False, "error": "asset not found"})
            return
        try:
            body = asset_path.read_bytes()
        except OSError:
            self._send_json(404, {"ok": False, "error": "asset not found"})
            return
        self._send(200, body, _ASSET_CONTENT_TYPES.get(asset_path.suffix.lower(), "application/octet-stream"))

    def _serve_index(self) -> None:
        html = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ChemBank 讲义题目选择器</title>
{_PAGE_CSS}
</head><body>
<div id="topbar">
  <h1 id="title">加载中…</h1>
  <div id="status"></div>
  <div id="controls">
    <span id="count">保留 0 / 共 0 题</span>
    <button id="btn-all">全选</button>
    <button id="btn-none">取消全选</button>
    <button id="btn-export">导出</button>
  </div>
</div>
<div id="grid"></div>
{_PAGE_JS}
</body></html>"""
        self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")

    def _handle_pick(self) -> None:
        try:
            pick_path = locate_pick(self._query_arg("file"), cwd=self.cwd)
            pick = load_pick_file(pick_path)
        except ValueError as e:
            self._send_json(404, {"ok": False, "error": str(e)})
            return
        payload = pick_payload(pick, self.vault_root)
        self._send_json(200, payload)

    def _handle_export(self) -> None:
        try:
            pick_path = locate_pick(self._query_arg("file"), cwd=self.cwd)
            pick = load_pick_file(pick_path)
            keep = parse_keep(self._query_arg("keep"))
        except ValueError as e:
            self._send_json(404, {"ok": False, "error": str(e)})
            return
        if not keep:
            self._send_json(400, {"ok": False, "error": "keep must be a non-empty comma list"})
            return
        try:
            new_pick, out_path = prune_pick(
                pick, keep, vault_root=self.vault_root, out_dir=self.out_dir
            )
        except OSError as e:
            self._send_json(500, {"ok": False, "error": f"export failed: {e}"})
            return
        self._send_json(
            200,
            {
                "ok": True,
                "out_path": str(out_path),
                "question_count": new_pick["question_count"],
                "slug": new_pick["slug"],
            },
        )

    def _query_arg(self, key: str) -> str | None:
        vals = self._query().get(key)
        return vals[0] if vals else None


# --------------------------------------------------------------------------- #
# Server bootstrap
# --------------------------------------------------------------------------- #
def build_server(
    *,
    pick: str | None = None,
    port: int = DEFAULT_PORT,
    vault: str | None = None,
    host: str = DEFAULT_HOST,
) -> ThreadingHTTPServer:
    """Create (but do not start) the HTTP server, wiring runtime config in."""
    cwd = Path.cwd()
    vault_root = locate_vault(vault, cwd=cwd)
    out_dir = locate_out_dir(vault_root)
    pick_default = pick

    class Handler(SelectorHandler):  # per-server subclass to carry config
        pass

    # Class-body scope can't see enclosing locals that share their names, so
    # set the runtime config explicitly (setattr sidesteps the shadowing).
    setattr(Handler, "cwd", cwd)
    setattr(Handler, "vault_root", vault_root)
    setattr(Handler, "out_dir", out_dir)
    setattr(Handler, "pick_default", pick_default)

    server = ThreadingHTTPServer((host, port), Handler)
    server._chembank_out_dir = out_dir  # type: ignore[attr-defined]
    return server


def serve(pick: str | None, *, port: int, vault: str | None, host: str) -> None:
    """Run the server until interrupted (blocking). Meant for the CLI."""
    server = build_server(pick=pick, port=port, vault=vault, host=host)
    bind_host, bind_port = server.server_address[:2]
    print(f"打开 http://{bind_host}:{bind_port}/", flush=True)
    print("按 Ctrl+C 停止。", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        server.server_close()


# --------------------------------------------------------------------------- #
# Embedded page assets (inline CSS/JS — no external CDN, offline local)
# --------------------------------------------------------------------------- #
_PAGE_CSS = """
<style>
:root{--bg:#f6f7fb;--card:#fff;--line:#e4e7ee;--accent:#2f6bff;--danger:#d93026;}
*{box-sizing:border-box;}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:#1c1f26;}
#topbar{position:sticky;top:0;z-index:10;background:#fff;border-bottom:1px solid var(--line);
  padding:10px 18px;display:flex;align-items:center;flex-wrap:wrap;gap:12px;
  box-shadow:0 1px 4px rgba(0,0,0,.05);}
#topbar h1{font-size:18px;margin:0;font-weight:600;}
#status{font-size:13px;color:#4a5160;flex:1 1 200px;}
#controls{display:flex;align-items:center;gap:8px;}
#count{font-weight:600;color:#14181f;}
button{cursor:pointer;border:1px solid var(--line);background:#fff;border-radius:8px;
  padding:7px 14px;font-size:13px;}
button:hover{border-color:var(--accent);color:var(--accent);}
#btn-export{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600;}
#btn-export:hover{filter:brightness(1.08);color:#fff;}
#grid{padding:18px;display:grid;grid-template-columns:1fr;gap:18px;}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;
  display:flex;flex-direction:column;box-shadow:0 1px 2px rgba(0,0,0,.04);width:100%;}
.card.unchosen{opacity:.45;}
.card img{max-width:100%;height:auto;display:block;background:#0d0f14;}
.card .thumb{width:100%;display:flex;justify-content:center;align-items:flex-start;padding:8px;}
.card .thumb img{width:100%;height:auto;border-radius:6px;}
.card .meta{padding:10px 14px;display:flex;flex-direction:column;gap:6px;}
.card .caption{font-size:13px;line-height:1.4;color:#1c1f26;}
.card .lo{font-size:11px;color:#5a6272;background:#f2f4f9;border-radius:6px;padding:3px 7px;}
.card .keep{display:flex;align-items:center;gap:8px;font-size:13px;color:#2c313b;}
.card input[type=checkbox]{width:16px;height:16px;accent-color:var(--accent);}
.card .newseq{font-weight:700;color:var(--accent);}
#msg{padding:0 18px;font-size:13px;color:#155724;}
#msg.error{color:#721c24;}
.badge{display:inline-block;background:var(--accent);color:#fff;border-radius:999px;font-size:11px;
  padding:2px 8px;margin-left:6px;}
</style>
"""

_PAGE_JS = """
<script>
const PARAMS = new URLSearchParams(location.search);
const FILE = PARAMS.get("file") || "build/pick.json";
let payload = null;
const KEPT = new Set();   // seq numbers of kept questions
const ORDER = {};         // seq -> question

const $ = (id) => document.getElementById(id);

function countKept(){ return KEPT.size; }
function renderCount(){
  const total = payload ? payload.question_count : 0;
  $("count").textContent = `保留 ${countKept()} / 共 ${total} 题`;
  $("title").textContent = payload ? payload.title : "加载中…";
}

function computeNewNumber(seq){
  // Recompute the handout-sequential number this card will get after pruning.
  const keptSeqs = [...payload.questions.map(q=>q.seq)].filter(s => KEPT.has(s));
  keptSeqs.sort((a,b)=>a-b);
  return keptSeqs.indexOf(seq) + 1;
}

function render(){
  if(!payload){ return; }
  const grid = $("grid");
  grid.innerHTML = "";
  for(const q of payload.questions){
    const card = document.createElement("div");
    card.className = "card";
    const img = q.image_url
      ? `<img src="${q.image_url}" loading="lazy" alt="${(q.id||'img').replace(/"/g,'')}"/>`
      : `<div class="thumb" style="padding:16px;color:#7a8090;font-size:12px;">（无图）${(q.caption||'')}</div>`;
    const newNum = computeNewNumber(q.seq);
    card.innerHTML = `
      <div class="thumb">${img}</div>
      <div class="meta">
        <div class="caption">${q.caption||"第"+q.seq+"题"}</div>
        ${q.lo_text ? `<div class="lo">LO ${q.primary_lo} — ${escapeHtml(q.lo_text)}</div>` : ""}
        <div class="keep">
          <input type="checkbox" data-seq="${q.seq}" ${KEPT.has(q.seq)?"checked":""}/>
          <span>保留，将为第 <span class="newseq" data-newseq="${q.seq}">${newNum||"?"}</span> 题</span>
        </div>
      </div>`;
    card.querySelector("input").addEventListener("change", (e)=>{
      if(e.target.checked){ KEPT.add(q.seq); } else { KEPT.delete(q.seq); }
      card.classList.toggle("unchosen", !e.target.checked);
      renderCount();
      updateNewNumbers();
    });
    if(!KEPT.has(q.seq)){ card.classList.add("unchosen"); }
    grid.appendChild(card);
  }
}

function updateNewNumbers(){
  for(const q of payload.questions){
    const newNum = computeNewNumber(q.seq);
    const el = document.querySelector(`.newseq[data-newseq="${q.seq}"]`);
    if(el){ el.textContent = newNum || "?"; }
  }
}

function escapeHtml(s){
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;");
}

async function loadPick(){
  const r = await fetch(`/api/pick?file=${encodeURIComponent(FILE)}`);
  const data = await r.json();
  if(data.ok === false){ showMsg(data.error||"加载失败","error"); return; }
  payload = data;
  payload.questions.forEach(q=>{ KEPT.add(q.seq); ORDER[q.seq]=q; });
  renderCount();
  render();
}

function showMsg(text, cls){
  let m = $("msg");
  if(!m){ m = document.createElement("div"); m.id="msg"; document.body.appendChild(m); }
  m.textContent = text; m.className = cls||"";
}

$("btn-all").addEventListener("click", ()=>{
  if(!payload){return;}
  payload.questions.forEach(q=>KEPT.add(q.seq));
  render();
  renderCount();
});
$("btn-none").addEventListener("click", ()=>{
  if(!payload){return;}
  payload.questions.forEach(q=>KEPT.delete(q.seq));
  render();
  renderCount();
});
$("btn-export").addEventListener("click", async ()=>{
  if(!payload){ return; }
  if(KEPT.size === 0){ showMsg("至少保留 1 题才能导出。","error"); return; }
  const keep = [...KEPT].sort((a,b)=>a-b).join(",");
  showMsg("导出中…");
  try{
    const r = await fetch(`/api/export?file=${encodeURIComponent(FILE)}&keep=${keep}`);
    const data = await r.json();
    if(data.ok){
      showMsg(`已生成新讲义（${data.question_count} 题）：${data.out_path}`
        + `　请在桌面打开 Obsidian 题库，刷新后即可在 vault/handouts 中看到。`);
    } else {
      showMsg(data.error||"导出失败","error");
    }
  }catch(e){
    showMsg("导出失败：" + e, "error");
  }
});

loadPick();
</script>
"""


__all__ = [
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "PRUNED_SUFFIX",
    "SelectorHandler",
    "build_server",
    "serve",
    "load_pick_file",
    "locate_out_dir",
    "locate_pick",
    "locate_vault",
    "parse_keep",
    "pick_payload",
    "prune_pick",
    "image_url",
    "image_subpath",
    "assets_root",
]
