from machine import Pin
import time
import micropython

from config import (
    PULSE_VALUE_MAP,
    MIN_LOW_MS,
    MAX_LOW_MS,
    MIN_GAP_MS,
    COIN_END_GAP_MS,
    MAX_PENDING_COIN_PULSES,
)

micropython.alloc_emergency_exception_buf(100)


class CoinSlot:
    """
    Coin slot input service.

    Purpose:
    - Reads active-LOW open-collector coin pulse signal
    - Measures LOW pulse width
    - Counts pulses per coin
    - Converts pulse count to peso value
    - Returns a coin event to the app/station logic
    """

    def __init__(self, name, pin_no):
        self.name = name
        self.pin_no = pin_no
        self.pin = Pin(pin_no, Pin.IN, Pin.PULL_UP)

        self.pulse_count = 0
        self.total_amount = 0

        self.last_level = self.pin.value()
        self.low_start_ms = 0
        self.last_pulse_ms = 0
        self.coin_active = False

    def decode_coin(self, pulses):
        return PULSE_VALUE_MAP.get(pulses, None)

    def is_waiting(self):
        return self.coin_active and self.pulse_count > 0

    def enable_irq(self):
        self.last_level = self.pin.value()
        self.pin.irq(
            trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
            handler=self.irq_handler
        )

    def disable_irq(self):
        try:
            self.pin.irq(handler=None)
        except Exception:
            pass

    def irq_handler(self, pin):
        now = time.ticks_ms()
        level = pin.value()

        if level == self.last_level:
            return

        prev = self.last_level
        self.last_level = level

        # Falling edge: idle HIGH to pulse LOW
        if prev == 1 and level == 0:
            self.low_start_ms = now
            self.coin_active = True
            return

        # Rising edge: pulse LOW back to idle HIGH
        if prev == 0 and level == 1:
            low_duration = time.ticks_diff(now, self.low_start_ms)
            gap = time.ticks_diff(now, self.last_pulse_ms)

            if MIN_LOW_MS <= low_duration <= MAX_LOW_MS:
                if self.last_pulse_ms == 0 or gap >= MIN_GAP_MS:
                    if self.pulse_count < MAX_PENDING_COIN_PULSES:
                        self.pulse_count += 1

                    self.last_pulse_ms = now
                    self.coin_active = True

    def update(self):
        """
        Call this frequently in main loop.

        Returns:
            None if coin is not finished yet.

            Dict if coin is finished:
            {
                "name": "CUSTOMER",
                "pulses": 3,
                "value": 10 or None,
                "total": running total detected by this service
            }
        """

        if not self.coin_active:
            return None

        if self.pulse_count <= 0:
            return None

        now = time.ticks_ms()
        gap = time.ticks_diff(now, self.last_pulse_ms)

        if gap < COIN_END_GAP_MS:
            return None

        self.disable_irq()

        pulses = self.pulse_count
        value = self.decode_coin(pulses)

        if value is not None:
            self.total_amount += value
            result = {
                "name": self.name,
                "pulses": pulses,
                "value": value,
                "total": self.total_amount
            }
        else:
            result = {
                "name": self.name,
                "pulses": pulses,
                "value": None,
                "total": self.total_amount
            }

        self.pulse_count = 0
        self.low_start_ms = 0
        self.last_pulse_ms = 0
        self.coin_active = False
        self.last_level = self.pin.value()

        time.sleep_ms(20)
        self.enable_irq()

        return result