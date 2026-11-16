#!/usr/bin/env python3
"""交付红线检查：验证分辨率、BOM编码、SHA256清单并拦截 TODO/草稿口吻，不修改任何源文件。"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from PIL import Image

REQUIRED_TEXT_FILES = ["标题.txt", "正文.txt", "置顶评论.txt", "来源.md"]
BOM = b"\xef\xbb\xbf"
BANNED_COPY_PATTERNS = [
    (re.compile(r"\bTODO\b", re.IGNORECASE), "包含 TODO 未完成标记"),
    (re.compile(r"待核实"), "包含「待核实」半成品草稿语"),
    (re.compile(r"未取得.*原文"), "包含「未取得官方原文」等内部核对腔"),
    (re.compile(r"法律规书"), "包含常见 AI 误写「法律规书」"),
    (re.compile(r"^账号名$", re.MULTILINE), "包含未替换的占位符「账号名」"),
]


def check_delivery(out_dir: Path, min_pages: int = 4) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    if not out_dir.is_dir():
        return {"passed": False, "errors": [f"交付目录不存在: {out_dir}"], "warnings": []}

    cover = out_dir / "01-封面.png"
    if not cover.is_file():
        errors.append("缺少封面 01-封面.png")

    numbered = sorted(
        [p for p in out_dir.iterdir() if p.is_file() and p.suffix.lower() == ".png" and re.match(r"^\d{2}", p.name)],
        key=lambda p: p.name,
    )
    if len(numbered) < min_pages:
        errors.append(f"成图数量不足：当前 {len(numbered)} 张，至少需要 {min_pages} 张")

    for img_path in numbered:
        try:
            with Image.open(img_path) as im:
                if im.size != (1440, 1920):
                    errors.append(f"{img_path.name} 尺寸不是 1440×1920，而是 {im.size}")
        except Exception as exc:
            errors.append(f"{img_path.name} 无法作为图片读取: {exc}")

    if not (out_dir / "全套预览.jpg").is_file():
        errors.append("缺少 全套预览.jpg")

    for fname in REQUIRED_TEXT_FILES + ["交付清单.json"]:
        p = out_dir / fname
        if not p.is_file():
            errors.append(f"缺少交付文件: {fname}")
            continue
        raw = p.read_bytes()
        if len(raw) <= 3:
            errors.append(f"交付文件为空: {fname}")
            continue
        if not raw.startswith(BOM):
            errors.append(f"{fname} 缺少 UTF-8 BOM（Windows 记事本可能乱码）")
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            errors.append(f"{fname} UTF-8 解码失败: {exc}")
            continue

        if fname in {"标题.txt", "正文.txt", "置顶评论.txt"}:
            for pat, msg in BANNED_COPY_PATTERNS:
                if pat.search(text):
                    errors.append(f"{fname} {msg}")

    manifest_path = out_dir / "交付清单.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_bytes().decode("utf-8-sig"))
            for item in manifest.get("pages", []):
                fpath = out_dir / item["file"]
                if not fpath.is_file():
                    errors.append(f"清单引用图片不存在: {item['file']}")
                    continue
                if "sha256" in item:
                    actual = hashlib.sha256(fpath.read_bytes()).hexdigest()
                    if actual != item["sha256"]:
                        errors.append(f"{item['file']} SHA256 与 交付清单.json 不一致")
        except Exception as exc:
            errors.append(f"交付清单.json 解析失败: {exc}")

    if not (out_dir / "交付简介.txt").is_file():
        warnings.append("建议附带通俗版 交付简介.txt")

    return {
        "passed": len(errors) == 0,
        "pages_checked": len(numbered),
        "errors": errors,
        "warnings": warnings,
        "visual_note": "技术检查通过不代表图片文字零误差，请务必逐张目检汉字、数字及 IP 对称细节。",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="检查交付目录是否满足工程红线")
    parser.add_argument("--out-dir", required=True, type=Path, help="待检查成片目录")
    parser.add_argument("--min-pages", type=int, default=4, help="最少页数门槛，默认 4")
    args = parser.parse_args()

    res = check_delivery(args.out_dir, min_pages=args.min_pages)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
