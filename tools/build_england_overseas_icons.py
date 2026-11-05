"""Convert the six generated heraldic sources to 256px DXT5 DDS icons.

Requires Pillow. Run from any directory. To first import the original generated
PNGs, pass --import-generated followed by their containing directory.
"""
from __future__ import annotations

import argparse
import io
import json
import shutil
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "docs/england_overseas_art"
OUTPUT = ROOT / "gfx/interface/icons/event_icons/england_overseas"
IDS = ("cape", "east_india", "australasia", "hudson_bay", "royal_navy", "new_world")
SIZE = 256


def resize_rgba(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    # Filter premultiplied colour to preserve clean transparent silhouettes.
    return image.convert("RGBa").resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def decode_dds(target: Path) -> Image.Image:
    data = target.read_bytes()
    assert data[:4] == b"DDS "
    assert data[84:88] == b"DXT5"
    with Image.open(io.BytesIO(data)) as image:
        image.load()
        return image.convert("RGBA")


def save_dds(image: Image.Image, target: Path) -> None:
    """Legacy DXT5 / BC3, straight alpha, all nine mip levels.

    Use a conventional DDS header without the DX10 extension so both the game's
    journal and lobby texture loaders can consume the same bitmap directly.
    """
    levels = []
    for level in range(9):
        side = max(1, SIZE >> level)
        mip = resize_rgba(image, (side, side))
        # Encode each BC3 level with Pillow, then assemble a full mip chain.
        encoded = io.BytesIO()
        mip.save(encoded, format="DDS", pixel_format="DXT5")
        payload = encoded.getvalue()[128:]
        expected = max(1, (side + 3) // 4) ** 2 * 16
        assert len(payload) == expected, (target, side, len(payload), expected)
        levels.append(payload)
    header = [124, 0xA1007, SIZE, SIZE, len(levels[0]), 0, 9]
    header += [0] * 11
    header += [32, 4, int.from_bytes(b"DXT5", "little"), 0, 0, 0, 0, 0]
    header += [0x401008, 0, 0, 0, 0]
    target.write_bytes(b"DDS " + struct.pack("<31I", *header)
                       + b"".join(levels))
    check = decode_dds(target)
    assert check.size == (SIZE, SIZE) and check.mode == "RGBA"
    assert check.getchannel("A").getextrema() == (0, 255)
    assert check.getpixel((0, 0))[3] == 0
    assert target.stat().st_size == 87536


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--import-generated", type=Path)
    args = parser.parse_args()
    sources = ART / "sources"
    sources.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if args.import_generated:
        mapping = json.loads((ART / "generated_sources.json").read_text(encoding="utf-8"))
        for key in IDS:
            target = sources / f"{key}.png"
            if not target.exists():
                shutil.copyfile(args.import_generated / mapping[key], target)
    # A contact sheet decoded from the finished DDS files verifies the deliverables.
    sheet = Image.new("RGB", (3 * 320, 2 * 390), "#202a36")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 18)
    small_font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 13)
    for index, key in enumerate(IDS):
        with Image.open(sources / f"{key}.png") as source:
            image = source.convert("RGBA")
            assert image.getchannel("A").getextrema()[0] == 0, f"{key}: no transparency"
            bounds = image.getchannel("A").getbbox()
            assert bounds
            image = image.crop(bounds)
            fitted = ImageOps.contain(image, (232, 232), Image.Resampling.LANCZOS)
            fitted = resize_rgba(image, fitted.size)
            icon = Image.new("RGBA", (SIZE, SIZE))
            icon.alpha_composite(fitted, ((SIZE-fitted.width)//2, (SIZE-fitted.height)//2))
        target = OUTPUT / f"aoc_england_{key}.dds"
        save_dds(icon, target)
        rgba = decode_dds(target)
        x, y = index % 3 * 320, index // 3 * 390
        sheet.paste(rgba, (x + 32, y + 8), rgba)
        label = key.replace("_", " ").title()
        draw.text((x + 160, y + 275), label, fill="#efdfb5", font=font, anchor="mt")
        tiny = resize_rgba(rgba, (64, 64))
        sheet.paste(tiny, (x + 128, y + 306), tiny)
        draw.text((x + 160, y + 375), "64px journal preview", fill="#b9c4ce", font=small_font, anchor="mt")
        print(f"{key}: 256x256 DXT5 / RGBA / 9 mips / {target.stat().st_size} bytes")
    sheet.save(ART / "icon_preview.png")


if __name__ == "__main__":
    main()
