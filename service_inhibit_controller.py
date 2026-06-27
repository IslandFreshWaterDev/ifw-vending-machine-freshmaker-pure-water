from machine import Pin

from config import PAYMENT_INHIBIT_ACTIVE_HIGH


class InhibitController:
    """
    Payment inhibit output service.

    Purpose:
    - Controls one MOSFET module that activates the inhibit lines
      for the customer coin slot and bill acceptor.
    - Used while coin/bill pulses are being computed.
    """

    def __init__(self, pin_no, name="PAYMENT_INHIBIT"):
        self.pin_no = pin_no
        self.name = name
        self.pin = Pin(pin_no, Pin.OUT)
        self.active = False
        self.off()

    def on(self):
        if PAYMENT_INHIBIT_ACTIVE_HIGH:
            self.pin.value(1)
        else:
            self.pin.value(0)

        if not self.active:
            print(self.name, "ON GPIO", self.pin_no)

        self.active = True

    def off(self):
        if PAYMENT_INHIBIT_ACTIVE_HIGH:
            self.pin.value(0)
        else:
            self.pin.value(1)

        if self.active:
            print(self.name, "OFF GPIO", self.pin_no)

        self.active = False

    def set(self, value):
        if value:
            self.on()
        else:
            self.off()

    def is_on(self):
        return self.active