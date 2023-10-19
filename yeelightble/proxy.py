import logging
from .lamp import Lamp
from .message import MessageService, Command, CommandType

logger = logging.getLogger(__name__)


class ProxyService:
    def __init__(self, message_service: MessageService):
        self._message_service = message_service
        self._lamps = {}

    def cmd(self, uuid, command: Command):
        logger.debug(f'{command} for {uuid}')
        key = uuid.lower()
        if key not in self._lamps:
            self._lamps[key] = Lamp(uuid, lambda data: self.state_cb(uuid, data))
        lamp = self._lamps[key]
        if command.type == CommandType.SetColor:
            lamp.set_color(command.payload)
        elif command.type == CommandType.SetBrightness:
            lamp.set_brightness(command.payload)
        elif command.type == CommandType.SetOn:
            lamp.set_on_off(command.payload)
        elif command.type == CommandType.GetState:
            lamp.state()
        else:
            logger.warning(f"Unsupported command type: {command.type}")
            return

    def state_cb(self, uuid, lamp: Lamp):
        logger.debug("Got notification from %s: %s" % (uuid, lamp))
        self._message_service.update_state(uuid, lamp.state_data)
