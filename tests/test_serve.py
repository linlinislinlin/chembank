"""Tile-selector local web server: page, /api/pick, /api/export, pruning.

Tests run the handler in-process (direct method dispatch on a fake socket) so no
real network binding is needed. Pure helpers (pick_payload, prune_pick,
parse_keep) are tested directly as well as through the HTTP layer.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

from chembank.serve import (
    DEFAULT_PICK,
    SelectorHandler,
    image_url,
    load_pick_file,
    parse_keep,
    pick_payload,
    prune_pick,
)

FIXTURES = Path(__file__).parent / "fixtures"
VAULT = FIXTURES / "vault"
DOCS = FIXTURES / "select"


def _q(qid: str, *, year: int, question: str, paper: int, los: list[str], texts: list[str], ms: str) -> dict:
    return {
        "id": qid,
        "exam_board": "CIE",
        "syllabus_code": "9701",
        "level": "AS",
        "year": year,
        "session": "MJ",
        "paper": paper,
        "question": question,
        "marks": 1,
        "syllabus_codes": ["5.1"],
        "learning_outcomes": los,
        "learning_outcome_texts": texts,
        "ms_answer": ms,
        "figures": [],
        "body": f"body of {qid}",
        "topic_titles": ["Enthalpy"],
    }


def _pick(*questions: dict) -> dict:
    qs = list(questions)
    return {
        "title": "Tiles Selector Test",
        "slug": "tiles-selector-test",
        "rules": {"title": "Tiles Selector Test"},
        "question_count": len(qs),
        "questions": qs,
    }


def _make_questions() -> list[dict]:
    """Four questions with mixed LOs so grouping reorders them (as assemble does)."""
    # q1: LO 5.1-3b -> sorts into group after 5.1-1 group; q2/q3: 5.1-1.
    return [
        _q("q-a", year=2020, question="1", paper=11, los=["5.1-3b"], texts=["LO3b text"], ms="A"),
        _q("q-b", year=2019, question="2", paper=11, los=["5.1-1"], texts=["LO1 text"], ms="B"),
        _q("q-c", year=2018, question="3", paper=11, los=["5.1-1"], texts=["LO1 text"], ms="C"),
        _q("q-d", year=2021, question="4", paper=12, los=["5.1-2"], texts=["LO2 text"], ms="D"),
    ]


class _Response:
    def __init__(self) -> None:
        self.buf = io.BytesIO()
        self.status = None
        self.headers: dict[str, str] = {}

    def write(self, data: bytes) -> None:
        self.buf.write(data)

    def body_bytes(self) -> bytes:
        return self.buf.getvalue()

    def body(self) -> str:
        return self.body_bytes().decode("utf-8")

    def json(self):
        return json.loads(self.body())


class _FakeHandler:
    """Minimal stand-in that records what SelectorHandler would emit."""

    def __init__(self, path: str, *, vault_root: Path = VAULT, out_dir: Path | None = None) -> None:
        self.path = path
        self.rfile = io.BytesIO(b"")
        self.wfile = _Response()
        self.vault_root = Path(vault_root)
        self.out_dir = Path(out_dir) if out_dir else Path(VAULT) / "handouts"
        self.cwd = FIXTURES.parent  # tests/

    def dispatch(self) -> None:
        # Run actual handler code without sockets by copying request lifecycle.
        h = _HandlerBridge(self)
        h.do_GET()


class _HandlerBridge(SelectorHandler):
    """Reuse SelectorHandler's handlers with a fake socket-style instance."""

    def __init__(self, fake: _FakeHandler) -> None:
        self._fake = fake
        self.path = fake.path
        self.rfile = fake.rfile
        self.wfile = fake.wfile
        self.vault_root = fake.vault_root
        self.out_dir = fake.out_dir
        self.cwd = fake.cwd

    def send_response(self, code: int, message: str | None = None) -> None:
        self._fake.wfile.status = code

    def send_header(self, key: str, value: str) -> None:
        self._fake.wfile.headers[key] = value

    def end_headers(self) -> None:
        pass


def _write_pick(tmp_path: Path, pick: dict, name: str = "pick.json") -> Path:
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(pick, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


# --------------------------------------------------------------------------- #
# parse_keep
# --------------------------------------------------------------------------- #
def test_parse_keep():
    assert parse_keep("1,3,5") == {1, 3, 5}
    assert parse_keep("1,3,5") == {1, 3, 5}
    assert parse_keep("1") == {1}
    assert parse_keep("") == set()
    assert parse_keep(None) == set()
    assert parse_keep("1,abc,0") == {1}  # junk and 0 dropped


# --------------------------------------------------------------------------- #
# GET /  → selector page
# --------------------------------------------------------------------------- #
def test_root_serves_selector_page(tmp_path: Path):
    fake = _FakeHandler("/")
    _HandlerBridge(fake).do_GET()
    resp = fake.wfile
    assert resp.status == 200
    assert resp.headers["Content-Type"].startswith("text/html")
    body = resp.body()
    assert "ChemBank 讲义题目选择器" in body
    assert "btn-export" in body
    assert "api/pick" in body and "api/export" in body


# --------------------------------------------------------------------------- #
# GET /api/pick
# --------------------------------------------------------------------------- #
def test_api_pick_returns_json_with_seq_and_image(tmp_path: Path):
    pick = _pick(*_make_questions())
    # Write at the default pick path so the no-file-arg request resolves it.
    _write_pick(tmp_path, pick, name="build/pick.json")

    fake = _FakeHandler("/api/pick", out_dir=tmp_path)
    fake.cwd = tmp_path
    bridge = _HandlerBridge(fake)
    bridge.do_GET()

    resp = fake.wfile
    assert resp.status == 200
    data = resp.json()
    assert data["title"] == "Tiles Selector Test"
    assert data["question_count"] == 4

    cards = data["questions"]
    assert len(cards) == 4
    # seq are 1-based, unique, continuous (1..4).
    assert [c["seq"] for c in cards] == [1, 2, 3, 4]
    # Grouping: primary LO present and mirrors assemble (5.1-1 group first).
    assert all(c["primary_lo"] for c in cards)
    assert cards[0]["primary_lo"] == "5.1-1"
    # Each card is lightweight: no full body dumped.
    for c in cards:
        assert "body" not in c
        assert "learning_outcome_texts" not in c
        assert isinstance(c["syllabus_codes"], list)
    # image_url is a server-relative /assets URL when a figure resolves, so
    # the browser can load it over http instead of a blocked file:// URL.

    # Give one card a resolvable figure and check the API surfaces its URL.
    asset = VAULT / "assets" / "cie-9701-2018-mj-p11-q5-paper.png"
    assert asset.is_file()
    q_fig = _q("q-fig", year=2018, question="5", paper=11, los=["5.1-1"], texts=["LO1"], ms="C")
    q_fig["figures"] = ["assets/cie-9701-2018-mj-p11-q5-paper.png"]
    data_fig = pick_payload(_pick(q_fig), VAULT)
    url = data_fig["questions"][0]["image_url"]
    assert url.startswith("/assets/")
    assert "file://" not in url
    # The /assets subpath matches the real on-disk file relative to the root.
    assert url.endswith("vault/assets/cie-9701-2018-mj-p11-q5-paper.png")


def test_image_url_resolves(tmp_path: Path):
    q_fig = _q("q-fig", year=2018, question="5", paper=11, los=["5.1-1"], texts=["LO1"], ms="C")
    q_fig["figures"] = ["assets/cie-9701-2018-mj-p11-q5-paper.png"]
    url = image_url(q_fig, VAULT)
    assert url is not None and url.startswith("/assets/")
    assert "cie-9701-2018-mj-p11-q5-paper.png" in url
    # No figure → None (no crash).
    nofig = _q("q-nofig", year=2019, question="1", paper=11, los=["5.1-1"], texts=["LO1"], ms="A")
    assert image_url(nofig, VAULT) is None


def test_api_pick_missing_file_returns_json_error(tmp_path: Path):
    fake = _FakeHandler("/api/pick?file=does-not-exist.json")
    fake.cwd = tmp_path
    _HandlerBridge(fake).do_GET()
    resp = fake.wfile
    assert resp.status == 404
    data = resp.json()
    assert data["ok"] is False
    assert "error" in data


# --------------------------------------------------------------------------- #
# GET /api/export → prunes, renumbers continuously
# --------------------------------------------------------------------------- #
def test_export_keep_1_3_writes_pruned_handout(tmp_path: Path):
    pick = _pick(*_make_questions())
    pick_path = _write_pick(tmp_path, pick)
    out_dir = tmp_path / "out"
    out_dir.mkdir(exist_ok=True)

    fake = _FakeHandler("/api/export?file=pick.json&keep=1,3", out_dir=out_dir)
    fake.cwd = tmp_path
    _HandlerBridge(fake).do_GET()

    resp = fake.wfile
    assert resp.status == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["question_count"] == 2
    out_path = Path(data["out_path"])
    assert out_path.is_file()
    assert out_path.name == "tiles-selector-test-pruned.md"

    # The pruned handout renumbers continuously: 第1题 and 第2题, no gaps.
    note = out_path.read_text(encoding="utf-8")
    assert "第1题" in note
    assert "第2题" in note
    assert "第3题" not in note
    # Every tile 第N题 has a matching answer-section entry 第N题.
    grid, answers = note.split("## 答案区", 1)
    for i in (1, 2):
        assert f"第{i}题" in grid
        assert f"**第{i}题**" in answers
    # LO grouping headers preserved.
    assert "### 5.1-1" in note


def test_export_renumbering_no_gaps_with_all_other_dropped(tmp_path: Path):
    """keep only seq 4 → new handout has a single question numbered 第1题."""
    pick = _pick(*_make_questions())
    _write_pick(tmp_path, pick)
    out_dir = tmp_path / "out"
    out_dir.mkdir(exist_ok=True)

    fake = _FakeHandler("/api/export?file=pick.json&keep=4", out_dir=out_dir)
    fake.cwd = tmp_path
    _HandlerBridge(fake).do_GET()
    data = fake.wfile.json()
    assert data["question_count"] == 1
    note = Path(data["out_path"]).read_text(encoding="utf-8")
    assert "第1题" in note
    assert "第0题" not in note and "第2题" not in note


def test_export_reuses_original_pick_fields(tmp_path: Path):
    """Pruned pick keeps slug/title/rules so the handout builds correctly."""
    pick = _pick(*_make_questions())
    _write_pick(tmp_path, pick)
    out_dir = tmp_path / "out"
    out_dir.mkdir(exist_ok=True)

    new_pick, out_path = prune_pick(pick, {1, 3}, vault_root=VAULT, out_dir=out_dir)
    assert new_pick["slug"] == "tiles-selector-test"
    assert new_pick["title"] == "Tiles Selector Test"
    assert new_pick["rules"]["title"] == "Tiles Selector Test"
    assert new_pick["question_count"] == 2
    assert out_path.name == "tiles-selector-test-pruned.md"


def test_export_missing_pick_returns_json_error(tmp_path: Path):
    fake = _FakeHandler("/api/export?file=nope.json&keep=1")
    fake.cwd = tmp_path
    _HandlerBridge(fake).do_GET()
    resp = fake.wfile
    assert resp.status == 404
    assert resp.json()["ok"] is False


def test_export_empty_keep_returns_400(tmp_path: Path):
    pick = _pick(*_make_questions())
    _write_pick(tmp_path, pick)
    fake = _FakeHandler("/api/export?file=pick.json&keep=")
    fake.cwd = tmp_path
    _HandlerBridge(fake).do_GET()
    assert fake.wfile.status == 400
    assert fake.wfile.json()["ok"] is False


# --------------------------------------------------------------------------- #
# GET /assets/<subpath> → image bytes over http
# --------------------------------------------------------------------------- #
ASSET_SUBPATH = "vault/assets/cie-9701-2018-mj-p11-q5-paper.png"


def test_assets_serves_real_image(tmp_path: Path):
    fake = _FakeHandler(f"/assets/{ASSET_SUBPATH}")
    _HandlerBridge(fake).do_GET()
    resp = fake.wfile
    assert resp.status == 200
    assert resp.headers["Content-Type"] == "image/png"
    assert resp.body_bytes() == (VAULT / "assets" / "cie-9701-2018-mj-p11-q5-paper.png").read_bytes()


def test_assets_serves_cross_vault_asset(tmp_path: Path):
    """Sibling vault asset (vault-structured) resolves, not just vault assets."""
    target = VAULT.parent / "vault-structured" / "assets" / "cie-9701-2021-mj-p21-q9a-paper.png"
    assert target.is_file()
    fake = _FakeHandler("/assets/vault-structured/assets/cie-9701-2021-mj-p21-q9a-paper.png")
    _HandlerBridge(fake).do_GET()
    assert fake.wfile.status == 200
    assert fake.wfile.headers["Content-Type"] == "image/png"
    assert fake.wfile.body_bytes() == target.read_bytes()


def test_assets_missing_returns_404_json(tmp_path: Path):
    fake = _FakeHandler("/assets/vault/assets/does-not-exist.png")
    _HandlerBridge(fake).do_GET()
    resp = fake.wfile
    assert resp.status == 404
    assert resp.json()["ok"] is False


def test_assets_path_traversal_rejected(tmp_path: Path):
    """Percent-encoded .. must NOT escape the assets root to /etc/passwd."""
    fake = _FakeHandler("/assets/..%2F..%2F..%2F..%2Fetc%2Fpasswd")
    _HandlerBridge(fake).do_GET()
    resp = fake.wfile
    assert resp.status in (403, 404)
    assert b"root:" not in resp.body_bytes()


# --------------------------------------------------------------------------- #
# 404 catch-all
# --------------------------------------------------------------------------- #
def test_unknown_route_returns_404_json(tmp_path: Path):
    fake = _FakeHandler("/nope")
    _HandlerBridge(fake).do_GET()
    assert fake.wfile.status == 404
    assert fake.wfile.json()["ok"] is False


# --------------------------------------------------------------------------- #
# load_pick_file / default resolution
# --------------------------------------------------------------------------- #
def test_load_pick_file(tmp_path: Path):
    pick = _pick(*_make_questions())
    p = _write_pick(tmp_path, pick)
    assert load_pick_file(p)["title"] == "Tiles Selector Test"
    assert load_pick_file(p)["question_count"] == 4


def test_default_pick_constant():
    assert DEFAULT_PICK == "build/pick.json"
