from machine import Pin
import time

from config import (
    RELAY_ACTIVE_LOW,
    PULSES_PER_LITER,
    DISPENSE_TIMEOUT_MS,
    BUTTON_ACTIVE_VALUE,
    HOLD_CANCEL_MS,
    FLOW_DEBUG_PRINT_MS,
    NOTICE_SCREEN_MS,
    RESULT_SCREEN_MS,
    BILL_WAIT_BLINK_MS,
    ENABLE_FLOW_DEBUG,
)

from ui_colors import RED, YELLOW

from header import Header
from page_welcome import WelcomePage
from page_dispensing import DispensingPage
from service_flow_meter import FlowMeter

import settings_data_volume


class Station:
    """
    Station-level app state machine.

    Customer credit sources:
    - Coin slot
    - Bill acceptor

    Customer inhibit:
    - Optional inhibit_controller turns ON while coin/bill pulse counting is active.
    """

    def __init__(
        self,
        name,
        tft,
        layout,
        station_config,
        coin_slot,
        bill_acceptor,
        inhibit_controller,
        button_pin,
        relay_pin,
        flow_pin
    ):
        self.name = name
        self.tft = tft
        self.layout = layout
        self.config = station_config
        self.coin_slot = coin_slot
        self.bill_acceptor = bill_acceptor
        self.inhibit_controller = inhibit_controller

        self.button = Pin(button_pin, Pin.IN, Pin.PULL_UP)
        self.relay = Pin(relay_pin, Pin.OUT)

        self.flow = FlowMeter(flow_pin)

        self.credit = 0

        self.last_button = 1
        self.button_hold_start_ms = 0
        self.cancel_already_triggered = False

        self.page = "welcome"
        self.dispensing = False
        self.dispense_start_ms = 0
        self.last_flow_debug_ms = 0

        self.notice_text = None
        self.notice_color = RED
        self.notice_scale = None
        self.notice_until_ms = 0

        self.wait_visible = False
        self.wait_last_blink_ms = 0

        self.mode_text = self.config["mode"]

        self.price = 0
        self.target_ml = 0
        self.target_pulses = 0
        self.rate_text = ""

        self.load_volume_settings()

        self.header = Header(layout)

        self.welcome_page = WelcomePage(
            layout,
            self.mode_text,
            self.rate_text
        )

        self.dispensing_page = DispensingPage(
            layout,
            self.mode_text
        )

        self.relay_off()
        self.payment_inhibit_off()

    # ========================================================
    # SETTINGS
    # ========================================================

    def load_volume_settings(self):
        item = settings_data_volume.get_station_settings(self.name)

        self.price = int(item["amount"])
        self.target_ml = int(item["milliliter"])
        self.target_pulses = int(item["calibration"])

        if self.target_pulses <= 0 and self.target_ml > 0:
            self.target_pulses = int((self.target_ml / 1000) * PULSES_PER_LITER)

        self.rate_text = settings_data_volume.get_rate_text(self.name)

        print("[{}] Loaded volume settings price={} target_ml={} calibration={}".format(
            self.name,
            self.price,
            self.target_ml,
            self.target_pulses
        ))

    def reload_volume_settings(self):
        settings_data_volume.reload_data()
        self.load_volume_settings()

        self.welcome_page.set_offer(self.mode_text, self.rate_text)
        self.dispensing_page.set_mode(self.mode_text)

        if self.page == "welcome":
            self.welcome_page.update_offer_box(
                self.tft,
                self.mode_text,
                self.rate_text
            )

            self.welcome_page.update_action(
                self.tft,
                self.current_action()
            )

    # ========================================================
    # IRQ / RELAY / INHIBIT
    # ========================================================

    def enable_irqs(self):
        if self.coin_slot is not None:
            self.coin_slot.enable_irq()

        if self.bill_acceptor is not None:
            self.bill_acceptor.enable_irq()

        self.flow.enable_irq()

    def disable_irqs(self):
        if self.coin_slot is not None:
            self.coin_slot.disable_irq()

        if self.bill_acceptor is not None:
            self.bill_acceptor.disable_irq()

        self.flow.disable_irq()

    def relay_on(self):
        if RELAY_ACTIVE_LOW:
            self.relay.value(0)
        else:
            self.relay.value(1)

    def relay_off(self):
        if RELAY_ACTIVE_LOW:
            self.relay.value(1)
        else:
            self.relay.value(0)

    def payment_inhibit_on(self):
        if self.inhibit_controller is not None:
            self.inhibit_controller.on()

    def payment_inhibit_off(self):
        if self.inhibit_controller is not None:
            self.inhibit_controller.off()

    def update_payment_inhibit(self):
        # Only customer station has inhibit_controller.
        if self.inhibit_controller is None:
            return

        if self.payment_waiting():
            self.payment_inhibit_on()
        else:
            self.payment_inhibit_off()

    # ========================================================
    # CREDIT
    # ========================================================

    def add_credit(self, amount, source="MANUAL"):
        try:
            amount = int(amount)
        except Exception:
            return

        if amount <= 0:
            return

        self.clear_notice()
        self.credit += amount

        print("[{}] Credit added PHP {} via {} | Credit PHP {}".format(
            self.name,
            amount,
            source,
            self.credit
        ))

        if self.page == "welcome":
            self.welcome_page.update_credit(self.tft, self.credit)
            self.welcome_page.update_action(self.tft, self.current_action())

    def current_action(self):
        if self.credit >= self.price:
            return "PRESS TO START"

        return "INSERT COIN"

    # ========================================================
    # PAYMENT WAIT / BLINK
    # ========================================================

    def coin_waiting(self):
        if self.coin_slot is None:
            return False

        return self.coin_slot.is_waiting()

    def bill_waiting(self):
        if self.bill_acceptor is None:
            return False

        return self.bill_acceptor.is_waiting()

    def payment_waiting(self):
        return self.coin_waiting() or self.bill_waiting()

    def update_payment_wait_blink(self):
        if self.page != "welcome":
            return

        now = time.ticks_ms()

        if self.wait_last_blink_ms == 0:
            self.wait_last_blink_ms = now
            self.wait_visible = True

            self.welcome_page.update_action(
                self.tft,
                "PLEASE WAIT",
                color=YELLOW,
                scale=self.layout["action_scale"]
            )
            return

        if time.ticks_diff(now, self.wait_last_blink_ms) < BILL_WAIT_BLINK_MS:
            return

        self.wait_last_blink_ms = now
        self.wait_visible = not self.wait_visible

        if self.wait_visible:
            self.welcome_page.update_action(
                self.tft,
                "PLEASE WAIT",
                color=YELLOW,
                scale=self.layout["action_scale"]
            )
        else:
            self.welcome_page.update_action(
                self.tft,
                "",
                color=YELLOW,
                scale=self.layout["action_scale"]
            )

    def clear_payment_wait_blink(self):
        self.wait_visible = False
        self.wait_last_blink_ms = 0

    # ========================================================
    # TEMPORARY WELCOME NOTICE
    # ========================================================

    def set_notice(self, text, color=RED, duration_ms=NOTICE_SCREEN_MS):
        self.notice_text = text
        self.notice_color = color
        self.notice_scale = self.layout["action_error_scale"]
        self.notice_until_ms = time.ticks_add(time.ticks_ms(), duration_ms)

        if self.page == "welcome":
            self.welcome_page.update_action(
                self.tft,
                self.notice_text,
                color=self.notice_color,
                scale=self.notice_scale
            )

    def clear_notice(self):
        self.notice_text = None
        self.notice_until_ms = 0

    def notice_active(self):
        if self.notice_text is None:
            return False

        return time.ticks_diff(self.notice_until_ms, time.ticks_ms()) > 0

    # ========================================================
    # PAGE DRAWING
    # ========================================================

    def draw_welcome(self):
        self.page = "welcome"

        self.load_volume_settings()

        self.welcome_page.set_offer(
            self.mode_text,
            self.rate_text
        )

        self.clear_notice()
        self.clear_payment_wait_blink()
        self.update_payment_inhibit()

        self.welcome_page.draw_static(
            self.tft,
            self.header,
            self.credit,
            self.current_action()
        )

    def update_welcome_dynamic(self):
        if self.page != "welcome":
            return

        self.header.update_datetime(self.tft)
        self.welcome_page.update_credit(self.tft, self.credit)

        if self.payment_waiting():
            self.update_payment_wait_blink()
            return

        if self.wait_last_blink_ms != 0:
            self.clear_payment_wait_blink()
            self.welcome_page.update_action(
                self.tft,
                self.current_action(),
                color=YELLOW,
                scale=self.layout["action_scale"]
            )

        if self.notice_active():
            self.welcome_page.update_action(
                self.tft,
                self.notice_text,
                color=self.notice_color,
                scale=self.notice_scale
            )
            return

        if self.notice_text is not None:
            self.clear_notice()

        self.welcome_page.update_action(
            self.tft,
            self.current_action(),
            color=YELLOW,
            scale=self.layout["action_scale"]
        )

    # ========================================================
    # COIN
    # ========================================================

    def process_coin(self):
        if self.coin_slot is None:
            return

        result = self.coin_slot.update()

        if result is None:
            return

        self.clear_payment_wait_blink()

        value = result["value"]

        if value is None:
            if self.page == "welcome":
                self.set_notice("INVALID", RED)

            print("[{}] Invalid coin pulses={}".format(
                self.name,
                result["pulses"]
            ))
            return

        self.clear_notice()
        self.credit += value

        print("[{}] Coin PHP {} | Credit PHP {}".format(
            self.name,
            value,
            self.credit
        ))

        if self.page == "welcome":
            self.welcome_page.update_credit(self.tft, self.credit)
            self.welcome_page.update_action(self.tft, self.current_action())

    # ========================================================
    # BILL ACCEPTOR
    # ========================================================

    def process_bill_acceptor(self):
        if self.bill_acceptor is None:
            return

        result = self.bill_acceptor.update()

        if result is None:
            return

        self.clear_payment_wait_blink()

        value = result["value"]

        if value is None:
            if self.page == "welcome":
                self.set_notice("INVALID", RED)

            print("[{}] Unknown bill pulses={}".format(
                self.name,
                result["pulses"]
            ))
            return

        self.clear_notice()
        self.credit += value

        print("[{}] Bill PHP {} | Credit PHP {} | pulses={}".format(
            self.name,
            value,
            self.credit,
            result["pulses"]
        ))

        if self.page == "welcome":
            self.welcome_page.update_credit(self.tft, self.credit)
            self.welcome_page.update_action(self.tft, self.current_action())

    # ========================================================
    # BUTTON
    # ========================================================

    def check_button(self):
        current = self.button.value()

        if self.dispensing:
            self.check_hold_to_cancel(current)
            self.last_button = current
            return

        # Block start button while coin/bill acceptor is still computing pulses.
        if self.payment_waiting():
            self.update_payment_wait_blink()
            self.last_button = current
            return

        if self.last_button != BUTTON_ACTIVE_VALUE and current == BUTTON_ACTIVE_VALUE:
            self.handle_button_press()

        self.last_button = current

    def check_hold_to_cancel(self, current):
        now = time.ticks_ms()

        if current == BUTTON_ACTIVE_VALUE:
            if self.button_hold_start_ms == 0:
                self.button_hold_start_ms = now
                self.cancel_already_triggered = False

            held_ms = time.ticks_diff(now, self.button_hold_start_ms)

            if held_ms >= HOLD_CANCEL_MS and not self.cancel_already_triggered:
                self.cancel_already_triggered = True

                print("[{}] HOLD CANCEL triggered after {} ms".format(
                    self.name,
                    held_ms
                ))

                self.cancel_dispensing()
                return

        else:
            self.button_hold_start_ms = 0
            self.cancel_already_triggered = False

    def handle_button_press(self):
        if self.dispensing:
            return

        if self.payment_waiting():
            return

        self.load_volume_settings()

        if self.credit < self.price:
            if self.page == "welcome":
                self.set_notice("NOT ENOUGH CREDITS", RED)

            return

        if self.target_ml <= 0:
            if self.page == "welcome":
                self.set_notice("NO VOLUME", RED)

            print("[{}] Cannot dispense. target_ml is 0.".format(self.name))
            return

        if self.target_pulses <= 0:
            if self.page == "welcome":
                self.set_notice("NO CAL", RED)

            print("[{}] Cannot dispense. calibration is 0.".format(self.name))
            return

        self.start_dispensing()

    # ========================================================
    # DISPENSING
    # ========================================================

    def start_dispensing(self):
        self.clear_notice()
        self.clear_payment_wait_blink()
        self.payment_inhibit_off()

        self.credit -= self.price

        self.flow.reset()
        self.flow.set_enabled(True)

        self.button_hold_start_ms = 0
        self.cancel_already_triggered = False

        self.dispensing = True
        self.page = "dispensing"
        self.dispense_start_ms = time.ticks_ms()
        self.last_flow_debug_ms = 0

        self.dispensing_page.set_mode(self.mode_text)
        self.dispensing_page.draw_static(self.tft)

        self.dispensing_page.update_progress(
            self.tft,
            0,
            0,
            self.target_ml,
            force=True
        )

        self.relay_on()

        print("[{}] DISPENSE START price={} target_ml={} target_pulses={}".format(
            self.name,
            self.price,
            self.target_ml,
            self.target_pulses
        ))

    def cancel_dispensing(self):
        if not self.dispensing:
            return

        self.stop_dispensing("CANCELLED")

    def calc_progress(self):
        current_pulses = self.flow.get_pulses()

        if self.target_pulses <= 0:
            percent = 0
            current_ml = 0
        else:
            percent = int((current_pulses * 100) / self.target_pulses)
            current_ml = int((current_pulses * self.target_ml) / self.target_pulses)

        if percent > 100:
            percent = 100

        if current_ml > self.target_ml:
            current_ml = self.target_ml

        return current_pulses, percent, current_ml

    def print_flow_debug(self, percent, current_ml):
        if not ENABLE_FLOW_DEBUG:
            return

        now = time.ticks_ms()

        if self.last_flow_debug_ms == 0:
            self.last_flow_debug_ms = now

        if time.ticks_diff(now, self.last_flow_debug_ms) < FLOW_DEBUG_PRINT_MS:
            return

        self.last_flow_debug_ms = now

        print("[{}] FLOW DEBUG pulses={} level={} ml={}/{} percent={}% target_pulses={}".format(
            self.name,
            self.flow.get_pulses(),
            self.flow.get_level(),
            current_ml,
            self.target_ml,
            percent,
            self.target_pulses
        ))

    def update_dispensing(self):
        if not self.dispensing:
            return

        elapsed = time.ticks_diff(
            time.ticks_ms(),
            self.dispense_start_ms
        )

        current_pulses, percent, current_ml = self.calc_progress()

        self.dispensing_page.update_progress(
            self.tft,
            percent,
            current_ml,
            self.target_ml
        )

        self.print_flow_debug(percent, current_ml)

        if current_pulses >= self.target_pulses:
            self.dispensing_page.update_progress(
                self.tft,
                100,
                self.target_ml,
                self.target_ml,
                force=True
            )
            self.stop_dispensing("DONE")
            return

        if elapsed >= DISPENSE_TIMEOUT_MS:
            self.stop_dispensing("TIMEOUT")
            return

    def stop_dispensing(self, reason):
        current_pulses, percent, current_ml = self.calc_progress()

        self.relay_off()
        self.flow.set_enabled(False)
        self.dispensing = False
        self.payment_inhibit_off()

        self.button_hold_start_ms = 0
        self.cancel_already_triggered = False

        print("[{}] DISPENSE STOP reason={} pulses={}".format(
            self.name,
            reason,
            self.flow.get_pulses()
        ))

        if reason == "DONE":
            result_text = "DISPENSING COMPLETE"
            current_ml = self.target_ml
        else:
            result_text = "DISPENSING CANCELLED"

        self.page = "result"

        self.dispensing_page.draw_result(
            self.tft,
            result_text,
            self.mode_text,
            current_ml,
            self.target_ml
        )

        time.sleep_ms(RESULT_SCREEN_MS)
        self.draw_welcome()

    # ========================================================
    # MAIN UPDATE
    # ========================================================

    def update(self):
        self.process_coin()
        self.process_bill_acceptor()
        self.update_payment_inhibit()
        self.check_button()
        self.update_dispensing()
        self.update_welcome_dynamic()

    def emergency_stop(self):
        self.disable_irqs()
        self.flow.set_enabled(False)
        self.relay_off()
        self.payment_inhibit_off()