from ui_colors import BLACK, WHITE, RED, YELLOW, ORANGE


class WelcomePage:
    def __init__(self, layout, mode_text, rate_text):
        self.layout = layout
        self.mode_text = mode_text
        self.rate_text = rate_text

        self.last_credit = None
        self.last_action = None
        self.last_action_color = None
        self.last_action_scale = None
        self.last_mode = None
        self.last_rate = None

    def set_offer(self, mode_text, rate_text):
        self.mode_text = mode_text
        self.rate_text = rate_text

    def draw_static(self, tft, header, credit, action_text):
        tft.fill_screen(BLACK)

        header.draw(tft)

        tft.draw_center_text(
            self.layout["credits_label_y"],
            "CREDITS",
            WHITE,
            scale=self.layout["credits_label_scale"]
        )

        self.last_credit = None
        self.last_action = None
        self.last_action_color = None
        self.last_action_scale = None
        self.last_mode = None
        self.last_rate = None

        self.update_credit(tft, credit)
        self.update_action(tft, action_text)
        self.update_offer_box(tft, self.mode_text, self.rate_text)

    def update_credit(self, tft, credit):
        if credit == self.last_credit:
            return

        tft.fill_rect(
            0,
            self.layout["credit_clear_y"],
            self.layout["w"],
            self.layout["credit_clear_h"],
            BLACK
        )

        text = "P{:.2f}".format(credit)

        tft.draw_center_text(
            self.layout["credit_y"],
            text,
            RED,
            scale=self.layout["credit_scale"]
        )

        self.last_credit = credit

    def update_action(self, tft, action_text, color=None, scale=None):
        if color is None:
            color = YELLOW

        if scale is None:
            scale = self.layout["action_scale"]

        if action_text == "NOT ENOUGH CREDITS":
            color = RED
            scale = self.layout["action_error_scale"]

        elif action_text in ("NO VOLUME", "NO CAL", "INVALID"):
            color = RED
            scale = self.layout["action_error_scale"]

        if (
            action_text == self.last_action and
            color == self.last_action_color and
            scale == self.last_action_scale
        ):
            return

        tft.fill_rect(
            0,
            self.layout["action_clear_y"],
            self.layout["w"],
            self.layout["action_clear_h"],
            BLACK
        )

        tft.draw_center_text(
            self.layout["action_y"],
            action_text,
            color,
            scale=scale
        )

        self.last_action = action_text
        self.last_action_color = color
        self.last_action_scale = scale

    def update_offer_box(self, tft, mode_text, rate_text):
        if mode_text == self.last_mode and rate_text == self.last_rate:
            return

        x = self.layout["box_x"]
        y = self.layout["box_y"]
        w = self.layout["box_w"]
        h = self.layout["box_h"]

        tft.fill_rect(x, y, w, h, BLACK)

        tft.draw_rect(
            x,
            y,
            w,
            h,
            ORANGE,
            thickness=self.layout["box_border"]
        )

        tft.draw_center_text(
            self.layout["box_line1_y"],
            mode_text,
            WHITE,
            scale=self.layout["box_line1_scale"]
        )

        tft.draw_center_text(
            self.layout["box_line2_y"],
            rate_text,
            WHITE,
            scale=self.layout["box_line2_scale"]
        )

        self.last_mode = mode_text
        self.last_rate = rate_text