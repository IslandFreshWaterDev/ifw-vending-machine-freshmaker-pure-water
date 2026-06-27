from machine import Pin, SPI
import time
import gc

from config import *

from driver_tft_40_320x480 import TFT40_320x480
from service_coin_slot import CoinSlot
from service_bill_acceptor import BillAcceptor
from service_inhibit_controller import InhibitController
from service_rotary_encoder import RotaryEncoder
from page_admin_menu import AdminMenuPage
from app_station import Station


RUNNING = True


def reset_all_tfts_once():
    rst = Pin(TFT_RST, Pin.OUT, value=1)

    time.sleep_ms(30)
    rst.value(0)
    time.sleep_ms(30)
    rst.value(1)
    time.sleep_ms(150)


def force_relay_off(pin_no, label):
    try:
        print("Relay OFF:", label, "GPIO", pin_no)

        pin = Pin(pin_no, Pin.OUT)

        if RELAY_ACTIVE_LOW:
            pin.value(1)
        else:
            pin.value(0)

        time.sleep_ms(10)

    except Exception as e:
        print("Relay OFF failed:", label, e)


def force_payment_inhibit_off():
    try:
        print("Payment inhibit OFF GPIO", CUSTOMER_PAYMENT_INHIBIT_PIN)

        pin = Pin(CUSTOMER_PAYMENT_INHIBIT_PIN, Pin.OUT)

        if PAYMENT_INHIBIT_ACTIVE_HIGH:
            pin.value(0)
        else:
            pin.value(1)

        time.sleep_ms(10)

    except Exception as e:
        print("Payment inhibit OFF failed:", e)


def force_all_relays_off():
    force_relay_off(CUSTOMER_RELAY_PIN, "CUSTOMER")
    force_relay_off(OPERATOR_RELAY_PIN, "OPERATOR")


def disable_irq(pin_no, label):
    try:
        print("Disable IRQ:", label, "GPIO", pin_no)
        Pin(pin_no, Pin.IN).irq(handler=None)
        time.sleep_ms(5)
    except Exception as e:
        print("Disable IRQ failed:", label, e)


def disable_all_irqs():
    disable_irq(CUSTOMER_COIN_PIN, "CUSTOMER_COIN")
    disable_irq(CUSTOMER_BILL_PIN, "CUSTOMER_BILL")
    disable_irq(CUSTOMER_FLOW_PIN, "CUSTOMER_FLOW")
    disable_irq(OPERATOR_FLOW_PIN, "OPERATOR_FLOW")


def operator_can_open_admin(operator_station):
    if operator_station.dispensing:
        print("Admin blocked: operator is dispensing")
        return False

    if operator_station.page != "welcome":
        print("Admin blocked: operator page is", operator_station.page)
        return False

    return True


def handle_admin_menu_event(event, admin_page, operator_tft, operator_station):
    if event == "LEFT":
        admin_page.move_prev(operator_tft)
        return "ADMIN"

    if event == "RIGHT":
        admin_page.move_next(operator_tft)
        return "ADMIN"

    if event == "LONG_PRESS":
        print("Closing admin menu by LONG_PRESS")
        operator_station.draw_welcome()
        return "WELCOME"

    if event == "PRESS":
        selected = admin_page.selected_item()

        print("Admin selected:", selected)

        if selected == "PAYMENT SETTINGS":
            admin_page.show_notice(operator_tft, "PAYMENT SOON")
            return "ADMIN"

        if selected == "VOLUME SETTINGS":
            admin_page.show_notice(operator_tft, "VOLUME SOON")
            return "ADMIN"

        if selected == "CALIBRATE FLOW":
            admin_page.show_notice(operator_tft, "CALIBRATE SOON")
            return "ADMIN"

    return "ADMIN"


def main():
    global RUNNING

    gc.collect()
    RUNNING = True

    print()
    print("SMART WATER REFILLING MACHINE")
    print("4.0 TFT 320x480 physical, 480x320 landscape")
    print("Hardware SPI uses dummy MISO to prevent ESP32-S3 WDT reset")
    print("Dummy MISO GPIO:", TFT_DUMMY_MISO)
    print("Customer bill acceptor GPIO:", CUSTOMER_BILL_PIN)
    print("Customer payment inhibit GPIO:", CUSTOMER_PAYMENT_INHIBIT_PIN)
    print("Operator rotary CLK:", OPERATOR_ENCODER_CLK_PIN)
    print("Operator rotary DT:", OPERATOR_ENCODER_DT_PIN)
    print("Operator rotary SW:", OPERATOR_ENCODER_SW_PIN)
    print("Operator relay GPIO:", OPERATOR_RELAY_PIN)
    print("SPI baudrate:", SPI_BAUDRATE)
    print()

    print("Step 1: force relays/inhibit OFF")
    force_all_relays_off()
    force_payment_inhibit_off()

    print("Step 2: disable IRQs")
    disable_all_irqs()

    print("Step 3: create SPI with dummy MISO")
    spi = SPI(
        SPI_ID,
        baudrate=SPI_BAUDRATE,
        polarity=0,
        phase=0,
        sck=Pin(TFT_SCK),
        mosi=Pin(TFT_MOSI),
        miso=Pin(TFT_DUMMY_MISO)
    )

    print("Step 4: create TFT control pins")
    customer_cs = Pin(CUSTOMER_TFT_CS, Pin.OUT, value=1)
    operator_cs = Pin(OPERATOR_TFT_CS, Pin.OUT, value=1)

    dc = Pin(TFT_DC, Pin.OUT, value=0)
    rst = Pin(TFT_RST, Pin.OUT, value=1)
    bl = Pin(TFT_BL, Pin.OUT, value=1)

    print("Step 5: reset TFTs")
    reset_all_tfts_once()

    print("Step 6: create TFT objects")
    customer_tft = TFT40_320x480(
        spi=spi,
        cs=customer_cs,
        dc=dc,
        rst=rst,
        bl=bl,
        width=CUSTOMER_W,
        height=CUSTOMER_H,
        name="CUSTOMER_4_0_TFT"
    )

    operator_tft = TFT40_320x480(
        spi=spi,
        cs=operator_cs,
        dc=dc,
        rst=rst,
        bl=bl,
        width=OPERATOR_W,
        height=OPERATOR_H,
        name="OPERATOR_4_0_TFT"
    )

    print("Step 7: initialize customer 4.0 TFT")
    customer_tft.init_display()

    print("Step 8: initialize operator 4.0 TFT")
    operator_tft.init_display()

    print("Step 9: create customer credit sources")
    customer_coin = CoinSlot(
        name="CUSTOMER",
        pin_no=CUSTOMER_COIN_PIN
    )

    customer_bill = BillAcceptor(
        name="CUSTOMER",
        pin_no=CUSTOMER_BILL_PIN
    )

    print("Step 10: create customer payment inhibit controller")
    customer_payment_inhibit = InhibitController(
        pin_no=CUSTOMER_PAYMENT_INHIBIT_PIN,
        name="CUSTOMER_PAYMENT_INHIBIT"
    )

    print("Step 11: create operator rotary encoder")
    operator_encoder = RotaryEncoder(
        clk_pin=OPERATOR_ENCODER_CLK_PIN,
        dt_pin=OPERATOR_ENCODER_DT_PIN,
        sw_pin=OPERATOR_ENCODER_SW_PIN
    )

    admin_page = AdminMenuPage(ADMIN_LAYOUT)

    print("Step 12: create stations")
    customer_station = Station(
        name="CUSTOMER",
        tft=customer_tft,
        layout=CUSTOMER_LAYOUT,
        station_config=CUSTOMER_STATION,
        coin_slot=customer_coin,
        bill_acceptor=customer_bill,
        inhibit_controller=customer_payment_inhibit,
        button_pin=CUSTOMER_BUTTON_PIN,
        relay_pin=CUSTOMER_RELAY_PIN,
        flow_pin=CUSTOMER_FLOW_PIN
    )

    operator_station = Station(
        name="OPERATOR",
        tft=operator_tft,
        layout=OPERATOR_LAYOUT,
        station_config=OPERATOR_STATION,
        coin_slot=None,
        bill_acceptor=None,
        inhibit_controller=None,
        button_pin=OPERATOR_BUTTON_PIN,
        relay_pin=OPERATOR_RELAY_PIN,
        flow_pin=OPERATOR_FLOW_PIN
    )

    print("Step 13: draw customer welcome page")
    customer_station.draw_welcome()

    print("Step 14: draw operator welcome page")
    operator_station.draw_welcome()

    print("Step 15: enable station IRQs")
    customer_station.enable_irqs()
    operator_station.enable_irqs()

    admin_mode = False

    print("System ready.")
    print("Customer coin GPIO:", CUSTOMER_COIN_PIN)
    print("Customer bill GPIO:", CUSTOMER_BILL_PIN)
    print("Customer payment inhibit GPIO:", CUSTOMER_PAYMENT_INHIBIT_PIN)
    print("Customer button GPIO:", CUSTOMER_BUTTON_PIN)
    print("Operator button GPIO:", OPERATOR_BUTTON_PIN)
    print("Operator encoder CLK GPIO:", OPERATOR_ENCODER_CLK_PIN)
    print("Operator encoder DT GPIO:", OPERATOR_ENCODER_DT_PIN)
    print("Operator encoder SW GPIO:", OPERATOR_ENCODER_SW_PIN)
    print("Customer relay GPIO:", CUSTOMER_RELAY_PIN)
    print("Operator relay GPIO:", OPERATOR_RELAY_PIN)
    print("Customer flow GPIO:", CUSTOMER_FLOW_PIN)
    print("Operator flow GPIO:", OPERATOR_FLOW_PIN)
    print("Free memory:", gc.mem_free())
    print()

    try:
        while RUNNING:
            customer_station.update()

            operator_encoder.print_debug_every(1000)
            encoder_event = operator_encoder.update()

            if encoder_event is not None:
                print("MAIN ROTARY EVENT:", encoder_event)

            if admin_mode:
                if encoder_event is not None:
                    result = handle_admin_menu_event(
                        encoder_event,
                        admin_page,
                        operator_tft,
                        operator_station
                    )

                    if result == "WELCOME":
                        admin_mode = False

            else:
                operator_station.update()

                if encoder_event == "LONG_PRESS":
                    print("Long press detected while operator page =", operator_station.page)

                    if operator_can_open_admin(operator_station):
                        print("Opening operator admin menu")
                        admin_mode = True
                        admin_page.draw_static(operator_tft)

            time.sleep_ms(2)

    except KeyboardInterrupt:
        print()
        print("KeyboardInterrupt received.")
        print("Stopping safely...")

    finally:
        RUNNING = False

        try:
            customer_station.emergency_stop()
        except Exception:
            pass

        try:
            operator_station.emergency_stop()
        except Exception:
            pass

        disable_all_irqs()
        force_all_relays_off()
        force_payment_inhibit_off()

        print("All IRQ disabled.")
        print("All relays OFF.")
        print("Payment inhibit OFF.")
        print("Stopped safely.")


try:
    main()

except KeyboardInterrupt:
    RUNNING = False
    disable_all_irqs()
    force_all_relays_off()
    force_payment_inhibit_off()
    print("Stopped by KeyboardInterrupt before main completed.")

except Exception as e:
    RUNNING = False
    disable_all_irqs()
    force_all_relays_off()
    force_payment_inhibit_off()
    print("Fatal error:")
    print(e)
    print("Relays and payment inhibit forced OFF.")