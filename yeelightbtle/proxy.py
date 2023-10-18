import logging
import sys
import time

from .lamp import Lamp
from .message import MessageService, Command, CommandType


class ProxyService:
    _lamps = {}

    def __init__(self, message_service: MessageService):
        logging.info("Proxy service is on")
        self._message_service = message_service

    def cmd(self, uuid, command: Command):
        logging.info(f"Proxy cmd: {command} for {uuid}")
        key = uuid.lower()
        if key not in self._lamps:
            logging.info('New Lamp')
            self._lamps[key] = Lamp(uuid, lambda data: self.status_cb(uuid, data),
                                    lambda data: self.paired_cb(uuid, data), keep_connection=True)
        else:
            logging.info('Existing Lamp')
        lamp = self._lamps[key]
        if command.type == CommandType.SetColor:
            lamp.set_color(command.payload)
        elif command.type == CommandType.SetBrightness:
            lamp.set_brightness(command.payload)
        elif command.type == CommandType.SetOn:
            lamp.set_on_off(command.payload)
        # elif command.type == CommandType.SetMode:
        #     lamp.set_scene(command.payload)
        elif command.type == CommandType.GetState:
            # Publish the current state straight away
            self._message_service.publish_state(uuid)
            # And get a new state from lamp
            lamp.state()
        else:
            logging.warning(f"Unsupported command type: {command.type}")
            return

    def paired_cb(self, uuid, data):
        logging.debug(f'paired_cb for {uuid} with data: {data}')
        data = data.payload
        if data.pairing_status == "PairRequest":
            logging.info("Waiting for pairing, please push the button/change the brightness")
            time.sleep(5)
        elif data.pairing_status == "PairSuccess":
            logging.info("We are paired.")
        elif data.pairing_status == "PairFailed":
            logging.error("Pairing failed, exiting")
            sys.exit(-1)
        logging.info("Got paired to %s: %s" % (uuid, data))

    def status_cb(self, uuid, lamp: Lamp):
        logging.info("Got notification from %s: %s" % (uuid, lamp))
        self._message_service.update_state(uuid, lamp.state_data)
