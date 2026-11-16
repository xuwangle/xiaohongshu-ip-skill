#!/usr/bin/env python3
"""使用 PyMuPDF 从原书或论文 PDF 中按页提取逐字原文，供事实查证表使用。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_pages(spec: str, max_pages: int) -> list[int]:
    """将 1-based 页码字符串（如 '13-15,18'）解析为 0-based 索引列表。"""
    indices: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a_str, b_str = part.split("-", 1)
            start, end = int(a_str), int(b_str)
            if start < 1 or end < start or end > max_pages:
                raise ValueError(f"页码范围超出 1..{max_pages}: {part}")
            indices.extend(range(start - 1, end))
        else:
            p = int(part)
            if p < 1 or p > max_pages:
                raise ValueError(f"页码超出 1..{max_pages}: {part}")
            indices.append(p - 1)
    return sorted(set(indices))


def extract_pdf(pdf_path: Path, pages_spec: str | None = None, query: str | None = None) -> str:
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf  # type: ignore

    if not pdf_path.is_file():
        raise FileNotFoundError(f"找不到 PDF 文件: {pdf_path}")

    doc = pymupdf.open(str(pdf_path))
    try:
        if pages_spec:
            indices = parse_pages(pages_spec, len(doc))
        elif query:
            q_lower = query.lower()
            indices = [i for i in range(len(doc)) if q_lower in doc[i].get_text().lower()]
        else:
            indices = list(range(min(len(doc), 20)))

        chunks = [f"# 原文提取：{pdf_path.name}（总页数 {len(doc)}）\n"]
        for idx in indices:
            text = doc[idx].get_text().strip()
            chunks.append(f"\n=== PDF 第 {idx + 1} 页 ===\n{text}\n")
        return "\n".join(chunks)
    finally:
        doc.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="按页或关键词提取 PDF 一手原文")
    parser.add_argument("pdf", type=Path, help="PDF 文件路径")
    parser.add_argument("--pages", help="1-based 页码或区间，如 '13-16,20'")
    parser.add_argument("--query", help="全书按关键词检索命中页码")
    parser.add_argument("--out", type=Path, help="保存路径（按 Windows UTF-8 with BOM 写入）")
    args = parser.parse_args()

    result = extract_pdf(args.pdf, pages_spec=args.pages, query=args.query)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        crlf = result.replace("\r\n", "\n").replace("\n", "\r\n")
        args.out.write_bytes(b"\xef\xbb\xbf" + crlf.encode("utf-8"))
        print(f"已写入 {args.out}")
    else:
        sys.stdout.write(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
