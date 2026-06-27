from machine import Pin
import time

from config import (
    FLOW_DEBOUNCE_MS,
    FLOW_EDGE_MODE,
)


class FlowMeter:
    """
    Flow meter input service.

    Purpose:
    - Reads flow sensor pulse input
    - Counts valid pulses while dispensing is enabled
    - Supports FALLING, RISING, or BOTH edge modes
    """

    def __init__(self, pin_no):
        self.pin_no = pin_no
        self.pin = Pin(pin_no, Pin.IN, Pin.PULL_UP)

        self.pulses = 0
        self.last_irq_ms = 0
        self.enabled = False

        self.last_level = self.pin.value()

    def reset(self):
        self.pulses = 0
        self.last_irq_ms = 0
        self.last_level = self.pin.value()

    def _get_irq_trigger(self):
        mode = str(FLOW_EDGE_MODE).upper()

        if mode == "RISING":
            return Pin.IRQ_RISING

        if mode == "FALLING":
            return Pin.IRQ_FALLING

        # Default: BOTH
        return Pin.IRQ_RISING | Pin.IRQ_FALLING

    def enable_irq(self):
        self.last_level = self.pin.value()

        self.pin.irq(
            trigger=self._get_irq_trigger(),
            handler=self.irq_handler
        )

        print("Flow IRQ enabled GPIO", self.pin_no, "mode", FLOW_EDGE_MODE)

    def disable_irq(self):
        try:
            self.pin.irq(handler=None)
        except Exception:
            pass

    def set_enabled(self, value):
        self.enabled = value

        if value:
            self.last_level = self.pin.value()
            self.last_irq_ms = time.ticks_ms()

    def irq_handler(self, pin):
        if not self.enabled:
            return

        now = time.ticks_ms()

        if time.ticks_diff(now, self.last_irq_ms) < FLOW_DEBOUNCE_MS:
            return

        level = pin.value()

        # Extra protection: ignore same-level repeated IRQ noise.
        if level == self.last_level:
            return

        self.last_level = level
        self.last_irq_ms = now
        self.pulses += 1

    def get_level(self):
        return self.pin.value()

    def get_pulses(self):
        return self.pulses