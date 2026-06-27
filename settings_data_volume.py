# settings_data_volume.py
# Persistent CUSTOMER / OPERATOR volume + price + calibration settings.
#
# Storage:
#   /data/settings_volume.txt
#
# Data format:
#   type,amount,milliliter,calibration
#
# Example:
#   CUSTOMER,10,500,240
#   OPERATOR,20,1000,480
#
# Meaning:
#   CUSTOMER = P10 / 500mL / 240 flow pulses
#   OPERATOR = P20 / 1000mL / 480 flow pulses

import os


DATA_DIR = "/data"
FILE_PATH = DATA_DIR + "/settings_volume.txt"
TMP_FILE = DATA_DIR + "/settings_volume.tmp"

STATION_TYPES = ("CUSTOMER", "OPERATOR")
AMOUNT_OPTIONS = (5, 10, 15, 20, 25)

MILLILITER_MIN_VALUE = 0
AMOUNT_DEFAULT = 10
CALIBRATION_MIN_VALUE = 0


DEFAULT_VOLUME_DATA = [
    {
        "type": "CUSTOMER",
        "amount": 10,
        "milliliter": 500,
        "calibration": 240,
    },
    {
        "type": "OPERATOR",
        "amount": 20,
        "milliliter": 1000,
        "calibration": 480,
    },
]


VOLUME_DATA = []


# ============================================================
# FILE HELPERS
# ============================================================

def _ensure_data_dir():
    try:
        os.stat(DATA_DIR)
    except OSError:
        try:
            os.mkdir(DATA_DIR)
            print("Created data directory:", DATA_DIR)
        except OSError as e:
            print("Failed to create data directory:", e)


def _copy_default_data():
    result = []

    for item in DEFAULT_VOLUME_DATA:
        result.append({
            "type": _normalize_type(item["type"]),
            "amount": _validate_amount(item["amount"]),
            "milliliter": _validate_milliliter(item["milliliter"]),
            "calibration": _validate_calibration(item["calibration"]),
        })

    return result


def _normalize_type(station_type):
    station_type = str(station_type).strip().upper()

    if station_type not in STATION_TYPES:
        return "CUSTOMER"

    return station_type


def _validate_amount(amount):
    try:
        amount = int(amount)
    except Exception:
        amount = AMOUNT_DEFAULT

    if amount not in AMOUNT_OPTIONS:
        # nearest safe fallback
        if amount <= 5:
            return 5
        if amount <= 10:
            return 10
        if amount <= 15:
            return 15
        if amount <= 20:
            return 20
        return 25

    return amount


def _validate_milliliter(milliliter):
    try:
        milliliter = int(milliliter)
    except Exception:
        milliliter = MILLILITER_MIN_VALUE

    if milliliter < MILLILITER_MIN_VALUE:
        milliliter = MILLILITER_MIN_VALUE

    return milliliter


def _validate_calibration(calibration):
    try:
        calibration = int(calibration)
    except Exception:
        calibration = CALIBRATION_MIN_VALUE

    if calibration < CALIBRATION_MIN_VALUE:
        calibration = CALIBRATION_MIN_VALUE

    return calibration


def _default_item_for_type(station_type):
    station_type = _normalize_type(station_type)

    for item in DEFAULT_VOLUME_DATA:
        if _normalize_type(item["type"]) == station_type:
            return {
                "type": station_type,
                "amount": _validate_amount(item["amount"]),
                "milliliter": _validate_milliliter(item["milliliter"]),
                "calibration": _validate_calibration(item["calibration"]),
            }

    return {
        "type": station_type,
        "amount": 10,
        "milliliter": 0,
        "calibration": 0,
    }


def _line_to_item(line):
    line = line.strip()

    if line == "":
        return None

    parts = line.split(",")

    if len(parts) < 4:
        return None

    station_type = _normalize_type(parts[0])

    # Data format:
    # type,amount,milliliter,calibration
    amount = _validate_amount(parts[1])
    milliliter = _validate_milliliter(parts[2])
    calibration = _validate_calibration(parts[3])

    return {
        "type": station_type,
        "amount": amount,
        "milliliter": milliliter,
        "calibration": calibration,
    }


def _item_to_line(item):
    return "{},{},{},{}\n".format(
        _normalize_type(item["type"]),
        _validate_amount(item["amount"]),
        _validate_milliliter(item["milliliter"]),
        _validate_calibration(item["calibration"]),
    )


def _find_index(station_type):
    station_type = _normalize_type(station_type)

    for i, item in enumerate(VOLUME_DATA):
        if _normalize_type(item["type"]) == station_type:
            return i

    return -1


def ensure_all_station_types_exist():
    for station_type in STATION_TYPES:
        if _find_index(station_type) < 0:
            VOLUME_DATA.append(_default_item_for_type(station_type))


# ============================================================
# LOAD / SAVE
# ============================================================

def load_data():
    global VOLUME_DATA

    _ensure_data_dir()

    loaded = []

    try:
        with open(FILE_PATH, "r") as f:
            for line in f:
                item = _line_to_item(line)

                if item is not None:
                    loaded.append(item)

    except OSError:
        print("Volume settings file missing. Creating defaults.")
        VOLUME_DATA = _copy_default_data()
        save_data()
        return

    if len(loaded) <= 0:
        print("Volume settings file empty. Using defaults.")
        VOLUME_DATA = _copy_default_data()
        save_data()
        return

    VOLUME_DATA = loaded
    ensure_all_station_types_exist()

    print("Loaded volume settings rows:", len(VOLUME_DATA))


def save_data():
    _ensure_data_dir()

    try:
        with open(TMP_FILE, "w") as f:
            for item in VOLUME_DATA:
                f.write(_item_to_line(item))

        try:
            os.remove(FILE_PATH)
        except OSError:
            pass

        os.rename(TMP_FILE, FILE_PATH)

        print("Saved volume settings rows:", len(VOLUME_DATA))
        return True

    except Exception as e:
        print("Failed saving volume settings:", e)

        try:
            os.remove(TMP_FILE)
        except OSError:
            pass

        return False


def reload_data():
    load_data()


def reset_to_defaults():
    global VOLUME_DATA

    VOLUME_DATA = _copy_default_data()
    return save_data()


# ============================================================
# PUBLIC HELPERS
# ============================================================

def get_all():
    return VOLUME_DATA


def get_station_settings(station_type):
    station_type = _normalize_type(station_type)

    index = _find_index(station_type)

    if index >= 0:
        item = VOLUME_DATA[index]

        return {
            "type": station_type,
            "amount": _validate_amount(item["amount"]),
            "milliliter": _validate_milliliter(item["milliliter"]),
            "calibration": _validate_calibration(item["calibration"]),
        }

    return _default_item_for_type(station_type)


def get_rate_text(station_type):
    item = get_station_settings(station_type)

    return "{}mL/P{}".format(
        int(item["milliliter"]),
        int(item["amount"])
    )


def update_station_settings(station_type, amount, milliliter):
    """
    Used later by admin volume settings page.
    Updates price and volume only.
    Calibration is preserved.
    """
    station_type = _normalize_type(station_type)
    amount = _validate_amount(amount)
    milliliter = _validate_milliliter(milliliter)

    index = _find_index(station_type)

    if index < 0:
        default_item = _default_item_for_type(station_type)

        VOLUME_DATA.append({
            "type": station_type,
            "amount": amount,
            "milliliter": milliliter,
            "calibration": default_item["calibration"],
        })
    else:
        VOLUME_DATA[index]["amount"] = amount
        VOLUME_DATA[index]["milliliter"] = milliliter

        if "calibration" not in VOLUME_DATA[index]:
            VOLUME_DATA[index]["calibration"] = 0

    return save_data()


def update_calibration(station_type, calibration):
    """
    Used later after calibration process.
    """
    station_type = _normalize_type(station_type)
    calibration = _validate_calibration(calibration)

    index = _find_index(station_type)

    if index < 0:
        default_item = _default_item_for_type(station_type)

        VOLUME_DATA.append({
            "type": station_type,
            "amount": default_item["amount"],
            "milliliter": default_item["milliliter"],
            "calibration": calibration,
        })
    else:
        VOLUME_DATA[index]["calibration"] = calibration

    return save_data()


def debug_print():
    print()
    print("Volume settings:")
    for item in VOLUME_DATA:
        print(
            item["type"],
            "amount:", item["amount"],
            "mL:", item["milliliter"],
            "calibration:", item["calibration"]
        )
    print()


load_data()