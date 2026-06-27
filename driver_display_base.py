from machine import Pin
import time
from ui_font import FONT


_SWRESET = 0x01
_SLPOUT = 0x11
_DISPON = 0x29
_CASET = 0x2A
_RASET = 0x2B
_RAMWR = 0x2C
_MADCTL = 0x36
_PIXFMT = 0x3A
_NORON = 0x13
_INVOFF = 0x20


_spi_busy = False


def spi_lock():
    global _spi_busy
    while _spi_busy:
        time.sleep_ms(1)
    _spi_busy = True


def spi_unlock():
    global _spi_busy
    _spi_busy = False


class BaseTFT:
    def __init__(self, spi, cs, dc, rst, bl=None, width=160, height=128, name="TFT"):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.bl = bl
        self.width = width
        self.height = height
        self.name = name

        self.cs.init(Pin.OUT, value=1)
        self.dc.init(Pin.OUT, value=0)
        self.rst.init(Pin.OUT, value=1)

        if self.bl:
            self.bl.init(Pin.OUT, value=1)

        self.x_offset = 0
        self.y_offset = 0
        self._fill_cache = {}

    # ========================================================
    # LOW LEVEL WRITE
    # ========================================================

    def write_cmd(self, cmd):
        spi_lock()
        try:
            self.cs.value(0)
            self.dc.value(0)
            self.spi.write(bytes([cmd]))
            self.cs.value(1)
        finally:
            self.cs.value(1)
            spi_unlock()

    def write_data(self, data):
        spi_lock()
        try:
            self.cs.value(0)
            self.dc.value(1)
            self.spi.write(data)
            self.cs.value(1)
        finally:
            self.cs.value(1)
            spi_unlock()

    def write_cmd_data(self, cmd, data):
        self.write_cmd(cmd)
        self.write_data(data)

    def set_window(self, x0, y0, x1, y1):
        x0 += self.x_offset
        x1 += self.x_offset
        y0 += self.y_offset
        y1 += self.y_offset

        self.write_cmd(_CASET)
        self.write_data(bytes([
            (x0 >> 8) & 0xFF, x0 & 0xFF,
            (x1 >> 8) & 0xFF, x1 & 0xFF
        ]))

        self.write_cmd(_RASET)
        self.write_data(bytes([
            (y0 >> 8) & 0xFF, y0 & 0xFF,
            (y1 >> 8) & 0xFF, y1 & 0xFF
        ]))

        self.write_cmd(_RAMWR)

    # ========================================================
    # FAST BLOCK DRAWING
    # ========================================================

    def get_color_chunk(self, color, pixels=2048):
        key = (color, pixels)

        if key in self._fill_cache:
            return self._fill_cache[key]

        hi = (color >> 8) & 0xFF
        lo = color & 0xFF

        chunk = bytearray(pixels * 2)

        for i in range(0, len(chunk), 2):
            chunk[i] = hi
            chunk[i + 1] = lo

        self._fill_cache[key] = chunk
        return chunk

    def blit_buffer(self, x, y, w, h, buf):
        if w <= 0 or h <= 0:
            return

        if x < 0 or y < 0:
            return

        if x + w > self.width or y + h > self.height:
            return

        self.set_window(x, y, x + w - 1, y + h - 1)

        spi_lock()
        try:
            self.cs.value(0)
            self.dc.value(1)
            self.spi.write(buf)
            self.cs.value(1)
        finally:
            self.cs.value(1)
            spi_unlock()

    def fill_rect(self, x, y, w, h, color):
        if w <= 0 or h <= 0:
            return

        if x < 0:
            w += x
            x = 0

        if y < 0:
            h += y
            y = 0

        if x + w > self.width:
            w = self.width - x

        if y + h > self.height:
            h = self.height - y

        if w <= 0 or h <= 0:
            return

        self.set_window(x, y, x + w - 1, y + h - 1)

        chunk_pixels = 2048
        chunk = self.get_color_chunk(color, chunk_pixels)
        mv = memoryview(chunk)
        total_pixels = w * h

        spi_lock()
        try:
            self.cs.value(0)
            self.dc.value(1)

            while total_pixels >= chunk_pixels:
                self.spi.write(chunk)
                total_pixels -= chunk_pixels

            if total_pixels > 0:
                self.spi.write(mv[:total_pixels * 2])

            self.cs.value(1)
        finally:
            self.cs.value(1)
            spi_unlock()

    def fill_screen(self, color):
        self.fill_rect(0, 0, self.width, self.height, color)

    # ========================================================
    # TEXT DRAWING
    # ========================================================

    def draw_char(self, x, y, ch, color, scale=1):
        if ch in FONT:
            bitmap = FONT[ch]
        else:
            ch = ch.upper()
            bitmap = FONT.get(ch, FONT[" "])

        for row_index, row in enumerate(bitmap):
            col = 0

            while col < 5:
                while col < 5 and row[col] != "1":
                    col += 1

                if col >= 5:
                    break

                start_col = col

                while col < 5 and row[col] == "1":
                    col += 1

                run_len = col - start_col

                self.fill_rect(
                    x + start_col * scale,
                    y + row_index * scale,
                    run_len * scale,
                    scale,
                    color
                )

    def text_width(self, text, scale):
        if not text:
            return 0

        return len(text) * 6 * scale - scale

    def draw_text(self, x, y, text, color, scale=1):
        cx = x

        for ch in text:
            self.draw_char(cx, y, ch, color, scale)
            cx += 6 * scale

    def draw_center_text(self, y, text, color, scale=1):
        tw = self.text_width(text, scale)
        x = (self.width - tw) // 2
        self.draw_text(x, y, text, color, scale)

    def draw_text_box(self, x, y, text, fg_color, bg_color, scale=1):
        """
        Faster text drawing for labels/menus.

        It renders the entire text into one small RGB565 buffer, then pushes
        the buffer in one SPI window transaction. This keeps the current pixel
        font texture but avoids many tiny SPI writes.
        """
        if text is None:
            text = ""

        w = self.text_width(text, scale)

        if w <= 0:
            return 0, 0

        h = 7 * scale

        if x < 0 or y < 0:
            return 0, 0

        if x + w > self.width:
            w = self.width - x

        if y + h > self.height:
            h = self.height - y

        if w <= 0 or h <= 0:
            return 0, 0

        fg_hi = (fg_color >> 8) & 0xFF
        fg_lo = fg_color & 0xFF

        bg_hi = (bg_color >> 8) & 0xFF
        bg_lo = bg_color & 0xFF

        buf = bytearray(w * h * 2)

        # Fill background
        for i in range(0, len(buf), 2):
            buf[i] = bg_hi
            buf[i + 1] = bg_lo

        for char_index, ch in enumerate(text):
            if ch in FONT:
                bitmap = FONT[ch]
            else:
                bitmap = FONT.get(ch.upper(), FONT[" "])

            base_x = char_index * 6 * scale

            for row_index, row in enumerate(bitmap):
                for col_index in range(5):
                    if row[col_index] == "1":
                        px0 = base_x + col_index * scale
                        py0 = row_index * scale

                        for sy in range(scale):
                            py = py0 + sy

                            if py >= h:
                                continue

                            for sx in range(scale):
                                px = px0 + sx

                                if px >= w:
                                    continue

                                index = ((py * w) + px) * 2
                                buf[index] = fg_hi
                                buf[index + 1] = fg_lo

        self.blit_buffer(x, y, w, h, buf)
        return w, h

    def draw_center_text_box(self, y, text, fg_color, bg_color, scale=1):
        tw = self.text_width(text, scale)
        x = (self.width - tw) // 2
        return self.draw_text_box(x, y, text, fg_color, bg_color, scale)

    def draw_rect(self, x, y, w, h, color, thickness=2):
        self.fill_rect(x, y, w, thickness, color)
        self.fill_rect(x, y + h - thickness, w, thickness, color)
        self.fill_rect(x, y, thickness, h, color)
        self.fill_rect(x + w - thickness, y, thickness, h, color)