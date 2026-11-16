#!/usr/bin/env python3
"""图文后处理工具：统一 1440x1920 PNG、优先本地 MiSans / 兜底开源思源黑体加脚标、生成预览图与 BOM 文稿。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SKILL_ROOT = Path(__file__).resolve().parent.parent
TARGET_W, TARGET_H = 1440, 1920
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def natural_key(path: Path) -> tuple:
    parts = re.split(r"(\d+)", path.stem)
    return tuple(int(p) if p.isdigit() else p.lower() for p in parts)


def find_font(weight: str = "medium") -> tuple[Path, str]:
    """按许可规范查找字体：本地自装 MiSans（优先） -> 随仓 SIL OFL 思源黑体 CN（兜底）。"""
    candidate_dirs: list[Path] = []
    if env_dir := os.environ.get("XHS_FONT_DIR"):
        candidate_dirs.append(Path(env_dir))
    candidate_dirs.append(SKILL_ROOT / "assets" / "fonts")

    if os.name == "nt":
        local_app = os.environ.get("LOCALAPPDATA")
        if local_app:
            candidate_dirs.append(Path(local_app) / "Microsoft" / "Windows" / "Fonts")
        candidate_dirs.append(Path(r"C:\Windows\Fonts"))
    else:
        candidate_dirs.extend([
            Path.home() / "Library" / "Fonts",
            Path("/Library/Fonts"),
            Path.home() / ".local" / "share" / "fonts",
        ])

    preferred_names = (
        ["MiSans-Medium.ttf", "MiSans-Demibold.ttf", "MiSans VF.ttf", "MiSans-Regular.ttf"]
        if weight == "medium"
        else ["MiSans-Bold.ttf", "MiSans-Heavy.ttf", "MiSans VF.ttf"]
    )
    for d in candidate_dirs:
        if not d.is_dir():
            continue
        for pname in preferred_names:
            for hit in d.rglob(pname):
                if hit.is_file():
                    return hit, "MiSans Global (local install)"

    fallback = SKILL_ROOT / "assets" / "fonts" / "SourceHanSansCN" / "SourceHanSansCN-VF.otf"
    if fallback.is_file():
        return fallback, "Source Han Sans CN VF (bundled SIL OFL 1.1)"
    raise FileNotFoundError(f"未找到可用字体：本地无 MiSans 且缺少内置兜底字体 {fallback}")


def load_font(size: int, weight: str = "medium") -> tuple[ImageFont.FreeTypeFont, Path, str]:
    font_path, font_label = find_font(weight=weight)
    font = ImageFont.truetype(str(font_path), size)
    if "VF" in font_path.name:
        target_axis = 500 if weight == "medium" else 700
        try:
            font.set_variation_by_axes([target_axis])
        except Exception:
            pass
    return font, font_path, font_label


def fit_to_3_4(img: Image.Image) -> Image.Image:
    w, h = img.size
    target_ratio = TARGET_W / TARGET_H
    cur_ratio = w / h
    if abs(cur_ratio - target_ratio) > 0.005:
        if cur_ratio > target_ratio:
            new_w = int(round(h * target_ratio))
            left = (w - new_w) // 2
            img = img.crop((left, 0, left + new_w, h))
        else:
            new_h = int(round(w / target_ratio))
            top = (h - new_h) // 2
            img = img.crop((0, top, w, top + new_h))
    if img.size != (TARGET_W, TARGET_H):
        img = img.resize((TARGET_W, TARGET_H), Image.Resampling.LANCZOS)
    return img


def write_bom_crlf(path: Path, text: str) -> None:
    crlf = text.replace("\r\n", "\n").replace("\n", "\r\n")
    path.write_bytes(b"\xef\xbb\xbf" + crlf.encode("utf-8"))


def normalize_text_files(out_dir: Path) -> list[str]:
    converted: list[str] = []
    for p in sorted(out_dir.iterdir()):
        if p.is_file() and p.suffix.lower() in {".txt", ".md"}:
            text = p.read_bytes().decode("utf-8-sig")
            write_bom_crlf(p, text)
            converted.append(p.name)
    return converted


def build_contact_sheet(page_paths: list[Path], out_path: Path, label_font: ImageFont.FreeTypeFont) -> None:
    cols = 4
    rows = max(1, (len(page_paths) + cols - 1) // cols)
    tw, th = 540, 720
    pad = 28
    label_h = 38
    sheet_w = cols * tw + (cols + 1) * pad
    sheet_h = rows * (th + label_h) + (rows + 1) * pad
    sheet = Image.new("RGB", (sheet_w, sheet_h), "#E7E1D5")
    draw = ImageDraw.Draw(sheet)

    for idx, p in enumerate(page_paths):
        r, c = divmod(idx, cols)
        x = pad + c * (tw + pad)
        y = pad + r * (th + label_h + pad)
        thumb = Image.open(p).convert("RGB").resize((tw, th), Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x, y))
        draw.rectangle([x, y, x + tw - 1, y + th - 1], outline="#C7BFB0", width=2)
        draw.text((x + 6, y + th + 6), f"{idx + 1:02d}  {p.stem}", fill="#253B38", font=label_font)

    sheet.save(out_path, format="JPEG", quality=92)


def process_carousel(
    raw_dir: Path,
    out_dir: Path,
    book: str = "",
    section: str = "",
    chapter: str = "",
    ip_character: str = "",
    generator: str = "nanobanana / Seedream + xiaohongshu-ip-skill postprocess",
    copy_from: Path | None = None,
) -> dict:
    raw_images = sorted(
        [p for p in raw_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS],
        key=natural_key,
    )
    if not raw_images:
        raise FileNotFoundError(f"生图目录内没有可用图片: {raw_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    if copy_from and copy_from.is_dir():
        for fname in ["标题.txt", "正文.txt", "置顶评论.txt", "来源.md", "交付简介.txt"]:
            src = copy_from / fname
            if src.is_file():
                shutil.copy2(src, out_dir / fname)

    footer_font, font_path, font_label = find_loaded = load_font(24, "medium")
    label_font, _, _ = load_font(22, "medium")

    rendered: list[Path] = []
    manifest_pages: list[dict] = []

    for idx, src in enumerate(raw_images, start=1):
        out_name = "01-封面.png" if idx == 1 else f"{idx:02d}.png"
        img = Image.open(src).convert("RGB")
        orig_size = list(img.size)
        img = fit_to_3_4(img)

        if book or section:
            draw = ImageDraw.Draw(img)
            y_f = TARGET_H - 54
            if book:
                draw.text((64, y_f), book, fill="#65706A", font=footer_font)
            if section:
                rb = draw.textbbox((0, 0), section, font=footer_font)
                rw = rb[2] - rb[0]
                draw.text((TARGET_W - 64 - rw, y_f), section, fill="#65706A", font=footer_font)

        dst = out_dir / out_name
        img.save(dst, format="PNG", optimize=True)
        sha256 = hashlib.sha256(dst.read_bytes()).hexdigest()
        rendered.append(dst)
        manifest_pages.append(
            {
                "file": out_name,
                "source_image": src.name,
                "orig_size": orig_size,
                "final_size": [TARGET_W, TARGET_H],
                "sha256": sha256,
            }
        )

    preview_path = out_dir / "全套预览.jpg"
    build_contact_sheet(rendered, preview_path, label_font)

    normalized_texts = normalize_text_files(out_dir)

    manifest = {
        "chapter": chapter or book,
        "section": section,
        "ip_character": ip_character,
        "generator": generator,
        "font_used": font_label,
        "font_file": font_path.name,
        "pages": manifest_pages,
        "normalized_text_files": normalized_texts,
    }
    write_bom_crlf(out_dir / "交付清单.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="统一 1440x1920 PNG、加双角标、导出预览与 BOM 清单")
    parser.add_argument("--raw-dir", required=True, type=Path, help="AI 生图原图目录")
    parser.add_argument("--out-dir", required=True, type=Path, help="成片输出目录")
    parser.add_argument("--book", default="", help="左下角书名/系列名，例如 《高性价比人生指南》")
    parser.add_argument("--section", default="", help="右下角章节说明，例如 第1章第3-4节读书笔记")
    parser.add_argument("--chapter", default="", help="清单记录章节名")
    parser.add_argument("--ip-character", default="", help="IP 角色名称")
    parser.add_argument("--copy-from", type=Path, help="可选：从此工程目录同步文稿 .txt/.md 文件")
    args = parser.parse_args()

    result = process_carousel(
        raw_dir=args.raw_dir,
        out_dir=args.out_dir,
        book=args.book,
        section=args.section,
        chapter=args.chapter,
        ip_character=args.ip_character,
        copy_from=args.copy_from,
    )
    print(json.dumps({"pages": len(result["pages"]), "font_used": result["font_used"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
