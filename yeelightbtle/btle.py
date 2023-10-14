"""
A simple wrapper for bluepy's btle.Connection.
Handles Connection duties (reconnecting etc.) transparently.
A butchered version from python-eq3bt, which was butchered from bluepy_devices
with the following license:

The MIT License (MIT)

Copyright (c) 2016 Markus Peter

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""
import logging
import codecs
import time
import click
from bluepy.btle import Scanner, DefaultDelegate, BTLEException, Peripheral, Debugging

DEFAULT_TIMEOUT = 3

_LOGGER = logging.getLogger(__name__)


def retry(method, retries=3):
    method_name = method.__name__

    def _wrap(self, *args, **kwargs):
        for retry in range(retries):
            try:
                method(self, *args, **kwargs)
                break
            except BTLEException as ex:
                _LOGGER.error("%s failed on %s retry: %s", method_name, retry + 1, ex)
                if retry == retries:
                    raise ex

    return _wrap


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
    """Representation of a BTLE Peripheral."""

    def __init__(self, mac):
        """Initialize the Peripheral."""
        DefaultDelegate.__init__(self)
        self._peripheral = Peripheral().withDelegate(self)
        self._mac = mac
        self._callbacks = {}

    # @retry
    def connect(self):
        _LOGGER.info("Trying to connect to %s", self._mac)
        self._peripheral.connect(self._mac)
        _LOGGER.info("Connected to %s", self._mac)
        # for retry in range(max_retries):
        #     try:
        #         self._peripheral.connect(self._mac)
        #         break
        #     except BTLEException as ex:
        #         _LOGGER.info("Unable to connect to device %s on %s retry: %s", self._mac, retry+1, ex)
        #         if retry == max_retries:
        #             raise

    def disconnect(self):
        if self._peripheral:
            self._peripheral.disconnect()
            self._peripheral = None

    def wait(self, sec):
        end = time.time() + sec
        while time.time() < end:
            self._peripheral.waitForNotifications(timeout=0.1)

    def get_services(self):
        return self._peripheral.getServices()

    def get_characteristics(self, uuid=None):
        if uuid:
            _LOGGER.info("Requesting characteristics for uuid %s", uuid)
            return self._peripheral.getCharacteristics(uuid=uuid)
        return self._peripheral.getCharacteristics()

    # implements DefaultDelegate handleNotification method
    def handleNotification(self, handle, data):
        """Handle Callback from a Bluetooth (GATT) request."""
        _LOGGER.debug("Got notification from %s: %s", handle, codecs.encode(data, 'hex'))
        if handle in self._callbacks:
            self._callbacks[handle](data)

    @property
    def mac(self):
        """Return the MAC address of the connected device."""
        return self._mac

    def set_callback(self, handle, function):
        """Set the callback for a Notification handle. It will be called with the parameter data, which is binary."""
        self._callbacks[handle] = function

    # @retry
    def write_characteristic(self, handle, value, timeout=0, with_response=False):
        """Write a GATT Command without callback - not utf-8."""
        _LOGGER.debug("Writing %s to %s with with_response=%s", codecs.encode(value, 'hex'), handle, with_response)
        res = self._peripheral.writeCharacteristic(handle, value, withResponse=with_response)
        if timeout:
            self.wait(timeout)
        return res
