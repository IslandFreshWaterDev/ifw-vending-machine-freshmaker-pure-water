from machine import Pin
import time
import micropython

from config import (
    BILL_PULSE_ACTIVE_LEVEL,
    BILL_MIN_PULSE_US,
    BILL_END_GAP_MS,
    BILL_MAP,
)

micropython.alloc_emergency_exception_buf(100)


class BillAcceptor:
    """
    Bill acceptor input service.

    Purpose:
    - Reads active-LOW bill acceptor pulse signal
    - Counts bill pulses
    - Waits until no more pulses arrive
    - Converts pulse count to PHP bill value
    - Returns a finished bill event to app_station.py

    Pulse mapping:
    2 pulses   = PHP 20
    5 pulses   = PHP 50
    10 pulses  = PHP 100
    20 pulses  = PHP 200
    50 pulses  = PHP 500
    100 pulses = PHP 1000
    """

    def __init__(self, name, pin_no):
        self.name = name
        self.pin_no = pin_no
        self.pin = Pin(pin_no, Pin.IN, Pin.PULL_UP)

        self.last_level = self.pin.value()
        self.active_start_us = 0

        self.pulse_count = 0
        self.event_active = False
        self.last_pulse_ms = 0

        self.total_amount = 0
        self.unknown_count = 0

    def enable_irq(self):
        self.last_level = self.pin.value()

        self.pin.irq(
            trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
            handler=self.irq_handler
        )

        print("Bill acceptor IRQ enabled GPIO", self.pin_no)

    def disable_irq(self):
        try:
            self.pin.irq(handler=None)
        except Exception:
            pass

    def irq_handler(self, pin):
        now_us = time.ticks_us()
        level = pin.value()

        if level == self.last_level:
            return

        prev = self.last_level
        self.last_level = level

        # Start of active LOW pulse
        if level == BILL_PULSE_ACTIVE_LEVEL and prev != BILL_PULSE_ACTIVE_LEVEL:
            self.active_start_us = now_us
            return

        # End of active LOW pulse
        if prev == BILL_PULSE_ACTIVE_LEVEL and level != BILL_PULSE_ACTIVE_LEVEL:
            width_us = time.ticks_diff(now_us, self.active_start_us)

            if width_us >= BILL_MIN_PULSE_US:
                self.pulse_count += 1
                self.event_active = True
                self.last_pulse_ms = time.ticks_ms()

    def is_waiting(self):
        return self.event_active and self.pulse_count > 0

    def decode_bill(self, pulses):
        return BILL_MAP.get(pulses, None)

    def reset_current_event(self):
        self.pulse_count = 0
        self.event_active = False
        self.last_pulse_ms = 0
        self.active_start_us = 0
        self.last_level = self.pin.value()

    def update(self):
        """
        Call frequently inside main loop.

        Returns:
            None while no bill or still waiting for bill pulses.

            Dict when bill event is finished:
            {
                "name": "CUSTOMER",
                "pulses": 10,
                "value": 100 or None,
                "total": total accepted bill amount,
                "unknown_count": unknown bill counter
            }
        """

        if not self.event_active:
            return None

        if self.pulse_count <= 0:
            return None

        now_ms = time.ticks_ms()

        if time.ticks_diff(now_ms, self.last_pulse_ms) <= BILL_END_GAP_MS:
            return None

        self.disable_irq()

        pulses = self.pulse_count
        amount = self.decode_bill(pulses)

        if amount is None:
            self.unknown_count += 1

            result = {
                "name": self.name,
                "pulses": pulses,
                "value": None,
                "total": self.total_amount,
                "unknown_count": self.unknown_count,
            }
        else:
            self.total_amount += amount

            result = {
                "name": self.name,
                "pulses": pulses,
                "value": amount,
                "total": self.total_amount,
                "unknown_count": self.unknown_count,
            }

        self.reset_current_event()

        time.sleep_ms(20)
        self.enable_irq()

        return result

    def get_level(self):
        return self.pin.value()

    def get_pulses(self):
        return self.pulse_count