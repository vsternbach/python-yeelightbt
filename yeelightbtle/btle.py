import logging
import codecs
import time
import click
from bluepy.btle import Scanner, DefaultDelegate, BTLEException, Peripheral, Debugging, BTLEDisconnectError

_LOGGER = logging.getLogger(__name__)


class ScanDelegate(DefaultDelegate):
    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            name = dev.getValueText(9)
            click.echo("%s: %s" % (dev.addr, name))


class BTLEScanner:
    def __init__(self, timeout=5):
        self.timeout = timeout
        self.scanner = Scanner().withDelegate(ScanDelegate())

    def scan(self):
        logging.info("Scanning for %s seconds" % self.timeout)
        try:
            self.scanner.scan(self.timeout, passive=True)
        except BTLEException as ex:
            logging.error("Unable to scan, did you set-up permissions for bluepy-helper correctly? ex: %s" % ex)


class BTLEPeripheral(DefaultDelegate):

    def __init__(self, mac):
        """Initialize the Peripheral."""
        DefaultDelegate.__init__(self)
        self._peripheral = Peripheral().withDelegate(self)
        self._mac = mac
        self._callbacks = {}

    def connect(self):
        _LOGGER.info("Trying to connect to %s", self._mac)
        self._peripheral.connect(self._mac)
        _LOGGER.info("Connected to %s", self._mac)

    def disconnect(self):
        self._peripheral.disconnect()

    def wait(self, sec):
        end = time.time() + sec
        while time.time() < end:
            self._peripheral.waitForNotifications(timeout=0.1)

    def get_services(self):
        return self._peripheral.getServices()

    def get_characteristics(self, uuid=None):
        _LOGGER.info("Requesting characteristics for uuid %s", uuid)
        return self._peripheral.getCharacteristics(uuid=uuid)

    # implements DefaultDelegate handleNotification method
    def handleNotification(self, handle, data):
        """Handle Callback from a Bluetooth (GATT) request."""
        _LOGGER.debug("Got notification from %s: %s", handle, codecs.encode(data, 'hex'))
        if handle in self._callbacks:
            self._callbacks[handle](data)

    @property
    def mac(self):
        return self._mac

    def set_callback(self, handle, function):
        """Set the callback for a Notification handle. It will be called with the parameter data, which is binary."""
        self._callbacks[handle] = function

    def write_characteristic(self, handle, value, timeout=0, with_response=False):
        """Write a GATT Command without callback - not utf-8."""
        _LOGGER.debug("Writing %s to %s", codecs.encode(value, 'hex'), handle)
        self._peripheral.writeCharacteristic(handle, value, withResponse=with_response)
        if timeout:
            self.wait(timeout)
