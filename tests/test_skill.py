#!/usr/bin/env python3
"""xiaohongshu-ip-skill 核心脚本单元测试。"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools"))

import check_delivery  # noqa: E402
import extract_pdf  # noqa: E402
import gif_compose  # noqa: E402
import postprocess  # noqa: E402
import validate_repo  # noqa: E402


class SkillWorkflowTests(unittest.TestCase):
    def test_extract_pdf_helper(self) -> None:
        import pymupdf

        self.assertEqual(extract_pdf.parse_pages("1,3-4", 5), [0, 2, 3])
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "sample.pdf"
            doc = pymupdf.open()
            page = doc.new_page()
            page.insert_text((72, 72), "Seatbelt NHTSA check 45%")
            doc.save(pdf_path)
            doc.close()
            out_txt = extract_pdf.extract_pdf(pdf_path, query="NHTSA")
            self.assertIn("Seatbelt NHTSA check 45%", out_txt)
            self.assertIn("PDF 第 1 页", out_txt)

    def test_repo_validation_clean(self) -> None:
        self.assertEqual(validate_repo.validate_repo(), [])

    def test_bundled_open_font_fallback(self) -> None:
        # Force a temp dir without MiSans to verify SIL OFL SourceHanSansCN loads cleanly
        with tempfile.TemporaryDirectory() as tmp:
            old_env = os.environ.get("XHS_FONT_DIR")
            os.environ["XHS_FONT_DIR"] = tmp
            try:
                font, fpath, label = postprocess.load_font(24, "medium")
                self.assertTrue(fpath.is_file())
                self.assertIsNotNone(font)
            finally:
                if old_env is None:
                    os.environ.pop("XHS_FONT_DIR", None)
                else:
                    os.environ["XHS_FONT_DIR"] = old_env

    def test_postprocess_and_check_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tpath = Path(tmp)
            raw_dir = tpath / "raw"
            out_dir = tpath / "out"
            raw_dir.mkdir()

            for i in range(1, 5):
                im = Image.new("RGB", (896, 1200), (245, 241, 232))
                draw = ImageDraw.Draw(im)
                draw.rectangle([80, 120, 800, 1000], outline=(39, 135, 123), width=4)
                im.save(raw_dir / f"0{i}_card.jpg", format="JPEG")

            res = postprocess.process_carousel(
                raw_dir=raw_dir,
                out_dir=out_dir,
                book="《高性价比人生指南》",
                section="第1章第1-2节读书笔记",
            )
            self.assertEqual(len(res["pages"]), 4)
            self.assertTrue((out_dir / "01-封面.png").is_file())
            self.assertTrue((out_dir / "全套预览.jpg").is_file())

            for fname, text in {
                "标题.txt": "测试钩子标题\n",
                "正文.txt": "测试正文内容，数据已核对。\n",
                "置顶评论.txt": "一手出处列表\n",
                "来源.md": "# 来源\n- 示例来源\n",
                "交付简介.txt": "测试简介\n",
            }.items():
                postprocess.write_bom_crlf(out_dir / fname, text)

            chk = check_delivery.check_delivery(out_dir, min_pages=4)
            self.assertTrue(chk["passed"], msg=chk)

            # Inject banned draft marker and verify gate catches it
            postprocess.write_bom_crlf(out_dir / "正文.txt", "此处待核实，稍后再补充\n")
            chk_bad = check_delivery.check_delivery(out_dir, min_pages=4)
            self.assertFalse(chk_bad["passed"])
            self.assertTrue(any("待核实" in e for e in chk_bad["errors"]))

    def test_gif_compose_transparent_and_opaque(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tpath = Path(tmp)
            frames_alpha = []
            frames_opaque = []
            for idx in range(4):
                im_a = Image.new("RGBA", (320, 320), (0, 0, 0, 0))
                d_a = ImageDraw.Draw(im_a)
                d_a.ellipse([40 + idx * 20, 80, 180 + idx * 20, 220], fill=(119, 121, 99, 255))
                p_a = tpath / f"a_{idx}.png"
                im_a.save(p_a)
                frames_alpha.append(p_a)

                im_o = Image.new("RGB", (320, 320), (255, 255, 255))
                d_o = ImageDraw.Draw(im_o)
                d_o.rectangle([40 + idx * 20, 80, 160 + idx * 20, 200], fill=(37, 59, 56))
                p_o = tpath / f"o_{idx}.png"
                im_o.save(p_o)
                frames_opaque.append(p_o)

            gif_a = tpath / "alpha.gif"
            info_a = gif_compose.compose_gif(frames_alpha, gif_a, max_side=320)
            self.assertTrue(info_a["transparent"])
            with Image.open(gif_a) as g:
                self.assertTrue(getattr(g, "is_animated", False))
                self.assertEqual(g.n_frames, 4)

            gif_o = tpath / "opaque.gif"
            info_o = gif_compose.compose_gif(frames_opaque, gif_o, max_side=320)
            self.assertFalse(info_o["transparent"])
            with Image.open(gif_o) as g:
                self.assertEqual(g.n_frames, 4)


if __name__ == "__main__":
    unittest.main()
