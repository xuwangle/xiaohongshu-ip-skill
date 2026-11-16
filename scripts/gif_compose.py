#!/usr/bin/env python3
"""将独立动画帧（透明 RGBA 或纯白 RGB PNG）合成为真实可播放 GIF（用于无原生图转 GIF 工具时的逐帧合成）。"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from PIL import Image


def natural_key(path: Path) -> tuple:
    parts = re.split(r"(\d+)", path.stem)
    return tuple(int(p) if p.isdigit() else p.lower() for p in parts)


def compose_gif(
    frame_paths: list[Path],
    out_path: Path,
    duration_ms: int = 140,
    loop: int = 0,
    max_side: int = 720,
) -> dict:
    if len(frame_paths) < 2:
        raise ValueError("GIF 至少需要 2 帧图片")

    raw_frames = [Image.open(p) for p in frame_paths]
    has_alpha = any(im.mode in ("RGBA", "LA") and im.getchannel("A").getextrema()[0] < 250 for im in raw_frames)

    processed: list[Image.Image] = []
    base_w, base_h = raw_frames[0].size
    if max(base_w, base_h) > max_side:
        scale = max_side / max(base_w, base_h)
        target_size = (max(1, int(round(base_w * scale))), max(1, int(round(base_h * scale))))
    else:
        target_size = (base_w, base_h)

    for im in raw_frames:
        if im.size != target_size:
            im = im.resize(target_size, Image.Resampling.LANCZOS)

        if has_alpha:
            rgba = im.convert("RGBA")
            alpha = rgba.getchannel("A")
            # Reserve index 255 for transparent background
            rgb_q = rgba.convert("RGB").quantize(colors=255, method=Image.Quantize.MEDIANCUT)
            palette = rgb_q.getpalette() or [0] * 768
            if len(palette) < 768:
                palette = palette + [0] * (768 - len(palette))
            # Put transparent dummy color at slot 255
            palette[255 * 3 : 255 * 3 + 3] = [255, 255, 255]
            mask = alpha.point(lambda a: 255 if a < 128 else 0)
            p_img = Image.new("P", target_size)
            p_img.paste(rgb_q)
            p_img.paste(255, mask=mask)
            p_img.putpalette(palette)
            p_img.info["transparency"] = 255
            p_img.info["disposal"] = 2
            processed.append(p_img)
        else:
            rgb = Image.new("RGB", target_size, (255, 255, 255))
            if im.mode in ("RGBA", "LA"):
                rgba = im.convert("RGBA")
                rgb.paste(rgba, mask=rgba.getchannel("A"))
            else:
                rgb.paste(im.convert("RGB"))
            processed.append(rgb.convert("P", palette=Image.Palette.ADAPTIVE, colors=256))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    save_kwargs = {
        "save_all": True,
        "append_images": processed[1:],
        "duration": duration_ms,
        "loop": loop,
        "optimize": False,
    }
    if has_alpha:
        save_kwargs["transparency"] = 255
        save_kwargs["disposal"] = 2

    processed[0].save(out_path, format="GIF", **save_kwargs)
    return {
        "out": str(out_path),
        "frames": len(processed),
        "size": list(target_size),
        "transparent": has_alpha,
        "bytes": out_path.stat().st_size,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="将 PNG 帧序列合成为可播放透明或纯白 GIF")
    parser.add_argument("--frames-dir", required=True, type=Path, help="按序命名的帧目录（PNG）")
    parser.add_argument("--out", required=True, type=Path, help="输出 GIF 文件路径")
    parser.add_argument("--duration-ms", type=int, default=140, help="每帧停留毫秒数，默认 140ms")
    parser.add_argument("--loop", type=int, default=0, help="0 表示无限循环，1 表示只播一次")
    parser.add_argument("--max-side", type=int, default=720, help="最大边长，默认 720")
    args = parser.parse_args()

    frames = sorted(
        [p for p in args.frames_dir.iterdir() if p.is_file() and p.suffix.lower() in {".png", ".webp"}],
        key=natural_key,
    )
    info = compose_gif(frames, args.out, duration_ms=args.duration_ms, loop=args.loop, max_side=args.max_side)
    print(info)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
