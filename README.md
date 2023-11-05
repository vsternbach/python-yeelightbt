# Python library for Yeelight BLE lamps
This library allows controlling Yeelight bluetooth-enabled [Bedside Lamp](http://www.yeelight.com/en_US/product/yeelight-ctd) and [Candela](https://www.yeelight.com/en_US/product/gingko) devices.

Note: this library is a fork and contains modifications of the original library to allow running it as systemd service daemon that communicates over websockets

It is intended to run on RPI and was tested with Yeelight Candela lights only.

Currently supported features (Candelas support only On/Off and Brightness):
* State
* On/Off
* Color mode (white, color, flow)
* Temperature
* Brightness
* Sleep, wakeup & scheduling (partially)

## Installation
```
sudo pip3 install git+https://github.com/vsternbach/yeelightble
```
Check that it's working correctly by running scan:
```
yeelightble scan -t 1
```
If you're getting an error you need to let the helper have the capabilities for accessing the bluetooth devices without being root by running the following:
```
sudo setcap 'cap_net_raw,cap_net_admin+eip' bluepy-helper
```
if you get: `Failed to set capabilities on file 'bluepy-helper' (No such file or directory)`, provide the full path to `bluepy-helper`, for example on RPI: 
```
sudo setcap 'cap_net_raw,cap_net_admin+eip' /usr/local/lib/python3.7/dist-packages/bluepy/bluepy-helper
```
And then try again if the scanning works.

If you intend to use it with [homebridge-yeelight-ble](https://github.com/vsternbach/homebridge-yeelight-ble) you need to install it as a systemd service daemon, see [below](#service-daemon)

## Service daemon
Running this script will install, enable and run `yeelightble` as a systemd service:
```
curl -sSL https://github.com/vsternbach/yeelightble/raw/master/install-service.sh | sudo sh
```
To see service logs, run:
```
journalctl -u yeelightble -f
```
## CLI
Try
```
$ yeelightble --help
```
and
```
$ yeelightble [command] --help
```
For debugging, you can pass -d/--debug, adding it second time will also print out the debug from bluepy.
### Scan for devices
```
$ yeelightble scan
  f8:24:41:xx:xx:xx yeelight_ms
  f8:24:41:xx:xx:xx XMCTD_XXXX
```

### Reading status & states
To avoid passing ```--mac``` for every call, set the following environment variable:
```
export YEELIGHTBLE_MAC=AA:BB:CC:11:22:33
```
```
$ yeelightble state

MAC: f8:24:41:xx:xx:xx
  Mode: LampMode.White
  Color: (0, 0, 0)
  Temperature: 5000
  Brightness: 50
```

```
$ yeelightble temperature

Temperature: 5000
```

```
$ yeelightble color 255 0 0
Setting color: 255 0 0
```
