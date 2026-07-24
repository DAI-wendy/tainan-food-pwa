#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_icons.py — 產生 PWA 所需的全套 icon

用法：
    pip install pillow
    python3 gen_icons.py                 # 用預設設定產生 icons/
    python3 gen_icons.py --text 食        # 換中間的字
    python3 gen_icons.py --bg1 "#f97316" --bg2 "#facc15"   # 換漸層底色
    python3 gen_icons.py --out icons      # 換輸出資料夾

產生內容：
    icons/icon-72.png ... icon-512.png    一般 icon（圓角方形）
    icons/maskable-192.png / -512.png     Android 自適應圖示（安全區留白）
    icons/apple-touch-icon.png            iOS 加到主畫面用（180x180，不透明）
    icons/favicon.ico                     瀏覽器分頁小圖示
    icons/icon.svg                        向量版（可無限放大）
"""

import argparse
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("需要 Pillow，請先執行：pip install pillow")

# ---------------------------------------------------------------- 設定
SIZES = [72, 96, 128, 144, 152, 167, 180, 192, 256, 384, 512]

# 依作業系統自動尋找可用的中文字型
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/System/Library/Fonts/PingFang.ttc",              # macOS
    "/System/Library/Fonts/STHeiti Medium.ttc",        # macOS
    "C:/Windows/Fonts/msjhbd.ttc",                     # Windows 微軟正黑體 Bold
    "C:/Windows/Fonts/msjh.ttc",
]


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def find_font():
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def load_font(path, size):
    """字型檔可能是 ttc（多字型集合），逐一嘗試 index。"""
    for idx in range(0, 6):
        try:
            return ImageFont.truetype(path, size, index=idx)
        except Exception:
            continue
    return None


# ---------------------------------------------------------------- 繪圖
def gradient(size, c1, c2):
    """左上到右下的對角漸層。"""
    img = Image.new("RGB", (size, size), c1)
    px = img.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * (size - 1))
            px[x, y] = (
                int(c1[0] + (c2[0] - c1[0]) * t),
                int(c1[1] + (c2[1] - c1[1]) * t),
                int(c1[2] + (c2[2] - c1[2]) * t),
            )
    return img


def rounded_mask(size, radius_ratio):
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1],
                        radius=int(size * radius_ratio), fill=255)
    return mask


def draw_cutlery(draw, box, color):
    """沒有中文字型時的備用圖案：刀叉。"""
    x0, y0, x1, y1 = box
    w = x1 - x0
    h = y1 - y0
    bar = max(2, int(w * 0.055))

    # 叉子（左）
    fx = x0 + w * 0.30
    for i in (-1, 0, 1):
        px = fx + i * w * 0.10
        draw.rounded_rectangle([px - bar / 2, y0, px + bar / 2, y0 + h * 0.34],
                               radius=bar / 2, fill=color)
    draw.rounded_rectangle([fx - w * 0.145, y0 + h * 0.28,
                            fx + w * 0.145, y0 + h * 0.40],
                           radius=w * 0.06, fill=color)
    draw.rounded_rectangle([fx - bar, y0 + h * 0.36, fx + bar, y1],
                           radius=bar, fill=color)

    # 湯匙（右）
    sx = x0 + w * 0.72
    draw.ellipse([sx - w * 0.13, y0, sx + w * 0.13, y0 + h * 0.36], fill=color)
    draw.rounded_rectangle([sx - bar, y0 + h * 0.30, sx + bar, y1],
                           radius=bar, fill=color)


def make_icon(size, text, c1, c2, fg, radius_ratio=0.22, scale=0.62,
              opaque=False):
    """產生單張 icon。scale = 圖形佔畫布的比例（maskable 要調小）。"""
    ss = 4  # 4 倍超取樣，邊緣才平滑
    big = size * ss

    base = gradient(big, c1, c2).convert("RGBA")
    if opaque:
        card = base
    else:
        card = Image.new("RGBA", (big, big), (0, 0, 0, 0))
        card.paste(base, (0, 0), rounded_mask(big, radius_ratio))

    layer = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    side = big * scale
    box = ((big - side) / 2, (big - side) / 2,
           (big + side) / 2, (big + side) / 2)

    font_path = find_font()
    font = load_font(font_path, int(side)) if (font_path and text) else None

    if font:
        l, t, r, b = d.textbbox((0, 0), text, font=font)
        d.text(((big - (r - l)) / 2 - l, (big - (b - t)) / 2 - t),
               text, font=font, fill=fg)
    else:
        draw_cutlery(d, box, fg)

    card = Image.alpha_composite(card, layer)
    return card.resize((size, size), Image.LANCZOS)


def write_svg(path, text, c1_hex, c2_hex, fg_hex):
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{c1_hex}"/>
      <stop offset="1" stop-color="{c2_hex}"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="113" ry="113" fill="url(#g)"/>
  <text x="256" y="256" fill="{fg_hex}" font-size="317"
        font-family="'Noto Sans TC','PingFang TC','Microsoft JhengHei',sans-serif"
        font-weight="900" text-anchor="middle" dominant-baseline="central">{text}</text>
</svg>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser(description="產生 PWA icons")
    ap.add_argument("--out", default="icons", help="輸出資料夾（預設 icons）")
    ap.add_argument("--text", default="食", help="圖示中央的字（預設 食）")
    ap.add_argument("--bg1", default="#f97316", help="漸層起始色")
    ap.add_argument("--bg2", default="#facc15", help="漸層結束色")
    ap.add_argument("--fg", default="#ffffff", help="文字／圖形顏色")
    args = ap.parse_args()

    c1, c2, fg = hex2rgb(args.bg1), hex2rgb(args.bg2), hex2rgb(args.fg) + (255,)
    os.makedirs(args.out, exist_ok=True)

    fp = find_font()
    print("字型：" + (fp if fp else "找不到中文字型 → 改用刀叉圖案"))

    for s in SIZES:
        p = os.path.join(args.out, f"icon-{s}.png")
        make_icon(s, args.text, c1, c2, fg).save(p)
        print("  ✓", p)

    # Android maskable：整片滿版底色（系統會自己切形狀），圖形只佔中央安全區
    for s in (192, 512):
        p = os.path.join(args.out, f"maskable-{s}.png")
        make_icon(s, args.text, c1, c2, fg,
                  scale=0.42, opaque=True).save(p)
        print("  ✓", p)

    # iOS：不可透明、不要圓角（系統自己切）
    p = os.path.join(args.out, "apple-touch-icon.png")
    make_icon(180, args.text, c1, c2, fg, opaque=True).convert("RGB").save(p)
    print("  ✓", p)

    # favicon
    p = os.path.join(args.out, "favicon.ico")
    make_icon(256, args.text, c1, c2, fg).save(
        p, sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    print("  ✓", p)

    p = os.path.join(args.out, "icon.svg")
    write_svg(p, args.text, args.bg1, args.bg2, args.fg)
    print("  ✓", p)

    print("\n完成！共 %d 個檔案在 %s/" % (len(os.listdir(args.out)), args.out))


if __name__ == "__main__":
    main()
