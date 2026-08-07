# -*- coding: utf-8 -*-
"""生成 PDF2BOOK AI 应用图标

生成一套完整的图标：
- icon.ico (Windows 多尺寸)
- icon_256.png (高清)
- installer_banner.bmp (安装包横幅)
- installer_small.bmp (安装包小图标)
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUTPUT_DIR = Path(r"G:\0010.实用工具\工具箱\pdf-to-epub\PDF2BOOK_AI\resources")


def draw_book_icon(size: int) -> Image.Image:
    """绘制书本+AI 图标"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 外圈渐变背景（深蓝→紫）
    margin = int(size * 0.05)
    radius = size // 2 - margin

    # 圆角矩形背景
    bg_margin = int(size * 0.08)
    bg_radius = int(size * 0.15)
    draw.rounded_rectangle(
        [bg_margin, bg_margin, size - bg_margin, size - bg_margin],
        radius=bg_radius,
        fill=(11, 76, 163, 255),  # #0B4CA3 深蓝
    )

    # 内层渐变模拟（叠加半透明圆）
    for i in range(20):
        alpha = int(8 - i * 0.3)
        if alpha <= 0:
            break
        overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        offset = int(size * 0.15) - i * 2
        od.ellipse(
            [bg_margin + offset, bg_margin + offset,
             size - bg_margin - offset, int(size * 0.6)],
            fill=(99, 102, 241, alpha * 10),  # 紫色调
        )
        img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)

    # 书本主体（白色翻开的书）
    book_w = int(size * 0.45)
    book_h = int(size * 0.55)
    book_x = (size - book_w) // 2
    book_y = int(size * 0.22)

    # 书本底色
    draw.rounded_rectangle(
        [book_x, book_y, book_x + book_w, book_y + book_h],
        radius=int(size * 0.02),
        fill=(255, 255, 255, 255),
    )

    # 书脊（中间线）
    spine_x = book_x + book_w // 2
    draw.line(
        [spine_x, book_y + int(size * 0.02), spine_x, book_y + book_h - int(size * 0.02)],
        fill=(180, 190, 210, 255),
        width=max(1, size // 128),
    )

    # 书本文字线条（模拟文字）
    line_color = (140, 150, 170, 180)
    line_margin = int(size * 0.05)
    line_start_x = book_x + line_margin
    line_end_l = spine_x - int(size * 0.015)
    line_end_r = spine_x + int(size * 0.015)
    line_end_x = book_x + book_w - line_margin

    for i in range(5):
        ly = book_y + int(size * 0.08) + i * int(size * 0.075)
        if ly > book_y + book_h - int(size * 0.04):
            break
        # 左页线
        line_w_l = line_end_l - line_start_x - int(size * 0.01) * (i % 2)
        draw.line([line_start_x, ly, line_start_x + line_w_l, ly],
                  fill=line_color, width=max(1, size // 200))
        # 右页线
        line_w_r = line_end_x - line_end_r - int(size * 0.01) * (i % 3)
        draw.line([line_end_r, ly, line_end_r + line_w_r, ly],
                  fill=line_color, width=max(1, size // 200))

    # AI 标记（右下角金色圆点）
    ai_r = int(size * 0.08)
    ai_x = book_x + book_w - int(size * 0.02)
    ai_y = book_y + book_h + int(size * 0.02)
    draw.ellipse(
        [ai_x - ai_r, ai_y - ai_r, ai_x + ai_r, ai_y + ai_r],
        fill=(255, 193, 7, 255),  # 金色 #FFC107
    )

    # AI 文字
    try:
        font_size = int(size * 0.075)
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    ai_text = "AI"
    bbox = draw.textbbox((0, 0), ai_text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(
        (ai_x - tw // 2, ai_y - th // 2 - int(size * 0.005)),
        ai_text,
        fill=(11, 76, 163, 255),
        font=font,
    )

    return img


def draw_installer_banner(width: int = 497, height: int = 58) -> Image.Image:
    """安装包顶部横幅（Inno Setup 标准 497x58）"""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 深蓝渐变背景
    for x in range(width):
        r = int(11 + (99 - 11) * x / width)
        g = int(76 + (102 - 76) * x / width)
        b = int(163 + (241 - 163) * x / width)
        draw.line([x, 0, x, height], fill=(r, g, b, 255))

    # 左侧图标（小尺寸）
    icon_size = 40
    icon = draw_book_icon(icon_size)
    img.paste(icon, (9, (height - icon_size) // 2), icon)

    # 标题文字
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 16)
        sub_font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 11)
    except Exception:
        font = ImageFont.load_default()
        sub_font = font

    draw.text((55, 8), "PDF2BOOK AI", fill=(255, 255, 255, 255), font=font)
    draw.text((55, 30), "AI 智能电子书重构平台", fill=(200, 210, 240, 255), font=sub_font)

    # 右侧版本号
    try:
        ver_font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 12)
    except Exception:
        ver_font = ImageFont.load_default()
    draw.text((width - 60, height - 20), "v4.0", fill=(180, 190, 230, 255), font=ver_font)

    return img


def draw_installer_small(width: int = 55, height: int = 55) -> Image.Image:
    """安装包小图标（Inno Setup 标准 55x55）"""
    return draw_book_icon(width)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 生成多尺寸图标
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []
    for s in sizes:
        img = draw_book_icon(s)
        images.append(img)
        print(f"  生成 {s}x{s}")

    # 保存 ICO（Pillow 需要传入完整尺寸列表）
    ico_path = OUTPUT_DIR / "icon.ico"
    # 用最大尺寸作为基础，保存时指定多尺寸
    base = draw_book_icon(256)
    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    base.save(ico_path, format="ICO", sizes=ico_sizes)
    print(f"  ICO: {ico_path} ({ico_path.stat().st_size} bytes)")

    # 保存高清 PNG
    png_256 = draw_book_icon(256)
    png_path = OUTPUT_DIR / "icon_256.png"
    png_256.save(png_path, format="PNG")
    print(f"  PNG: {png_path} ({png_path.stat().st_size} bytes)")

    # 安装包横幅
    banner = draw_installer_banner()
    banner_path = OUTPUT_DIR / "installer_banner.bmp"
    # BMP 不支持 alpha，转 RGB
    banner.convert("RGB").save(banner_path, format="BMP")
    print(f"  Banner: {banner_path} ({banner_path.stat().st_size} bytes)")

    # 安装包小图标
    small = draw_installer_small()
    small_path = OUTPUT_DIR / "installer_small.bmp"
    small.convert("RGB").save(small_path, format="BMP")
    print(f"  Small: {small_path} ({small_path.stat().st_size} bytes)")

    print("\n所有图标资源生成完成！")


if __name__ == "__main__":
    main()
