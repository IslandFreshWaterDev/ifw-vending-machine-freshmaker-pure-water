import time
from ui_colors import BLACK, WHITE, SKYBLUE
from config import HEADER_UPDATE_MS


class Header:
    def __init__(self, layout, brand="PUREMAKER BY ISLAND FRESH"):
        self.layout = layout
        self.brand = brand
        self.last_datetime = None
        self.last_update_ms = 0

    def format_datetime(self):
        try:
            y, mo, d, h, mi, s, wd, yd = time.localtime()
            suffix = "AM"
            hour = h

            if hour == 0:
                hour = 12
            elif hour == 12:
                suffix = "PM"
            elif hour > 12:
                hour -= 12
                suffix = "PM"

            return "{}/{}/{} {}:{:02d}{}".format(mo, d, y, hour, mi, suffix)
        except Exception:
            return "1/1/2000 12:00AM"

    def draw_static(self, tft):
        tft.draw_center_text_box(
            self.layout["brand_y"],
            self.brand,
            SKYBLUE,
            BLACK,
            scale=self.layout["brand_scale"]
        )

    def update_datetime(self, tft, force=False):
        now_ms = time.ticks_ms()

        if not force:
            if self.last_update_ms != 0:
                if time.ticks_diff(now_ms, self.last_update_ms) < HEADER_UPDATE_MS:
                    return

        self.last_update_ms = now_ms

        text = self.format_datetime()

        if not force and text == self.last_datetime:
            return

        clear_h = 8 * self.layout["datetime_scale"] + 2

        tft.fill_rect(
            0,
            self.layout["datetime_y"],
            self.layout["w"],
            clear_h,
            BLACK
        )

        tft.draw_text_box(
            0,
            self.layout["datetime_y"],
            text,
            WHITE,
            BLACK,
            scale=self.layout["datetime_scale"]
        )

        self.last_datetime = text

    def draw(self, tft):
        self.update_datetime(tft, force=True)
        self.draw_static(tft)