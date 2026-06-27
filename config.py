# ============================================================
# PIN CONFIG
# ============================================================

TFT_SCK = 12
TFT_MOSI = 11

# Hardware SPI on ESP32-S3 MicroPython may watchdog reset if MISO is omitted.
# This is only a dummy software assignment.
# DO NOT wire this pin to the TFT.
TFT_DUMMY_MISO = 6

TFT_DC = 9
TFT_RST = 8
TFT_BL = 7

CUSTOMER_TFT_CS = 14
OPERATOR_TFT_CS = 10

CUSTOMER_COIN_PIN = 18
CUSTOMER_BILL_PIN = 13

CUSTOMER_BUTTON_PIN = 16
CUSTOMER_RELAY_PIN = 21
CUSTOMER_FLOW_PIN = 17

# Customer payment intake inhibit MOSFET.
# Used to block coin slot + bill acceptor while pulse counting is active.
CUSTOMER_PAYMENT_INHIBIT_PIN = 47

# Operator has NO coin slot and NO bill acceptor now.
OPERATOR_BUTTON_PIN = 4
OPERATOR_RELAY_PIN = 5
OPERATOR_FLOW_PIN = 15


# ============================================================
# OPERATOR ROTARY ENCODER CONFIG
# ============================================================

OPERATOR_ENCODER_CLK_PIN = 38
OPERATOR_ENCODER_DT_PIN = 39
OPERATOR_ENCODER_SW_PIN = 40

ENCODER_ACTIVE_VALUE = 0
ENCODER_DEBOUNCE_MS = 3
ENCODER_BUTTON_DEBOUNCE_MS = 80
ENCODER_LONG_PRESS_MS = 1200


# ============================================================
# RELAY CONFIG
# ============================================================

RELAY_ACTIVE_LOW = False


# ============================================================
# PAYMENT INHIBIT CONFIG
# ============================================================
# Current MOSFET module assumption:
# GPIO HIGH = MOSFET ON = inhibit circuit active = block intake
# GPIO LOW  = MOSFET OFF = intake enabled
#
# If behavior is reversed, set PAYMENT_INHIBIT_ACTIVE_HIGH = False.
# ============================================================

PAYMENT_INHIBIT_ACTIVE_HIGH = True


# ============================================================
# BUTTON CONFIG
# ============================================================

BUTTON_ACTIVE_VALUE = 0
HOLD_CANCEL_MS = 1200


# ============================================================
# UI / SPEED CONFIG
# ============================================================

NOTICE_SCREEN_MS = 1600
RESULT_SCREEN_MS = 1800
BILL_WAIT_BLINK_MS = 400
ADMIN_NOTICE_MS = 900

HEADER_UPDATE_MS = 1000

DISPENSE_UI_UPDATE_MS = 80
DISPENSE_ML_STEP = 5

ENABLE_FLOW_DEBUG = False


# ============================================================
# SPI CONFIG
# ============================================================

SPI_ID = 2

# If TFT glitches, return to 20_000_000.
SPI_BAUDRATE = 30_000_000


# ============================================================
# 4.0 TFT CONFIG
# ============================================================

CUSTOMER_W = 480
CUSTOMER_H = 320

OPERATOR_W = 480
OPERATOR_H = 320

TFT_40_MADCTL_STANDARD = 0x28
TFT_40_PIXFMT = 0x55
TFT_40_INVERT_COLOR = False


# ============================================================
# COIN CONFIG
# ============================================================

PULSE_VALUE_MAP = {
    1: 5,
    2: 5,
    3: 10,
    4: 10,
    5: 20,
}

MIN_LOW_MS = 2
MAX_LOW_MS = 80
MIN_GAP_MS = 2
COIN_END_GAP_MS = 150
MAX_PENDING_COIN_PULSES = 20


# ============================================================
# BILL ACCEPTOR CONFIG
# ============================================================

BILL_PULSE_ACTIVE_LEVEL = 0
BILL_MIN_PULSE_US = 3000
BILL_END_GAP_MS = 900

BILL_MAP = {
    2: 20,
    5: 50,
    10: 100,
    20: 200,
    50: 500,
    100: 1000,
}


# ============================================================
# FLOW CONFIG
# ============================================================

PULSES_PER_LITER = 450

FLOW_EDGE_MODE = "BOTH"
FLOW_DEBOUNCE_MS = 1

DISPENSE_TIMEOUT_MS = 120_000
FLOW_DEBUG_PRINT_MS = 1000


# ============================================================
# COMMON 4.0 TFT 480x320 LANDSCAPE LAYOUT
# ============================================================

COMMON_4IN_LAYOUT = {
    "w": 480,
    "h": 320,

    "datetime_y": 4,
    "datetime_scale": 1,

    "brand_y": 28,
    "brand_scale": 3,

    "credits_label_y": 64,
    "credits_label_scale": 5,

    "credit_y": 106,
    "credit_scale": 8,
    "credit_clear_y": 96,
    "credit_clear_h": 62,

    "action_y": 168,
    "action_scale": 5,
    "action_error_scale": 4,
    "action_clear_y": 158,
    "action_clear_h": 48,

    "box_x": 35,
    "box_y": 226,
    "box_w": 410,
    "box_h": 86,
    "box_border": 4,
    "box_line1_y": 236,
    "box_line1_scale": 5,
    "box_line2_y": 276,
    "box_line2_scale": 4,

    "disp_title_y": 12,
    "disp_title_scale": 5,

    "disp_mode_y": 56,
    "disp_mode_scale": 4,

    "bar_x": 40,
    "bar_y": 122,
    "bar_w": 400,
    "bar_h": 55,
    "bar_border": 4,

    "percent_y": 188,
    "percent_scale": 4,

    "ml_y": 228,
    "ml_scale": 5,

    "cancel_y": 288,
    "cancel_scale": 3,

    "result_title_y": 40,
    "result_title_scale": 4,

    "result_mode_y": 92,
    "result_mode_scale": 4,

    "result_ml_y": 150,
    "result_ml_scale": 5,

    "result_status_y": 225,
    "result_status_scale": 4,
}


# ============================================================
# ADMIN MENU 4.0 TFT 480x320 LANDSCAPE LAYOUT
# ============================================================

ADMIN_LAYOUT = {
    "w": 480,
    "h": 320,

    "header_x": 0,
    "header_y": 0,
    "header_w": 480,
    "header_h": 30,
    "title_y": 8,
    "title_scale": 2,

    "content_x": 0,
    "content_y": 30,
    "content_w": 480,
    "content_h": 238,

    "item_x": 5,
    "item_y": 45,
    "item_w": 470,
    "item_h": 32,
    "item_gap": 4,
    "item_text_x": 16,
    "item_text_y_offset": 8,
    "item_scale": 2,
    "item_border": 3,

    "footer_x": 0,
    "footer_y": 270,
    "footer_w": 480,
    "footer_h": 50,
    "footer_line_h": 2,
    "footer_text_y": 292,
    "footer_scale": 2,
    "footer_col_gap": 10,

    "notice_y": 238,
    "notice_scale": 3,
}


# ============================================================
# CUSTOMER / OPERATOR LAYOUTS
# ============================================================

CUSTOMER_LAYOUT = dict(COMMON_4IN_LAYOUT)
OPERATOR_LAYOUT = dict(COMMON_4IN_LAYOUT)


# ============================================================
# STATION CONFIG
# ============================================================

CUSTOMER_STATION = {
    "name": "CUSTOMER",
    "mode": "SELF-SERVICE",
    "rate": "500mL/P10",
    "price": 10,
    "target_ml": 500,
}

OPERATOR_STATION = {
    "name": "OPERATOR",
    "mode": "PICKUP",
    "rate": "1000mL/P20",
    "price": 20,
    "target_ml": 1000,
}