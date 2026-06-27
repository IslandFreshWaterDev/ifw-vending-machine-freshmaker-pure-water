def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


BLACK = rgb565(0, 0, 0)
WHITE = rgb565(255, 255, 255)
RED = rgb565(255, 0, 0)
YELLOW = rgb565(255, 255, 0)
GREEN = rgb565(0, 255, 0)

SKYBLUE = rgb565(0, 180, 255)
CYAN = rgb565(0, 180, 255)
DARK_CYAN = rgb565(0, 70, 90)

ORANGE = rgb565(255, 145, 0)
BLUE = rgb565(0, 80, 255)