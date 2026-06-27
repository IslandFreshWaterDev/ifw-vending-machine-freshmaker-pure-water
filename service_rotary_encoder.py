from machine import Pin
import time

from config import (
    ENCODER_ACTIVE_VALUE,
    ENCODER_DEBOUNCE_MS,
    ENCODER_BUTTON_DEBOUNCE_MS,
    ENCODER_LONG_PRESS_MS,
)


class RotaryEncoder:
    """
    KY-040 rotary encoder service.

    Events returned by update():
    - "LEFT"
    - "RIGHT"
    - "PRESS"
    - "LONG_PRESS"

    SW behavior:
    - Idle = 1
    - Pressed = 0
    - Long press triggers after ENCODER_LONG_PRESS_MS
    """

    def __init__(self, clk_pin, dt_pin, sw_pin):
        self.clk_pin_no = clk_pin
        self.dt_pin_no = dt_pin
        self.sw_pin_no = sw_pin

        self.clk = Pin(clk_pin, Pin.IN, Pin.PULL_UP)
        self.dt = Pin(dt_pin, Pin.IN, Pin.PULL_UP)
        self.sw = Pin(sw_pin, Pin.IN, Pin.PULL_UP)

        # Rotary state
        self.last_clk = self.clk.value()
        self.last_rotate_ms = 0

        # Button state
        self.last_sw = self.sw.value()
        self.sw_down_ms = 0
        self.last_button_event_ms = 0
        self.long_press_sent = False

        # Debug
        self.last_debug_ms = 0

        print("Rotary encoder initialized")
        print("  CLK GPIO:", self.clk_pin_no, "level:", self.clk.value())
        print("  DT  GPIO:", self.dt_pin_no, "level:", self.dt.value())
        print("  SW  GPIO:", self.sw_pin_no, "level:", self.sw.value())
        print("  Expected SW idle=1 pressed=0")

    def get_levels(self):
        return {
            "clk": self.clk.value(),
            "dt": self.dt.value(),
            "sw": self.sw.value(),
        }

    def print_debug_every(self, interval_ms=1000):
        now = time.ticks_ms()

        if self.last_debug_ms == 0:
            self.last_debug_ms = now
            return

        if time.ticks_diff(now, self.last_debug_ms) < interval_ms:
            return

        self.last_debug_ms = now

        print(
            "ROTARY DEBUG clk={} dt={} sw={}".format(
                self.clk.value(),
                self.dt.value(),
                self.sw.value()
            )
        )

    def update_rotation(self):
        now = time.ticks_ms()
        clk_now = self.clk.value()

        if clk_now == self.last_clk:
            return None

        if time.ticks_diff(now, self.last_rotate_ms) < ENCODER_DEBOUNCE_MS:
            self.last_clk = clk_now
            return None

        self.last_rotate_ms = now

        # Process only on CLK falling edge
        if clk_now == 0:
            dt_now = self.dt.value()
            self.last_clk = clk_now

            if dt_now == 1:
                return "RIGHT"
            else:
                return "LEFT"

        self.last_clk = clk_now
        return None

    def update_button(self):
        now = time.ticks_ms()
        sw_now = self.sw.value()

        # ====================================================
        # BUTTON IS PRESSED
        # ====================================================
        if sw_now == ENCODER_ACTIVE_VALUE:
            # New press edge
            if self.last_sw != ENCODER_ACTIVE_VALUE:
                self.sw_down_ms = now
                self.long_press_sent = False
                self.last_sw = sw_now
                print("ROTARY SW DOWN")
                return None

            # If booted while held, start timing here safely
            if self.sw_down_ms == 0:
                self.sw_down_ms = now
                self.long_press_sent = False
                self.last_sw = sw_now
                print("ROTARY SW HOLD START")
                return None

            held_ms = time.ticks_diff(now, self.sw_down_ms)

            if held_ms >= ENCODER_LONG_PRESS_MS and not self.long_press_sent:
                self.long_press_sent = True
                self.last_sw = sw_now
                print("ROTARY EVENT: LONG_PRESS held_ms={}".format(held_ms))
                return "LONG_PRESS"

            self.last_sw = sw_now
            return None

        # ====================================================
        # BUTTON IS RELEASED
        # ====================================================
        if self.last_sw == ENCODER_ACTIVE_VALUE:
            held_ms = time.ticks_diff(now, self.sw_down_ms)

            print("ROTARY SW UP held_ms={}".format(held_ms))

            # Short press only if long press was not already sent
            if (
                not self.long_press_sent and
                held_ms < ENCODER_LONG_PRESS_MS and
                time.ticks_diff(now, self.last_button_event_ms) >= ENCODER_BUTTON_DEBOUNCE_MS
            ):
                self.last_button_event_ms = now
                self.sw_down_ms = 0
                self.long_press_sent = False
                self.last_sw = sw_now

                print("ROTARY EVENT: PRESS")
                return "PRESS"

            self.sw_down_ms = 0
            self.long_press_sent = False

        self.last_sw = sw_now
        return None

    def update(self):
        rotate_event = self.update_rotation()

        if rotate_event is not None:
            print("ROTARY EVENT:", rotate_event)
            return rotate_event

        return self.update_button()