from .lamp import Lamp
from .message import MessageService, Command, CommandType


class ProxyService:
    _lamps = {}

    def __init__(self, message_service: MessageService):
        print("Proxy service is on")
        self._message_service = message_service

    def cmd(self, uuid, command: Command):
        key = uuid.replace(":", "").lower()
        if key not in self._lamps:
            self._lamps[key] = Lamp(uuid, lambda data: self.status_cb(uuid, data), lambda data: self.paired_cb(uuid, data), keep_connection=True)
        lamp = self._lamps[key]
        if not lamp.is_connected:
            lamp.connect()
        if command.type == CommandType.SetColor:
            lamp.set_color(command.payload)
        elif command.type == CommandType.SetBrightness:
            lamp.set_brightness(command.payload)
        elif command.type == CommandType.SetStatus:
            lamp.turn_on(command.payload)
        elif command.type == CommandType.SetMode:
            lamp.set_scene(command.payload)
        elif command.type == CommandType.GetState:
            lamp.state()
        else:
            print(f"Unsupported command type: {command.type}")
            return
        # lamp.connect()
        # lamp.state()

    def paired_cb(self, uuid, data):
        print("Got paired to %s: %s" % uuid, data)

    def status_cb(self, uuid, data):
        print("Got notification from %s: %s" % uuid, data)
