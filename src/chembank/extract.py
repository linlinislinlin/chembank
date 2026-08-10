"""Extract plain text from past-paper PDFs (with chemistry symbol recovery)."""

from __future__ import annotations

from pathlib import Path

from chembank.symbols import extract_page_with_symbols, normalize_chars


def extract_pdf_text(
    pdf_path: Path,
    *,
    page_markers: bool = True,
    recover_symbols: bool = True,
) -> str:
    """Extract text from a PDF using PyMuPDF.

    When ``recover_symbols`` is True (default), vector-drawn CIE symbols such as
    ΔH⦵ are decoded from drawings and merged back into the text layer.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise SystemExit(
            "PyMuPDF is required. Install with: pip install -r requirements.txt"
        ) from exc

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    doc = fitz.open(pdf_path)
    chunks: list[str] = []
    try:
        for i, page in enumerate(doc, start=1):
            if recover_symbols:
                text = extract_page_with_symbols(page)
            else:
                text = page.get_text("text") or ""
            text = normalize_chars(text.replace("\r\n", "\n").replace("\r", "\n")).strip()
            if page_markers:
                chunks.append(f"----- PAGE {i} -----\n{text}")
            else:
                chunks.append(text)
    finally:
        doc.close()

    return "\n\n".join(chunks).strip() + "\n"


def write_extracted_text(
    pdf_path: Path,
    out_path: Path,
    *,
    page_markers: bool = True,
    recover_symbols: bool = True,
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    text = extract_pdf_text(
        pdf_path, page_markers=page_markers, recover_symbols=recover_symbols
    )
    out_path.write_text(text, encoding="utf-8")
    return out_path
