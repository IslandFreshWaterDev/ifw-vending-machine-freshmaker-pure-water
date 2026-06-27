import time

from ui_colors import BLACK, WHITE, YELLOW, SKYBLUE, CYAN, GREEN, RED

from config import (
    DISPENSE_UI_UPDATE_MS,
    DISPENSE_ML_STEP,
)


class DispensingPage:
    def __init__(self, layout, mode_text):
        self.layout = layout
        self.mode_text = mode_text

        self.last_percent = None
        self.last_ml_text = None
        self.last_fill_w = None

        self.last_ui_update_ms = 0
        self.last_ml_bucket = None

    def set_mode(self, mode_text):
        self.mode_text = mode_text

    def draw_static(self, tft):
        tft.fill_screen(BLACK)

        tft.draw_center_text_box(
            self.layout["disp_title_y"],
            "DISPENSING",
            SKYBLUE,
            BLACK,
            scale=self.layout["disp_title_scale"]
        )

        tft.draw_center_text_box(
            self.layout["disp_mode_y"],
            self.mode_text,
            WHITE,
            BLACK,
            scale=self.layout["disp_mode_scale"]
        )

        bx = self.layout["bar_x"]
        by = self.layout["bar_y"]
        bw = self.layout["bar_w"]
        bh = self.layout["bar_h"]
        border = self.layout["bar_border"]

        tft.draw_rect(
            bx,
            by,
            bw,
            bh,
            CYAN,
            thickness=border
        )

        tft.fill_rect(
            bx + border,
            by + border,
            bw - (border * 2),
            bh - (border * 2),
            BLACK
        )

        tft.draw_center_text_box(
            self.layout["cancel_y"],
            "HOLD TO CANCEL",
            SKYBLUE,
            BLACK,
            scale=self.layout["cancel_scale"]
        )

        self.last_percent = None
        self.last_ml_text = None
        self.last_fill_w = None
        self.last_ui_update_ms = 0
        self.last_ml_bucket = None

    def _should_update_now(self, force=False):
        if force:
            return True

        now = time.ticks_ms()

        if self.last_ui_update_ms == 0:
            self.last_ui_update_ms = now
            return True

        if time.ticks_diff(now, self.last_ui_update_ms) >= DISPENSE_UI_UPDATE_MS:
            self.last_ui_update_ms = now
            return True

        return False

    def _ml_bucket(self, ml):
        if DISPENSE_ML_STEP <= 1:
            return ml

        return int(ml / DISPENSE_ML_STEP) * DISPENSE_ML_STEP

    def update_progress(self, tft, percent, current_ml, target_ml, force=False):
        if percent < 0:
            percent = 0

        if percent > 100:
            percent = 100

        if current_ml < 0:
            current_ml = 0

        if current_ml > target_ml:
            current_ml = target_ml

        current_ml_bucket = self._ml_bucket(current_ml)

        # Always update at 0 and 100, otherwise throttle.
        if percent == 0 or percent >= 100:
            force = True

        if not self._should_update_now(force=force):
            return

        # ====================================================
        # PROGRESS BAR
        # ====================================================

        bx = self.layout["bar_x"]
        by = self.layout["bar_y"]
        bw = self.layout["bar_w"]
        bh = self.layout["bar_h"]
        border = self.layout["bar_border"]

        inner_x = bx + border
        inner_y = by + border
        inner_w = bw - (border * 2)
        inner_h = bh - (border * 2)

        fill_w = int((inner_w * percent) / 100)

        if fill_w != self.last_fill_w:
            if self.last_fill_w is None:
                tft.fill_rect(
                    inner_x,
                    inner_y,
                    inner_w,
                    inner_h,
                    BLACK
                )

                if fill_w > 0:
                    tft.fill_rect(
                        inner_x,
                        inner_y,
                        fill_w,
                        inner_h,
                        CYAN
                    )

            else:
                # Faster incremental bar drawing.
                if fill_w > self.last_fill_w:
                    tft.fill_rect(
                        inner_x + self.last_fill_w,
                        inner_y,
                        fill_w - self.last_fill_w,
                        inner_h,
                        CYAN
                    )
                elif fill_w < self.last_fill_w:
                    tft.fill_rect(
                        inner_x + fill_w,
                        inner_y,
                        self.last_fill_w - fill_w,
                        inner_h,
                        BLACK
                    )

            self.last_fill_w = fill_w

        # ====================================================
        # PERCENT TEXT
        # ====================================================

        if percent != self.last_percent:
            tft.fill_rect(
                0,
                self.layout["percent_y"],
                self.layout["w"],
                8 * self.layout["percent_scale"] + 2,
                BLACK
            )

            tft.draw_center_text_box(
                self.layout["percent_y"],
                "{}%".format(percent),
                YELLOW,
                BLACK,
                scale=self.layout["percent_scale"]
            )

            self.last_percent = percent

        # ====================================================
        # ML TEXT
        # ====================================================

        if self.last_ml_bucket != current_ml_bucket or force:
            display_ml = current_ml_bucket

            if percent >= 100:
                display_ml = target_ml

            ml_text = "{}mL/{}mL".format(display_ml, target_ml)

            if ml_text != self.last_ml_text:
                tft.fill_rect(
                    0,
                    self.layout["ml_y"],
                    self.layout["w"],
                    8 * self.layout["ml_scale"] + 2,
                    BLACK
                )

                tft.draw_center_text_box(
                    self.layout["ml_y"],
                    ml_text,
                    WHITE,
                    BLACK,
                    scale=self.layout["ml_scale"]
                )

                self.last_ml_text = ml_text
                self.last_ml_bucket = current_ml_bucket

    def draw_result(self, tft, result_text, mode_text, current_ml, target_ml):
        tft.fill_screen(BLACK)

        title_color = SKYBLUE

        if result_text == "DISPENSING COMPLETE":
            title_color = GREEN

        elif result_text == "DISPENSING CANCELLED":
            title_color = RED

        tft.draw_center_text_box(
            self.layout["result_title_y"],
            result_text,
            title_color,
            BLACK,
            scale=self.layout["result_title_scale"]
        )

        tft.draw_center_text_box(
            self.layout["result_mode_y"],
            mode_text,
            WHITE,
            BLACK,
            scale=self.layout["result_mode_scale"]
        )

        tft.draw_center_text_box(
            self.layout["result_ml_y"],
            "{}mL/{}mL".format(current_ml, target_ml),
            WHITE,
            BLACK,
            scale=self.layout["result_ml_scale"]
        )

        if result_text == "DISPENSING COMPLETE":
            tft.draw_center_text_box(
                self.layout["result_status_y"],
                "COMPLETE",
                GREEN,
                BLACK,
                scale=self.layout["result_status_scale"]
            )

        elif result_text == "DISPENSING CANCELLED":
            tft.draw_center_text_box(
                self.layout["result_status_y"],
                "CANCELLED",
                RED,
                BLACK,
                scale=self.layout["result_status_scale"]
            )

        self.last_percent = None
        self.last_ml_text = None
        self.last_fill_w = None
        self.last_ui_update_ms = 0
        self.last_ml_bucket = None