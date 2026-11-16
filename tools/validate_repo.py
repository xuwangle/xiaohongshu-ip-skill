#!/usr/bin/env python3
"""仓库上架自检：检查 SKILL 规范、开源字体合规、相对链接与本机绝对路径泄露。"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "SKILL.md",
    "README.md",
    "CLAUDE.md",
    "LICENSE",
    "requirements.txt",
    "references/01_ip_design_candidates.md",
    "references/02_ip_brand_case.md",
    "references/03_ip_animated_gif.md",
    "references/04_carousel_visual_spec.md",
    "references/05_hooks_and_factcheck.md",
    "assets/fonts/README.md",
    "assets/fonts/来源与许可证.json",
    "assets/fonts/SourceHanSansCN/LICENSE.txt",
    "assets/fonts/SourceHanSansCN/SourceHanSansCN-VF.otf",
    "assets/ip_examples/ale/角色规范.md",
    "assets/ip_examples/ale/02_IP特征说明.png",
    "assets/ip_examples/ale/03_标准三视图.png",
    "assets/ip_examples/ale/06A_独立个人IP_LOGO.png",
    "assets/ip_examples/ale/07_表情设定.png",
    "scripts/extract_pdf.py",
    "scripts/postprocess.py",
    "scripts/gif_compose.py",
    "scripts/check_delivery.py",
    "examples/01-安全带与戴头盔/全套预览.jpg",
    "examples/02-报警器与燃气安全/全套预览.jpg",
]

HOST_PATH_PATTERNS = [
    re.compile(r"[A-Za-z]:\\Users\\[^\\\s\"']+"),
    re.compile(r"[A-Za-z]:/Users/[^/\s\"']+"),
    re.compile(r"/Users/[^/\s\"']+"),
]
MD_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def validate_repo() -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            errors.append(f"缺少必要文件: {rel}")

    # Verify SKILL.md YAML frontmatter
    skill_md = ROOT / "SKILL.md"
    if skill_md.is_file():
        text = skill_md.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            errors.append("SKILL.md 缺少 YAML frontmatter")
        elif "name: xiaohongshu-ip-skill" not in text[:300]:
            errors.append("SKILL.md frontmatter 中的 name 必须为 xiaohongshu-ip-skill")

    # Verify bundled fonts contain ONLY open fonts (no MiSans TTF/OTF bundled)
    fonts_dir = ROOT / "assets" / "fonts"
    for f in fonts_dir.rglob("*"):
        if f.is_file() and f.suffix.lower() in {".ttf", ".otf", ".ttc", ".woff2"}:
            if "misans" in f.name.lower():
                errors.append(f"仓库内不允许随仓分发 MiSans 字体文件: {f.relative_to(ROOT)}")

    meta_path = fonts_dir / "来源与许可证.json"
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        for entry in meta.get("fonts", []):
            fpath = fonts_dir / entry["file"]
            if not fpath.is_file():
                errors.append(f"登记字体不存在: {entry['file']}")
            else:
                sha = hashlib.sha256(fpath.read_bytes()).hexdigest()
                if sha != entry.get("sha256"):
                    errors.append(f"字体 SHA256 不匹配: {entry['file']}")

    # Scan markdown & python files for host paths and broken relative links
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".md", ".py", ".txt", ".json"}:
            continue
        if "__pycache__" in p.parts:
            continue
        try:
            content = p.read_bytes().decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            errors.append(f"文件无法 UTF-8 解码: {p.relative_to(ROOT)} ({exc})")
            continue

        rel_p = p.relative_to(ROOT)
        if rel_p != Path("tools/validate_repo.py"):
            for pat in HOST_PATH_PATTERNS:
                if pat.search(content):
                    errors.append(f"检测到本机绝对路径硬编码: {rel_p}")

        if p.suffix.lower() == ".md":
            for match in MD_LINK.finditer(content):
                href = match.group(1).strip()
                if href.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                target_path = (p.parent / href.split("#")[0]).resolve()
                if not target_path.exists():
                    errors.append(f"Markdown 链接失效: {rel_p} -> {href}")

    return errors


def main() -> int:
    errors = validate_repo()
    if errors:
        print("仓库校验失败:")
        for err in errors:
            print(" -", err)
        return 1
    print("xiaohongshu-ip-skill 仓库校验全部通过 (0 errors)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
