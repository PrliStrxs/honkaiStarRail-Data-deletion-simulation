import tkinter as tk
from tkinter import font as tkfont
import random
import os
import time

class FixedTransparentErrorSimulator:
    
    def __init__(self, total_duration_seconds=30, progress_update_interval_ms=100):
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

        # 边框区域
        self.border_x1 = self.screen_width * 0.1
        self.border_x2 = self.screen_width * 0.9
        self.border_y1 = self.screen_height * 0.65
        self.border_y2 = self.screen_height * 0.95

        # 文本滚动变量
        self.line_height = 20
        self.current_y = 0
        self.text_items = []
        self.screen_filled = False

        # 错误文本
        self.error_lines = self.load_error_lines()
        self.current_line_index = 0

        # 进度条变量
        self.total_duration_seconds = float(total_duration_seconds)
        self.progress_update_interval_ms = int(progress_update_interval_ms)
        self.progress_text_id = None
        self.progress_percent = 0
        self.start_time = None
        self.last_percent_update = 0

        # name.txt 相关
        self.name_lines = self.load_name_lines()
        self.name_text_ids = []
        try:
            # 可调整 size 为需要的大写
            self.name_font = tkfont.Font(family="微软雅黑", size=20, weight="bold")
        except Exception:
            self.name_font = None
        # 当前正在显示的单行文本 id （单行显示，后续会删除替换）
        self.current_name_text_id = None
        # 用于调度的 after id（方便未来取消）
        self._name_after_ids = []

        # 进度条几何信息
        self.bar_bg_id = None
        self.bar_fill_id = None
        self.bar_slash_ids = []
        self.bar_left = self.bar_top = self.bar_right = self.bar_bottom = 0.0
        self.bar_width = self.bar_height = 0.0

        # 绑定键盘
        self.root.bind('<Escape>', lambda e: self.root.destroy())
        self.root.bind('<KeyPress>', self.on_key_press)

        # 绘制UI
        self.draw_outline_border()

    # -------------------- 辅助函数 -------------------- #
    def load_error_lines(self):
        try:
            if os.path.exists("error.txt"):
                with open("error.txt", "r", encoding="utf-8") as f:
                    lines = [line.rstrip('\n\r') for line in f]
                    return lines or ["(no errors)"]
            else:
                return ["ERROR: error.txt not found", "Simulated error line 2", ""]
        except Exception as e:
            return [f"ERROR reading file: {e}"]

    def load_name_lines(self):
        try:
            if os.path.exists("name.txt"):
                with open("name.txt", "r", encoding="utf-8") as f:
                    # 保留空格与行内容原样
                    lines = [l.rstrip('\n\r') for l in f]
                    return lines or []
            else:
                return []
        except Exception:
            return []

    def get_next_line(self):
        if not self.error_lines:
            return "NO ERROR LINES AVAILABLE"
        line = self.error_lines[self.current_line_index]
        self.current_line_index = (self.current_line_index + 1) % len(self.error_lines)
        return line

    # -------------------- 绘制UI -------------------- #
    def draw_outline_border(self):
        x1 = self.screen_width * 0.1
        y1 = self.screen_height * 0.65
        x2 = self.screen_width - self.screen_width * 0.1
        y2 = self.screen_height - self.screen_height * 0.05

        # 主边框
        self.canvas.create_rectangle(x1, y1, x2, y2, outline="#fe4f4e", width=4, fill="")
        # 内部红色矩形
        inner_left = x1 + 10
        inner_right = x2 - 10
        inner_top = y1 + 7
        inner_bottom = y1 + (y2 - y1) * 0.18
        self.canvas.create_rectangle(inner_left, inner_top, inner_right, inner_bottom,
                                     fill="#fe4f4e", outline="")

        # 百分比小矩形
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
            font=("微软雅黑", 35, "bold"), anchor="center")

        # 三角形 + 感叹号 + 标题文字
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

        # 白色边框（进度条外框） - 先画进度条的内部区域，再画外框，保证外框不被覆盖
        new_rect_top = small_bottom + (y2 - y1) * 0.15
        new_rect_height = (y2 - y1) * 0.13
        new_rect_width = (inner_right - inner_left) * 0.97
        new_rect_left = center_x - new_rect_width / 2
        new_rect_right = center_x + new_rect_width / 2
        new_rect_bottom = new_rect_top + new_rect_height
        if new_rect_bottom > y2:
            new_rect_bottom = y2 - 5

        # 先绘制进度条内部（稍微缩进，避免覆盖边框）
        self.draw_progress_bar(new_rect_left + 2, new_rect_top + 2, new_rect_right - 2, new_rect_bottom - 2)
        # 再绘制白色外框，保证其在上层可见
        self.canvas.create_rectangle(new_rect_left, new_rect_top, new_rect_right, new_rect_bottom,
                                     outline="white", width=3, fill="")

    def draw_progress_bar(self, left, top, right, bottom):
        # 记录内部进度条坐标（已经做了缩进）
        self.bar_left = left + 5
        self.bar_top = top + 5
        self.bar_right = right - 5
        self.bar_bottom = bottom - 5
        self.bar_width = max(1, self.bar_right - self.bar_left)
        self.bar_height = max(1, self.bar_bottom - self.bar_top)

        # bar_bg 用作内部参考（不要把它 raise 到顶层以免覆盖边框）
        try:
            self.bar_bg_id = self.canvas.create_rectangle(
                self.bar_left, self.bar_top, self.bar_right, self.bar_bottom,
                fill="", outline=""
            )
        except Exception:
            self.bar_bg_id = None
        try:
            self.bar_fill_id = self.canvas.create_rectangle(
                self.bar_left, self.bar_top, self.bar_left, self.bar_bottom,
                fill="", outline=""
            )
        except Exception:
            self.bar_fill_id = None
        self.bar_slash_ids = []

    # -------------------- 文本滚动 -------------------- #
    def add_line(self):
        new_line = self.get_next_line()
        text_id = self.canvas.create_text(
            10, self.current_y, text=new_line, fill="#fe1926",
            font=("微软雅黑", 12, "bold"), anchor="nw"
        )
        self.canvas.tag_lower(text_id)  # 保证滚动文本在最底层
        self.text_items.append((text_id, self.current_y, "#fe1926"))
        self.current_y += self.line_height
        if not self.screen_filled and self.current_y >= self.screen_height:
            self.screen_filled = True

    def scroll_all_text_once(self):
        new_items = []
        for (text_id, y_pos, color) in self.text_items:
            new_y = y_pos - self.line_height
            self.canvas.coords(text_id, 10, new_y)
            try:
                self.canvas.itemconfig(text_id, fill=color)
            except Exception:
                pass
            if new_y >= -self.line_height:
                new_items.append((text_id, new_y, color))
            else:
                try:
                    self.canvas.delete(text_id)
                except Exception:
                    pass
        self.text_items = new_items
        self.current_y -= self.line_height
        self.add_line()

    def update_display(self):
        if not self.screen_filled:
            self.add_line()
        else:
            self.scroll_all_text_once()
        delay = random.randint(300, 900)
        self.root.after(delay, self.update_display)

    # -------------------- 进度条 -------------------- #
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

        # 删除旧斜线
        for sid in self.bar_slash_ids:
            try:
                self.canvas.delete(sid)
            except Exception:
                pass
        self.bar_slash_ids = []

        # 绘制新的斜线
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

        # 提升元素顺序（保证三角形/标题在上，进度条斜线和百分比也可见）
        if hasattr(self, 'warning_triangle_id'):
            self.canvas.tag_raise(self.warning_triangle_id)
        if hasattr(self, 'warning_exclamation_id'):
            self.canvas.tag_raise(self.warning_exclamation_id)
        if hasattr(self, 'title_text_id'):
            self.canvas.tag_raise(self.title_text_id)

        # 将进度条元素及百分比抬高（但不覆盖白色外框，因为外框绘制在最后）
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

    # -------------------- name.txt 显示（每秒滚动3行，3个随机时刻都在1秒内） -------------------- #
    def start_name_scrolling(self):
        """开始按每秒3行的模式循环滚动 name.txt"""
        # 清理之前的 after 回调 id（如果有）
        for aid in self._name_after_ids:
            try:
                self.root.after_cancel(aid)
            except Exception:
                pass
        self._name_after_ids = []

        self.name_index = 0  # 下一行索引
        self._schedule_next_triplet()  # 启动循环

    def _schedule_next_triplet(self):
        """
        在接下来的一秒内随机选取三个偏移时间（毫秒，0 <= t < 1000），
        在这些时间点显示 3 行（每次替换上一行），然后递归调度下一秒。
        """
        if not self.name_lines:
            # 没有内容则不做任何调度
            return

        # 生成三个在 [0,1000) 的随机毫秒偏移并排序
        offsets = sorted([random.randint(0, 999) for _ in range(3)])
        base_delay = 0  # 立即开始周期，offsets 相对现在

        # 安全：如果 name_lines 很少，我们仍然循环取行
        for off in offsets:
            # 计划在 off 毫秒后显示一行
            aid = self.root.after(base_delay + off, lambda idx=self.name_index: self._show_name_line_and_advance(idx))
            self._name_after_ids.append(aid)
            # advance index here so lambda captures the correct starting idx for each scheduled call
            self.name_index = (self.name_index + 1) % len(self.name_lines)

        # 在 1000 ms 后再次调度下一批 triplet
        aid_next = self.root.after(1000, self._schedule_next_triplet)
        self._name_after_ids.append(aid_next)

    def _show_name_line_and_advance(self, idx):
        """
        显示 name_lines[idx]（替换之前的单行），注意 idx 是在调度时捕获的值。
        """
        # 删除上一行显示
        if self.current_name_text_id:
            try:
                self.canvas.delete(self.current_name_text_id)
            except Exception:
                pass
            self.current_name_text_id = None

        # 获取文本并显示（水平居中，位置在进度条下方 50 px）
        if not self.name_lines:
            return
        line = self.name_lines[idx % len(self.name_lines)]
        start_y = self.bar_bottom + 50
        center_x = (self.bar_left + self.bar_right) / 2
        try:
            if self.name_font:
                self.current_name_text_id = self.canvas.create_text(center_x, start_y, text=line,
                                                                    fill="white", font=self.name_font, anchor='n')
            else:
                self.current_name_text_id = self.canvas.create_text(center_x, start_y, text=line,
                                                                    fill="white", anchor='n')
        except Exception:
            # 容错：直接创建文本
            self.current_name_text_id = self.canvas.create_text(center_x, start_y, text=line, fill="white", anchor='n')

    # -------------------- 键盘 -------------------- #
    def on_key_press(self, event):
        if event.keysym == 'Escape':
            # 在退出前取消 name 的 after 调用，避免残留
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
        # 启动 name.txt 按每秒 3 行滚动的循环
        self.start_name_scrolling()
        self.root.mainloop()


# -------------------- 主程序 -------------------- #
if __name__ == "__main__":
    app = FixedTransparentErrorSimulator(total_duration_seconds=30, progress_update_interval_ms=100)
    app.run()
