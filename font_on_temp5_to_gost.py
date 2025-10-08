# Font_on_TEMP5_to_GOST.py (точки теперь точно в начале каждого слова)
#  Сетка меняется

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, PathPatch, Circle
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from matplotlib.transforms import Affine2D
import numpy as np
import re

# ------------------ Константы ------------------
MM_INCH = 25.4
DEFAULT_PAGE_W, DEFAULT_PAGE_H = 209.9, 296.7
DEFAULT_DPI = 300
DEFAULT_LINE_STEP = 15.5
DEFAULT_THIN_STEP = 1.4
DEFAULT_ANGLE = -15
CORRECTION_K = 0.7

DEFAULT_SPACING = 4.2
DEFAULT_FONT_SIZE = 10.0
DEFAULT_LINE_WIDTH = None
DEFAULT_FRAME_COLOR = "#B3E5FC"
DEFAULT_GRID_COLOR = "#81D4FA"
DEFAULT_FONT_COLOR = "lightgray"

# ------------------ Вспомогательные функции ------------------
def mm_figsize(w_mm, h_mm):
    return (w_mm / MM_INCH, h_mm / MM_INCH)

def draw_frame(ax, page_w, page_h, color, left=20, right=5, top=5, bottom=5):
    x0, y0 = left, bottom
    x1, y1 = page_w - right, page_h - top
    frame = Rectangle((x0, y0), x1 - x0, y1 - y0,
                      linewidth=1.4, edgecolor=color, facecolor="none",
                      transform=ax.transData)
    ax.add_patch(frame)
    return frame, x0, y0, x1, y1

def get_text_scale(cap_height_mm, fontprops):
    tp = TextPath((0, 0), "A", size=100, prop=fontprops)
    bb = tp.get_extents()
    height_pt = (bb.y1 - bb.y0)
    return cap_height_mm / height_pt if height_pt > 0 else 1.0

def _word_path(word, scale, fontprops):
    tp = TextPath((0, 0), word, size=100, prop=fontprops)
    verts = tp.vertices
    x0, x1 = np.min(verts[:, 0]), np.max(verts[:, 0])
    width_mm = (x1 - x0) * scale
    tp_scaled = tp.transformed(Affine2D().scale(scale))
    tp_aligned = tp_scaled.transformed(Affine2D().translate(-x0 * scale, 0))
    return tp_aligned, width_mm, x0 * scale

def measure_line_total_width(text, scale, fontprops, spacing_mm):
    words = [w for w in re.split(r"\s+", text.strip()) if w]
    if not words:
        return 0.0, []
    parts, total_w = [], 0.0
    for w in words:
        path_mm, w_mm, x_offset = _word_path(w, scale, fontprops)
        parts.append((path_mm, w_mm, x_offset))
        total_w += w_mm
    spacing_corr = spacing_mm * CORRECTION_K
    total_w += spacing_corr * (len(words) - 1)
    return total_w, parts

def compute_text_boxes(lines, center_x, base_y, line_step, scale, fontprops,
                       spacing_mm, cap_height_mm, padding=2.0):
    boxes = []
    y = base_y
    for line in lines:
        total_w, _ = measure_line_total_width(line, scale, fontprops, spacing_mm)
        x = center_x - total_w / 2.0 - padding
        h = cap_height_mm + 2 * padding
        y_box = y - padding
        boxes.append((x, y_box, total_w + 2 * padding, h))
        y -= line_step
    return boxes

def draw_grid_in_boxes(ax, boxes, frame_rect, x0, y0, x1, y1,
                       thin_step_h, thin_step_v, angle, color,
                       classic=False):
    for (bx, by, bw, bh) in boxes:
        clip_rect = Rectangle((bx, by), bw, bh, facecolor='none', edgecolor='none',
                              transform=ax.transData)
        ax.add_patch(clip_rect)

        # Горизонтальные линии
        y = y0
        while y <= y1 + 1e-6:
            line = ax.plot([x0, x1], [y, y], color=color, lw=0.1,
                           clip_on=True, transform=ax.transData)[0]
            line.set_clip_path(clip_rect)
            y += thin_step_h

        # Вертикальные или наклонные
        height = y1 - y0
        x_vals = np.arange(x0 - height, x1 + height, thin_step_v)
        if classic:
            for xv in x_vals:
                line = ax.plot([xv, xv], [y0, y1], color=color, lw=0.1,
                               clip_on=True, transform=ax.transData)[0]
                line.set_clip_path(clip_rect)
        else:
            dx = height * np.tan(np.radians(-angle))
            for xv in x_vals:
                line = ax.plot([xv, xv + dx], [y0, y1], color=color, lw=0.1,
                               clip_on=True, transform=ax.transData)[0]
                line.set_clip_path(clip_rect)

def draw_gost_text(ax, text, center_x, y, scale, fontprops,
                   spacing_mm=DEFAULT_SPACING, line_width_mm=DEFAULT_LINE_WIDTH,
                   cap_height_mm=DEFAULT_FONT_SIZE, edge_color=DEFAULT_FONT_COLOR):
    words = [w for w in re.split(r"\s+", text.strip()) if w]
    if not words:
        return
    total_w, parts = measure_line_total_width(text, scale, fontprops, spacing_mm)
    cursor_x = center_x - total_w / 2.0
    gost_line_width = (cap_height_mm / 14.0) if line_width_mm is None else line_width_mm
    spacing_corr = spacing_mm * CORRECTION_K
    for i, (path_mm, w_mm, _) in enumerate(parts):
        path_t = path_mm.transformed(Affine2D().translate(cursor_x, y))
        patch = PathPatch(path_t, facecolor="none", edgecolor=edge_color,
                          lw=gost_line_width, clip_on=True,
                          transform=ax.transData, zorder=10)
        ax.add_patch(patch)
        cursor_x += w_mm
        if i < len(parts) - 1:
            cursor_x += spacing_corr

def draw_word_dots(ax, text, center_x, y, scale, fontprops, spacing_mm, cap_height_mm, dot_color):
    if not text.strip():
        return
    total_w, parts = measure_line_total_width(text, scale, fontprops, spacing_mm)
    cursor_x = center_x - total_w / 2.0
    radius = (cap_height_mm / 14.0) / 2.0
    spacing_corr = spacing_mm * CORRECTION_K
    for i, (_, w_mm, x_offset) in enumerate(parts):
        dot_x = cursor_x + x_offset
        ax.add_patch(Circle((dot_x, y), radius=radius, color=dot_color, zorder=10))
        cursor_x += w_mm
        if i < len(parts) - 1:
            cursor_x += spacing_corr

# ------------------ Класс TextRenderer ------------------
class TextRenderer:
    """
    Класс визуализирует текст с ГОСТ-сеткой, буквами и точками.
    Теперь поддерживает ручное управление толщиной линий шрифта.
    """

    def __init__(self, font_path,
                 spacing=DEFAULT_SPACING,
                 font_size=DEFAULT_FONT_SIZE,
                 line_width=DEFAULT_LINE_WIDTH,  # ✅ добавлено, теперь можно задавать вручную
                 frame_color=DEFAULT_FRAME_COLOR,
                 grid_color=DEFAULT_GRID_COLOR,
                 font_color=DEFAULT_FONT_COLOR,
                 dpi=DEFAULT_DPI,
                 padding=2.0):
        """
        Инициализация параметров отрисовщика.
        """
        self.font = FontProperties(fname=font_path)
        self.spacing = spacing
        self.font_size = font_size
        self.line_width = line_width            # ✅ сохраняем выбранную толщину
        self.frame_color = frame_color
        self.grid_color = grid_color
        self.font_color = font_color
        self.dpi = dpi
        self.padding = padding
        self.scale = get_text_scale(font_size, self.font)

    # -----------------------------------------------------
    def render_to_figure(self, lines,
                         show_grid=True,
                         show_font=True,
                         dots_only=False,
                         classic_grid=False,
                         thin_step_h=DEFAULT_THIN_STEP,
                         thin_step_v=DEFAULT_THIN_STEP):
        """
        Основная функция: создаёт страницу, сетку и текст.
        """
        # Создаём страницу под ГОСТ
        fig = plt.figure(figsize=mm_figsize(DEFAULT_PAGE_W, DEFAULT_PAGE_H), dpi=self.dpi)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, DEFAULT_PAGE_W)
        ax.set_ylim(0, DEFAULT_PAGE_H)
        ax.set_aspect('equal', adjustable='box')
        ax.axis("off")

        # Рамка
        frame_rect, x0, y0, x1, y1 = draw_frame(ax, DEFAULT_PAGE_W, DEFAULT_PAGE_H, self.frame_color)

        # Координаты начала текста
        center_x = (x0 + x1) / 2.0
        start_y = y0 + (y1 - y0) * 0.65
        base_y = start_y - (start_y % DEFAULT_LINE_STEP)

        # Расчёт "боксов" для сетки
        boxes = compute_text_boxes(lines, center_x, base_y,
                                   DEFAULT_LINE_STEP, self.scale, self.font,
                                   self.spacing, self.font_size, padding=self.padding)

        # Отрисовка сетки (если включена)
        if show_grid and not dots_only:
            draw_grid_in_boxes(ax, boxes, frame_rect, x0, y0, x1, y1,
                               thin_step_h=thin_step_h,
                               thin_step_v=thin_step_v,
                               angle=DEFAULT_ANGLE,
                               color=self.grid_color,
                               classic=classic_grid)

        # Отрисовка строк
        y = base_y
        for line in lines:
            # Если показываем только точки или выключен текст
            if dots_only or (not show_font):
                draw_word_dots(ax, line, center_x, y, self.scale, self.font,
                               spacing_mm=self.spacing,
                               cap_height_mm=self.font_size,
                               dot_color=self.font_color)
            # Если показываем буквы
            if show_font and not dots_only:
                draw_gost_text(ax, line, center_x, y, self.scale, self.font,
                               spacing_mm=self.spacing,
                               cap_height_mm=self.font_size,
                               line_width_mm=self.line_width,   # ✅ теперь используется переданная толщина
                               edge_color=self.font_color)
            y -= DEFAULT_LINE_STEP

        return fig
# =====================================================================
# ✏️  РЕЖИМ ОБУЧЕНИЯ — АНИМАЦИЯ РЕАЛЬНЫХ СИМВОЛОВ ГОСТ-ШРИФТА
# ---------------------------------------------------------------------
# Использует реальные контуры букв из .ttf-шрифта и анимирует
# процесс написания (постепенное проявление линий).
# =====================================================================

from matplotlib.textpath import TextPath
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.font_manager import FontProperties
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import os

def render_training_letter_images(
    text_lines,
    image_dir="letter_images",
    save_path="training_images.gif",
    canvas_size=(300, 300),
    frame_duration=0.5
):
    """
    Создаёт gif-анимацию из изображений букв.
    Каждая буква отображается по очереди — согласно введённому тексту.
    """

    print("🎞 Создание gif-анимации из изображений букв...")

    frames = []
    for line in text_lines:
        for ch in line:
            if ch.isspace():
                continue
            suffix = ".upper" if ch.isupper() else ".lower"
            filename = f"{ch}{suffix}.png"
            path = os.path.join(image_dir, filename)

            if not os.path.exists(path):
                print(f"⚠️ Нет изображения для буквы: {ch} → {filename}")
                continue

            img = Image.open(path).convert("RGBA")
            if img.size != canvas_size:
                img = img.resize(canvas_size)

            frames.append(img)

    if not frames:
        print("⚠️ Нет доступных букв для создания анимации.")
        return

    frames[0].save(
        save_path,
        save_all=True,
        append_images=frames[1:],
        duration=int(frame_duration * 5000), # — это длительность одного кадра в миллисекундах
        loop=0
    )

    print(f"✅ GIF сохранён: {save_path}")



    points = np.array(points)
    total_frames = len(points)

    # --- Инициализация анимации ---
    def init():
        drawn_line.set_data([], [])
        return drawn_line,

    # --- Обновление: постепенная прорисовка контуров ---
    def update(frame):
        drawn_line.set_data(points[:frame, 0], points[:frame, 1])
        return drawn_line,

    ani = FuncAnimation(
        fig,
        update,
        frames=total_frames,
        init_func=init,
        interval=frame_interval,
        blit=True,
        repeat=False
    )

    ani.save(save_path, writer=PillowWriter(fps=30))
    plt.close(fig)
    print(f"✅ Анимация написания символов сохранена: {save_path}")
