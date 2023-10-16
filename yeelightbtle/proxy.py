from .lamp import Lamp
from .message import MessageService, Command, CommandType, state


class ProxyService:
    _lamps = {}

    def __init__(self, message_service: MessageService):
        print("Proxy service is on")
        self._message_service = message_service

    def cmd(self, uuid, command: Command):
        key = uuid.replace(":", "").lower()
        if key not in self._lamps:
            print('New Lamp')
            self._lamps[key] = Lamp(uuid, lambda data: self.status_cb(uuid, data),
                                    lambda data: self.paired_cb(uuid, data), keep_connection=True)
        else:
            print('Existing Lamp')
        lamp = self._lamps[key]
        if not lamp.is_connected:
            print('Lamp not connected')
            lamp.connect()
        print('Lamp connected')
        if command.type == CommandType.SetColor:
            lamp.set_color(command.payload)
        elif command.type == CommandType.SetBrightness:
            lamp.set_brightness(command.payload)
        elif command.type == CommandType.SetStatus:
            lamp.turn_on(command.payload)
        elif command.type == CommandType.SetMode:
            lamp.set_scene(command.payload)
        elif command.type == CommandType.GetState:
            # Publish the current state straight away
            self._message_service.publish_state(uuid)
            # And get a new state from lamp
            lamp.state()
        else:
            print(f"Unsupported command type: {command.type}")
            return

    def paired_cb(self, uuid, data):
        print("Got paired to %s: %s" % (uuid, data))

    def status_cb(self, uuid, lamp: Lamp):
        print("Got notification from %s: %s" % (uuid, lamp))
        self._message_service.update_state(uuid, lamp.state_data)
