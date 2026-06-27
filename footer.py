from ui_colors import BLACK, WHITE, CYAN


class Footer:
    """
    Reusable horizontal footer component.

    Rules:
    - Max 3 items only.
    - Items are displayed horizontally.
    - Each item gets equal width like a grid column.
    - Text is centered inside each item cell.
    - Footer has one top divider line.
    """

    def __init__(
        self,
        x,
        y,
        w,
        h,
        line_h=2,
        text_y=None,
        scale=1,
        gap=8,
        line_color=CYAN,
        text_color=WHITE,
        bg_color=BLACK
    ):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.line_h = line_h
        self.text_y = text_y
        self.scale = scale
        self.gap = gap
        self.line_color = line_color
        self.text_color = text_color
        self.bg_color = bg_color

        if self.text_y is None:
            text_h = 7 * self.scale
            self.text_y = self.y + self.line_h + ((self.h - self.line_h - text_h) // 2)

    def draw(self, tft, items):
        if items is None:
            items = []

        # Limit max 3 items
        if len(items) > 3:
            items = items[:3]

        # Clear footer area
        tft.fill_rect(
            self.x,
            self.y,
            self.w,
            self.h,
            self.bg_color
        )

        # Divider line
        tft.fill_rect(
            self.x,
            self.y,
            self.w,
            self.line_h,
            self.line_color
        )

        item_count = len(items)

        if item_count <= 0:
            return

        total_gap = self.gap * (item_count - 1)
        cell_w = (self.w - total_gap) // item_count

        for i, text in enumerate(items):
            cell_x = self.x + (i * (cell_w + self.gap))
            self.draw_centered_item(tft, cell_x, cell_w, text)

    def draw_centered_item(self, tft, cell_x, cell_w, text):
        if text is None:
            text = ""

        text_w = tft.text_width(text, self.scale)
        text_x = cell_x + ((cell_w - text_w) // 2)

        if text_x < cell_x:
            text_x = cell_x

        tft.draw_text_box(
            text_x,
            self.text_y,
            text,
            self.text_color,
            self.bg_color,
            scale=self.scale
        )