from ui_colors import BLACK, WHITE, CYAN, ORANGE, BLUE

from footer import Footer


class AdminMenuPage:
    """
    Optimized operator admin main menu page.

    Speed improvement:
    - Full redraw only when opening page.
    - Rotation redraws only old selected row and new selected row.
    - Text is drawn using draw_text_box() to reduce SPI transactions.

    Footer:
    - Uses reusable Footer component.
    - Max 3 items.
    - Equal-width horizontal grid.
    - Text centered in each item cell.
    """

    def __init__(self, layout):
        self.layout = layout

        self.items = [
            "PAYMENT SETTINGS",
            "VOLUME SETTINGS",
            "CALIBRATE FLOW",
        ]

        self.footer_items = [
            "ROTATE=SCROLL",
            "PRESS=SELECT",
            "HOLD=EXIT",
        ]

        self.footer = Footer(
            x=self.layout["footer_x"],
            y=self.layout["footer_y"],
            w=self.layout["footer_w"],
            h=self.layout["footer_h"],
            line_h=self.layout["footer_line_h"],
            text_y=self.layout["footer_text_y"],
            scale=self.layout["footer_scale"],
            gap=self.layout["footer_col_gap"],
            line_color=CYAN,
            text_color=WHITE,
            bg_color=BLACK
        )

        self.selected_index = 0
        self.last_selected_index = None
        self.notice_text = None

    def draw_static(self, tft):
        tft.fill_screen(BLACK)

        self.draw_header(tft)
        self.draw_all_items(tft)
        self.draw_footer(tft)

        self.notice_text = None
        self.last_selected_index = self.selected_index

    def draw_header(self, tft):
        tft.fill_rect(
            self.layout["header_x"],
            self.layout["header_y"],
            self.layout["header_w"],
            self.layout["header_h"],
            BLUE
        )

        tft.draw_center_text_box(
            self.layout["title_y"],
            "ADMIN MENU",
            WHITE,
            BLUE,
            scale=self.layout["title_scale"]
        )

    def draw_footer(self, tft):
        self.footer.draw(tft, self.footer_items)

    def get_item_y(self, index):
        return self.layout["item_y"] + (index * (self.layout["item_h"] + self.layout["item_gap"]))

    def clear_item_row(self, tft, index):
        item_y = self.get_item_y(index)

        tft.fill_rect(
            0,
            item_y - 2,
            self.layout["w"],
            self.layout["item_h"] + 4,
            BLACK
        )

    def draw_item_row(self, tft, index):
        item = self.items[index]
        item_y = self.get_item_y(index)

        x = self.layout["item_x"]
        w = self.layout["item_w"]
        h = self.layout["item_h"]
        text_x = self.layout["item_text_x"]
        text_y = item_y + self.layout["item_text_y_offset"]
        scale = self.layout["item_scale"]

        self.clear_item_row(tft, index)

        if index == self.selected_index:
            tft.draw_rect(
                x,
                item_y,
                w,
                h,
                CYAN,
                thickness=self.layout["item_border"]
            )

        tft.draw_text_box(
            text_x,
            text_y,
            item,
            WHITE,
            BLACK,
            scale=scale
        )

    def draw_all_items(self, tft):
        tft.fill_rect(
            0,
            self.layout["content_y"],
            self.layout["w"],
            self.layout["footer_y"] - self.layout["content_y"],
            BLACK
        )

        for i in range(len(self.items)):
            self.draw_item_row(tft, i)

    def redraw_selection_change(self, tft, old_index, new_index):
        if old_index is not None:
            self.draw_item_row(tft, old_index)

        self.draw_item_row(tft, new_index)

        self.last_selected_index = new_index

    def move_next(self, tft):
        old_index = self.selected_index

        self.selected_index += 1

        if self.selected_index >= len(self.items):
            self.selected_index = 0

        self.clear_notice(tft)
        self.redraw_selection_change(tft, old_index, self.selected_index)

    def move_prev(self, tft):
        old_index = self.selected_index

        self.selected_index -= 1

        if self.selected_index < 0:
            self.selected_index = len(self.items) - 1

        self.clear_notice(tft)
        self.redraw_selection_change(tft, old_index, self.selected_index)

    def selected_item(self):
        return self.items[self.selected_index]

    def show_notice(self, tft, text, color=ORANGE):
        self.notice_text = text

        tft.fill_rect(
            0,
            self.layout["notice_y"],
            self.layout["w"],
            8 * self.layout["notice_scale"] + 4,
            BLACK
        )

        tft.draw_center_text_box(
            self.layout["notice_y"],
            text,
            color,
            BLACK,
            scale=self.layout["notice_scale"]
        )

    def clear_notice(self, tft):
        if self.notice_text is None:
            return

        tft.fill_rect(
            0,
            self.layout["notice_y"],
            self.layout["w"],
            8 * self.layout["notice_scale"] + 4,
            BLACK
        )

        self.notice_text = None