import tkinter as tk
import random
import os
import time
from PIL import Image, ImageDraw, ImageFont, ImageTk
import sys

class FixedTransparentErrorSimulator:
    def __init__(self, total_duration_seconds=30, progress_update_interval_ms=100):
        # 窗口与画布
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        try:
            self.root.attributes('-transparentcolor', 'black')
            self.root.configure(bg='black')
        except Exception:
            self.root.configure(bg='black')
        self.root.overrideredirect(True)

        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0,
                                width=self.screen_width, height=self.screen_height)
        self.canvas.pack()

        # 主边框与内框几何（保持原始风格）
        self.border_x1 = int(self.screen_width * 0.1)
        self.border_x2 = int(self.screen_width * 0.9)
        self.border_y1 = int(self.screen_height * 0.65)
        self.border_y2 = int(self.screen_height * 0.95)

        self.inner_left = self.border_x1 + 10
        self.inner_right = self.border_x2 - 10
        self.inner_top = self.border_y1 + 7
        self.inner_bottom = int(self.border_y1 + (self.border_y2 - self.border_y1) * 0.18)

        # 进度条参考位置（保持原视觉）
        small_rect_height = (self.border_y2 - self.border_y1) * 0.08
        center_x = (self.inner_left + self.inner_right) / 2
        small_top = self.inner_bottom + (self.border_y2 - self.border_y1) * 0.10
        small_bottom = small_top + small_rect_height
        new_rect_top = small_bottom + (self.border_y2 - self.border_y1) * 0.15
        new_rect_height = (self.border_y2 - self.border_y1) * 0.13
        new_rect_width = (self.inner_right - self.inner_left) * 0.97
        new_rect_left = center_x - new_rect_width / 2
        new_rect_right = center_x + new_rect_width / 2
        new_rect_bottom = new_rect_top + new_rect_height
        if new_rect_bottom > self.border_y2:
            new_rect_bottom = self.border_y2 - 5
        self._progress_rect = (new_rect_left + 2, new_rect_top + 2, new_rect_right - 2, new_rect_bottom - 2)

        # 错误文本区域：整个屏幕左侧（红框外），垂直覆盖整个屏幕（从最顶到最底）
        self.text_area_left = 10
        self.text_area_right = max(self.text_area_left + 50, self.inner_left - 10)
        # 这里是关键改动：从屏幕顶部到屏幕底部
        self.text_area_top = 0
        self.text_area_bottom = self.screen_height

        # 文本滚动容器：每行一张图片（保留空行）
        self.text_items = []  # 存储 (canvas_id, y_pos, img_ref, height)
        self.current_y = self.text_area_top
        self.screen_filled = False

        # 读取文件
        self.error_lines = self.load_error_lines()
        self.current_line_index = 0
        self.name_lines = self.load_name_lines()

        # 进度条
        self.total_duration_seconds = float(total_duration_seconds)
        self.progress_update_interval_ms = int(progress_update_interval_ms)
        self.progress_text_id = None
        self.progress_percent = 0
        self.start_time = None
        self.last_percent_update = 0
        self.bar_bg_id = None
        self.bar_fill_id = None
        self.bar_slash_ids = []

        # name.txt 显示
        self.current_name_text_id = None
        self._name_after_ids = []

        # PIL 字体
        self.default_font_size = 16
        self.name_font_size = 22
        self.pil_font = self._load_font(size=self.default_font_size)
        self.pil_name_font = self._load_font(size=self.name_font_size)

        # 保持 PhotoImage 引用，防止 GC
        self._image_refs = []

        # 绑定按键退出
        self.root.bind('<Escape>', lambda e: self.root.destroy())
        self.root.bind('<KeyPress>', self.on_key_press)

        # 绘制边框/进度条等 UI
        self.draw_outline_border()

    # -------------------- 字体 / 文件 -------------------- #
    def _load_font(self, size=16):
        candidates = []
        if sys.platform.startswith("win"):
            candidates = [
                r"C:\Windows\Fonts\msyh.ttc",
                r"C:\Windows\Fonts\msyhbd.ttf",
                r"C:\Windows\Fonts\simhei.ttf",
                r"C:\Windows\Fonts\segoeui.ttf",
            ]
        elif sys.platform.startswith("darwin"):
            candidates = [
                "/System/Library/Fonts/STHeiti Medium.ttc",
                "/Library/Fonts/Arial.ttf",
            ]
        else:
            candidates = [
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            ]
        for path in candidates:
            try:
                if os.path.exists(path):
                    return ImageFont.truetype(path, size)
            except Exception:
                pass
        try:
            return ImageFont.load_default()
        except Exception:
            return None

    def load_error_lines(self):
        try:
            if os.path.exists("error.txt"):
                with open("error.txt", "r", encoding="utf-8") as f:
                    # 保留空行、不要 trim
                    lines = [line.rstrip('\n\r') for line in f.readlines()]
                    return lines or ["(no errors)"]
            else:
                # 示例行便于测试
                return [
                    "ERROR: error.txt not found",
                    "Simulated error line 2 - long sample to test.",
                    "",
                    "Next error: Disk read failed at sector 31244",
                ]
        except Exception as e:
            return [f"ERROR reading file: {e}"]

    def load_name_lines(self):
        try:
            if os.path.exists("name.txt"):
                with open("name.txt", "r", encoding="utf-8") as f:
                    return [l.rstrip('\n\r') for l in f.readlines()] or []
            else:
                return []
        except Exception:
            return []

    def get_next_line(self):
        if not self.error_lines:
            return ""
        line = self.error_lines[self.current_line_index]
        self.current_line_index = (self.current_line_index + 1) % len(self.error_lines)
        return line

    # -------------------- 绘制边框 / 进度条 -------------------- #
    def draw_outline_border(self):
        x1 = self.border_x1; y1 = self.border_y1; x2 = self.border_x2; y2 = self.border_y2
        self.canvas.create_rectangle(x1, y1, x2, y2, outline="#fe4f4e", width=4, fill="")

        inner_left = self.inner_left; inner_right = self.inner_right
        inner_top = self.inner_top; inner_bottom = self.inner_bottom
        self.canvas.create_rectangle(inner_left, inner_top, inner_right, inner_bottom,
                                     fill="#fe4f4e", outline="")

        small_rect_height = (y2 - y1) * 0.08
        small_rect_width = (inner_right - inner_left) * 0.15
        center_x = (inner_left + inner_right) / 2
        small_top = inner_bottom + (y2 - y1) * 0.10
        small_bottom = small_top + small_rect_height
        small_left = center_x - small_rect_width / 2
        small_right = center_x + small_rect_width / 2
        self.canvas.create_rectangle(small_left, small_top, small_right, small_bottom,
                                     fill="#450e0f", outline="")

        self.progress_text_id = self.canvas.create_text(
            center_x, (small_top + small_bottom)/2, text="0%", fill="white",
            font=("微软雅黑", 28, "bold"), anchor="center")

        rect_center_x = (inner_left + inner_right) / 2
        rect_center_y = (inner_top + inner_bottom) / 2
        triangle_size = 20
        self.warning_triangle_id = self.canvas.create_polygon(
            rect_center_x - 60, rect_center_y - triangle_size,
            rect_center_x - 60 - triangle_size, rect_center_y + triangle_size,
            rect_center_x - 60 + triangle_size, rect_center_y + triangle_size,
            fill="white", outline="white"
        )
        self.warning_exclamation_id = self.canvas.create_text(
            rect_center_x - 60, rect_center_y, text="!", fill="#fe4f4e",
            font=("Arial", 18, "bold")
        )
        self.title_text_id = self.canvas.create_text(
            rect_center_x - 15, rect_center_y, text="数据删除进度",
            fill="white", font=("微软雅黑", 14, "bold"), anchor="w"
        )

        new_rect_top = small_bottom + (y2 - y1) * 0.15
        new_rect_height = (y2 - y1) * 0.13
        new_rect_width = (inner_right - inner_left) * 0.97
        new_rect_left = center_x - new_rect_width / 2
        new_rect_right = center_x + new_rect_width / 2
        new_rect_bottom = new_rect_top + new_rect_height
        if new_rect_bottom > y2:
            new_rect_bottom = y2 - 5

        self.draw_progress_bar(new_rect_left + 2, new_rect_top + 2, new_rect_right - 2, new_rect_bottom - 2)
        self.canvas.create_rectangle(new_rect_left, new_rect_top, new_rect_right, new_rect_bottom,
                                     outline="white", width=3, fill="")

    def draw_progress_bar(self, left, top, right, bottom):
        self.bar_left = left + 5
        self.bar_top = top + 5
        self.bar_right = right - 5
        self.bar_bottom = bottom - 5
        self.bar_width = max(1, self.bar_right - self.bar_left)
        self.bar_height = max(1, self.bar_bottom - self.bar_top)
        try:
            self.bar_bg_id = self.canvas.create_rectangle(self.bar_left, self.bar_top, self.bar_right, self.bar_bottom,
                                                          fill="", outline="")
        except Exception:
            self.bar_bg_id = None
        try:
            self.bar_fill_id = self.canvas.create_rectangle(self.bar_left, self.bar_top, self.bar_left, self.bar_bottom,
                                                            fill="", outline="")
        except Exception:
            self.bar_fill_id = None
        self.bar_slash_ids = []

    # -------------------- 文本测量与渲染（不换行，保留空行） -------------------- #
    def _measure_text(self, draw_obj, text, font):
        try:
            bbox = draw_obj.textbbox((0,0), text, font=font)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            try:
                return font.getsize(text)
            except Exception:
                est_w = max(1, int(len(text) * (getattr(font, "size", 12) * 0.6)))
                est_h = max(1, getattr(font, "size", 12))
                return est_w, est_h

    def draw_smooth_text_image(self, text, font=None, font_size=None, color=(255,255,255,255)):
        """
        将一整行（包括空字符串）渲染为一张图片（不换行）。
        空行会得到高度与字体高度相当的透明图片，保证显示占位。
        返回 (PhotoImage, (w,h))
        """
        if font is None:
            font = self.pil_font
        if font_size is not None:
            try:
                if isinstance(font, ImageFont.FreeTypeFont) and hasattr(font, "path"):
                    font = ImageFont.truetype(font.path, font_size)
                else:
                    font = self._load_font(font_size)
            except Exception:
                font = self._load_font(font_size)

        dummy = Image.new("RGBA", (10,10), (0,0,0,0))
        draw = ImageDraw.Draw(dummy)
        w, h = self._measure_text(draw, text, font)

        # 如果是空行或测量到 0，高度设置为字体大小
        if not text or w <= 0 or h <= 0:
            h = getattr(font, "size", self.default_font_size)
            w = max(2, w)

        pad_x = 6
        pad_y = 3
        img = Image.new("RGBA", (w + pad_x*2, h + pad_y*2), (0,0,0,0))
        d = ImageDraw.Draw(img)
        if text:
            d.text((pad_x, pad_y), text, font=font, fill=color)
        tk_img = ImageTk.PhotoImage(img)
        self._image_refs.append(tk_img)
        return tk_img, img.size

    # -------------------- 添加一行（按 file 中每一行） -------------------- #
    def add_line(self):
        new_line = self.get_next_line()  # 可能是空字符串
        tk_img, size = self.draw_smooth_text_image(new_line, font=self.pil_font,
                                                   font_size=self.default_font_size,
                                                   color=(254,25,38,255))
        x = self.text_area_left
        y = int(self.current_y)
        img_id = self.canvas.create_image(x, y, image=tk_img, anchor='nw')
        item = (img_id, y, tk_img, size[1])
        self.text_items.append(item)

        increment = size[1]
        if increment <= 0:
            increment = getattr(self.pil_font, "size", self.default_font_size)
        self.current_y += increment

        # 标记填满（开始滚动）条件：当 current_y 超过 text_area_bottom（现在是屏幕底）
        if not self.screen_filled and self.current_y >= self.text_area_bottom:
            self.screen_filled = True

    # -------------------- 按最顶部项高度滚动一次（保证整行完整移动） -------------------- #
    def scroll_all_text_once(self):
        if not self.text_items:
            self.add_line()
            return

        first_item = self.text_items[0]
        step = first_item[3]
        if step <= 0:
            step = getattr(self.pil_font, "size", self.default_font_size)

        new_items = []
        for (img_id, y_pos, img_ref, height) in self.text_items:
            new_y = y_pos - step
            self.canvas.coords(img_id, self.text_area_left, new_y)
            if new_y + height >= self.text_area_top:
                new_items.append((img_id, new_y, img_ref, height))
            else:
                try:
                    self.canvas.delete(img_id)
                except Exception:
                    pass
                try:
                    if img_ref in self._image_refs:
                        self._image_refs.remove(img_ref)
                except Exception:
                    pass

        self.text_items = new_items
        self.current_y -= step
        self.add_line()

    def update_display(self):
        if not self.screen_filled:
            self.add_line()
        else:
            self.scroll_all_text_once()
        delay = random.randint(300, 900)
        self.root.after(delay, self.update_display)

    # -------------------- 进度条更新 -------------------- #
    def update_progress_time_based(self):
        if self.start_time is None:
            self.start_time = time.monotonic()
            self.last_percent_update = self.start_time
        current_time = time.monotonic()
        seconds_since_last_update = current_time - self.last_percent_update
        if seconds_since_last_update >= 3 and self.progress_percent < 100:
            self.progress_percent += 1
            self.last_percent_update = current_time
        self.progress_percent = min(100, self.progress_percent)
        try:
            self.canvas.itemconfig(self.progress_text_id, text=f"{self.progress_percent}%")
        except Exception:
            pass
        self.update_progress_bar()
        if self.progress_percent < 100:
            self.root.after(self.progress_update_interval_ms, self.update_progress_time_based)
        else:
            try:
                self.canvas.itemconfig(self.progress_text_id, fill="#FFFFFF")
            except Exception:
                pass

    def update_progress_bar(self):
        if not self.bar_fill_id:
            return
        progress_width = (self.bar_width * (self.progress_percent / 100.0))
        new_right = self.bar_left + progress_width
        try:
            self.canvas.coords(self.bar_fill_id, self.bar_left, self.bar_top, new_right, self.bar_bottom)
        except Exception:
            pass

        for sid in self.bar_slash_ids:
            try:
                self.canvas.delete(sid)
            except Exception:
                pass
        self.bar_slash_ids = []

        if progress_width > 6:
            slash_spacing = 14
            slash_length = max(8, self.bar_height - 8)
            slash_width = max(4, int(self.bar_height / 4))
            x = self.bar_left + slash_spacing / 2
            max_x = new_right - 2
            while x < max_x:
                x1 = x - slash_length / 4
                y1 = self.bar_bottom - 3
                x2 = x + slash_length / 4
                y2 = self.bar_top + 3
                sid = self.canvas.create_line(x1, y1, x2, y2, fill="#ffffff", width=slash_width)
                self.bar_slash_ids.append(sid)
                x += slash_spacing

        if hasattr(self, 'warning_triangle_id'):
            self.canvas.tag_raise(self.warning_triangle_id)
        if hasattr(self, 'warning_exclamation_id'):
            self.canvas.tag_raise(self.warning_exclamation_id)
        if hasattr(self, 'title_text_id'):
            self.canvas.tag_raise(self.title_text_id)
        if self.bar_bg_id:
            try:
                self.canvas.tag_raise(self.bar_bg_id)
            except Exception:
                pass
        if self.bar_fill_id:
            try:
                self.canvas.tag_raise(self.bar_fill_id)
            except Exception:
                pass
        for sid in self.bar_slash_ids:
            try:
                self.canvas.tag_raise(sid)
            except Exception:
                pass
        if self.progress_text_id:
            try:
                self.canvas.tag_raise(self.progress_text_id)
            except Exception:
                pass

    # -------------------- name.txt 显示（保持原样） -------------------- #
    def start_name_scrolling(self):
        for aid in self._name_after_ids:
            try:
                self.root.after_cancel(aid)
            except Exception:
                pass
        self._name_after_ids = []
        self.name_index = 0
        self._schedule_next_triplet()

    def _schedule_next_triplet(self):
        if not self.name_lines:
            return
        offsets = sorted([random.randint(0, 999) for _ in range(3)])
        base_delay = 0
        for off in offsets:
            aid = self.root.after(base_delay + off, lambda idx=self.name_index: self._show_name_line_and_advance(idx))
            self._name_after_ids.append(aid)
            self.name_index = (self.name_index + 1) % len(self.name_lines)
        aid_next = self.root.after(1000, self._schedule_next_triplet)
        self._name_after_ids.append(aid_next)

    def _show_name_line_and_advance(self, idx):
        if self.current_name_text_id:
            try:
                cid, img_ref = self.current_name_text_id
                self.canvas.delete(cid)
                if img_ref in self._image_refs:
                    self._image_refs.remove(img_ref)
            except Exception:
                pass
            self.current_name_text_id = None

        if not self.name_lines:
            return
        line = self.name_lines[idx % len(self.name_lines)]
        start_y = int(self.bar_bottom + 50)
        center_x = int((self.bar_left + self.bar_right) / 2)
        tk_img, size = self.draw_smooth_text_image(line, font=self.pil_name_font, font_size=self.name_font_size,
                                                   color=(255,255,255,255))
        img_w, img_h = size
        x = center_x - img_w // 2
        cid = self.canvas.create_image(x, start_y, image=tk_img, anchor='nw')
        self.current_name_text_id = (cid, tk_img)

    # -------------------- 键盘 -------------------- #
    def on_key_press(self, event):
        if event.keysym == 'Escape':
            for aid in self._name_after_ids:
                try:
                    self.root.after_cancel(aid)
                except Exception:
                    pass
            self._name_after_ids = []
            self.root.destroy()

    # -------------------- 运行 -------------------- #
    def run(self):
        self.start_time = time.monotonic()
        self.last_percent_update = self.start_time
        self.update_progress_time_based()
        self.update_display()
        self.start_name_scrolling()
        self.root.mainloop()


if __name__ == "__main__":
    app = FixedTransparentErrorSimulator(total_duration_seconds=30, progress_update_interval_ms=100)
    app.run()
