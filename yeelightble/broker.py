import asyncio
import json
import logging
import signal
import websockets

from .lamp import Lamp

logger = logging.getLogger(__name__)


class Command:
    SetColor = 'color'
    SetBrightness = 'brightness'
    SetOn = 'on'
    GetState = 'state'


class Broker:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.ws = None
        self._lamps = {}

    async def start(self):
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        async with websockets.serve(self.handle_message, self.host, self.port):
            await asyncio.Future()

    def stop(self, signum):
        logger.info(f"Received {signum} signal. Cleaning up and exiting gracefully.")
        self.ws = None
        asyncio.get_event_loop().stop()

    async def handle_message(self, websocket):
        self.ws = websocket
        try:
            async for message in websocket:
                try:
                    message_data = json.loads(message)
                    uuid, command = message_data.get('uuid'), message_data.get('command', None)
                    if uuid and command:
                        command, payload = command.get('type'), command.get('payload', None)
                        logger.info("Received message from %s: command=%s and payload=%s" % (uuid, command, payload))
                        self.process_command(uuid, command, payload)
                    else:
                        logger.warning("Received invalid message:", message)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        except websockets.exceptions.ConnectionClosed:
            self.stop(signal.SIGABRT)

    def process_command(self, uuid, command: Command, payload=None):
        logger.debug(f"Received command {command} with payload {payload} for {uuid}")
        key = uuid.lower()
        if key not in self._lamps:
            self._lamps[key] = Lamp(uuid, lambda data: self.status_cb(uuid, data))
        lamp = self._lamps[key]
        if command == Command.SetColor:
            lamp.set_color(payload)
        elif command == Command.SetBrightness:
            lamp.set_brightness(payload)
        elif command == Command.SetOn:
            lamp.set_on_off(payload)
        elif command == Command.GetState:
            lamp.get_state()
        else:
            logger.warning(f"Unsupported command: {command}")
            return

    def status_cb(self, uuid, lamp: Lamp):
        logger.debug("Got notification from %s: %s" % (uuid, lamp))
        self.send_state(uuid, lamp.state)

    async def send_state(self, uuid, state=None):
        logger.debug(f"send_state {state} for {uuid}")
        if self.ws:
            await self.ws.send(json.dumps({"uuid": uuid, "state": state}))
        else:
            logger.warning("No open websocket")

