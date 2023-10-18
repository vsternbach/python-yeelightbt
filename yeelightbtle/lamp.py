import struct
import codecs
import logging
import time
import threading
from retry import retry
from functools import wraps
from bluepy.btle import BTLEException
from .btle import BTLEPeripheral
from .structures import Request, Response, StateResult


def cmd(command):
    @wraps(command)
    def wrapped(self, *args, **kwargs):
        logging.debug(f"@cmd ${command.__name__} was called")
        res = command(self, *args, **kwargs)
        obj = {"type": res}
        if isinstance(res, tuple):
            obj["type"] = res[0]
            obj["payload"] = res[1]
        logging.debug(f"@cmd ${command.__name__}: ${obj}")
        self.update(Request.build(obj))

    return wrapped


class Lamp:
    CONTROL_HANDLE = 0x1f
    NOTIFY_HANDLE = 0x22
    REGISTER_NOTIFY_HANDLE = 0x16
    MAIN_UUID = "8e2f0cbd-1a66-4b53-ace6-b494e25f87bd"
    NOTIFY_UUID = "8f65073d-9f57-4aaa-afea-397d19d5bbeb"
    CONTROL_UUID = "aa7d3f34-2d4f-41e0-807f-52fbf8cf7443"

    def __init__(self, mac, status_cb=None, paired_cb=None, keep_connection=True):
        logging.debug('lamp: init')
        self._mac = mac
        self._paired_cb = paired_cb
        self._status_cb = status_cb
        self._keep_connection = keep_connection
        self._lock = threading.RLock()
        self._is_on = False
        self._brightness = None
        self._temperature = None
        self._rgb = None
        self._mode = None
        self._dev = BTLEPeripheral(mac)
        self._dev.set_callback(self.NOTIFY_HANDLE, self.notify_cb)

    @retry(BTLEException, tries=3, delay=1)
    def connect(self):
        logging.debug('lamp: connect')
        self._dev.connect()
        self.pair()
        # self._dev.set_callback(self.NOTIFY_HANDLE, self.notify_cb)
        # self._dev.write_characteristic(self.REGISTER_NOTIFY_HANDLE, struct.pack("<BB", 0x01, 0x00))

    def disconnect(self):
        self._dev.disconnect()

    def update(self, data):
        logging.debug('lamp: update')
        tries = 3
        while tries > 0:
            try:
                logging.debug(f'lamp: update tries ${tries}')
                self._dev.write_characteristic(self.CONTROL_HANDLE, data)
                return
            except BTLEException:
                logging.warning("lamp: Lamp is disconnected, reconnecting")
                tries -= 1
                self.connect()

    def wait_for_notifications(self):
        while True:
            self._dev.wait(1)

    @property
    def mac(self):
        return self._mac

    @property
    def mode(self):
        return self._mode

    @property
    def is_on(self):
        return self._is_on

    @property
    def temperature(self):
        return self._temperature

    @property
    def brightness(self):
        return self._brightness

    @property
    def color(self):
        return self._rgb

    @property
    def state_data(self):
        return {
            "color": self.color,
            "ct": self.temperature,
            "brightness": self.brightness,
            "mode": self.mode,
            "is_on": self.is_on,
            "status": "on" if self.is_on else "off"
        }

    @cmd
    def pair(self):
        logging.debug('lamp: pair')
        return "Pair"

    @cmd
    def turn_on(self):
        return "SetOnOff", {"state": True}

    @cmd
    def turn_off(self):
        return "SetOnOff", {"state": False}

    @cmd
    def get_name(self):
        return "GetName"

    @cmd
    def get_scene(self, scene_id):
        return "GetScene", {"id": scene_id}

    @cmd
    def set_scene(self, scene_id, scene_name):
        return "SetScene", {"scene_id": scene_id, "text": scene_name}

    @cmd
    def get_version_info(self):
        return "GetVersion"

    @cmd
    def get_serial_number(self):
        return "GetSerialNumber"

    @cmd
    def set_temperature(self, kelvin: int, brightness: int):
        return "SetTemperature", {"temperature": kelvin, "brightness": brightness}

    @cmd
    def set_brightness(self, brightness: int):
        return "SetBrightness", {"brightness": brightness}

    @cmd
    def set_color(self, red: int, green: int, blue: int, brightness: int):
        return "SetColor", {"red": red, "green": green, "blue": blue, "brightness": brightness}

    @cmd
    def state(self) -> StateResult:
        return "GetState"

    @cmd
    def get_alarm(self, number):
        return "GetAlarm", {"id": number, "wait": 0.5}

    @cmd
    def get_flow(self, number):
        return "GetSimpleFlow", {"id": number, "wait": 0.5}

    @cmd
    def get_sleep(self):
        return "GetSleepTimer"

    @cmd
    def get_time(self):
        return "GetTime"

    @cmd
    def set_time(self, new_time):
        return "SetTime", {"time": new_time}

    @cmd
    def get_nightmode(self):
        return "GetNightMode"

    @cmd
    def get_statistics(self):
        return "GetStatistics"

    @cmd
    def get_wakeup(self):
        return "GetWakeUp"

    def __enter__(self):
        self._lock.acquire()
        if not self._dev and self._keep_connection:
            self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()
        if not self._keep_connection:
            logging.info("not keeping the connection, disconnecting..")
            self._dev.disconnect()
        return

    def __str__(self):
        return "<Lamp %s is_on(%s) mode(%s) rgb(%s) brightness(%s) colortemp(%s)>" % (
            self._mac, self._is_on, self._mode, self._rgb, self._brightness, self._temperature)

    def notify_cb(self, data):
        logging.debug('lamp: notify_cb')
        logging.debug("<< %s", codecs.encode(data, 'hex'))
        res = Response.parse(data)
        logging.debug(f'lamp: notify_cb data: ${res}')
        payload = res.payload
        if res.type == "StateResult":
            self._is_on = payload.state
            self._mode = payload.mode
            self._rgb = (payload.red, payload.green, payload.blue, payload.white)
            self._brightness = payload.brightness
            self._temperature = payload.temperature
            if self._status_cb:
                self._status_cb(self)
        elif res.type == "PairingResult":
            logging.debug("pairing res: %s", res)
            if self._paired_cb:
                self._paired_cb(res)

        else:
            logging.info("Unhandled cb: %s", res)
