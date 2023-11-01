import asyncio
import json
import logging
import signal
import websockets

from .lamp import Lamp
from .utils import throttle

logger = logging.getLogger(__name__)


class Command:
    SetColor = 'color'
    SetBrightness = 'brightness'
    SetOn = 'on'
    GetState = 'state'


class Server:
    def __init__(self):
        self._lamps = {}
        self.ws = None
        self.server = None

    async def start(self, host: str, port: int):
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        self.server = await websockets.serve(self.handle_message, host, port)
        await self.server.wait_closed()

    def stop(self, signum, frame):
        logger.info(f"Received {signum} signal")
        if self.server:
            self.server.close()

    async def handle_message(self, websocket):
        self.ws = websocket
        try:
            async for message in websocket:
                try:
                    message_data = json.loads(message)
                    logger.debug(f"Received ws message: {message_data}")
                    uuid, command = message_data.get('uuid'), message_data.get('command', None)
                    if uuid and command:
                        command, payload = command.get('type'), command.get('payload', None)
                        self.process_command(uuid, command, payload)
                    else:
                        logger.warning("Received invalid message:", message)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        except websockets.exceptions.ConnectionClosed:
            self.stop(signal.SIGABRT, None)

    @throttle()
    def process_command(self, uuid, command: Command, payload=None):
        logger.debug(f"Process command {command} with payload {payload} for {uuid}")
        uuid = uuid.lower()
        if uuid not in self._lamps:
            self._lamps[uuid] = Lamp(uuid, lambda data: self.send_state(uuid, data))
        lamp = self._lamps[uuid]
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

    def send_state(self, uuid, lamp: Lamp):
        logger.debug("Received notification from %s" % uuid)
        message = json.dumps({"uuid": uuid, "state": lamp.state})
        asyncio.get_event_loop().create_task(self.send_message(message))

    async def send_message(self, message):
        if self.ws:
            logger.debug("Send ws message: %s" % message)
            await self.ws.send(message)
        else:
            logger.warning("No open websocket")

