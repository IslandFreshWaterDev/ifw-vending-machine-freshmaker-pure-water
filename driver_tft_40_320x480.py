import time

from driver_display_base import BaseTFT
from driver_display_base import (
    _SWRESET,
    _SLPOUT,
    _DISPON,
    _MADCTL,
    _PIXFMT,
    _INVOFF,
)

from config import (
    TFT_40_MADCTL_STANDARD,
    TFT_40_PIXFMT,
    TFT_40_INVERT_COLOR,
)


_INVON = 0x21


class TFT40_320x480(BaseTFT):
    """
    4.0 inch TFT driver wrapper.

    Target:
    - 320x480 physical panel
    - 480x320 landscape logical drawing
    - Common ILI9488/ST7796-style command set
    - RGB565 mode

    Both customer and operator TFTs should use this same driver
    so color and rotation behavior are the same.
    """

    def __init__(
        self,
        spi,
        cs,
        dc,
        rst,
        bl=None,
        width=480,
        height=320,
        name="TFT40_320x480"
    ):
        super().__init__(
            spi=spi,
            cs=cs,
            dc=dc,
            rst=rst,
            bl=bl,
            width=width,
            height=height,
            name=name
        )

    def init_display(self):
        self.write_cmd(_SWRESET)
        time.sleep_ms(150)

        self.write_cmd(_SLPOUT)
        time.sleep_ms(150)

        # RGB565
        self.write_cmd_data(_PIXFMT, bytes([TFT_40_PIXFMT]))
        time.sleep_ms(20)

        # Standard landscape orientation copied from the working operator setup.
        self.write_cmd_data(_MADCTL, bytes([TFT_40_MADCTL_STANDARD]))
        time.sleep_ms(20)

        if TFT_40_INVERT_COLOR:
            self.write_cmd(_INVON)
        else:
            self.write_cmd(_INVOFF)

        self.write_cmd(_DISPON)
        time.sleep_ms(100)