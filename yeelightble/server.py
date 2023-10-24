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


class Server:
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

    def stop(self, signum, frame):
        logger.info(f"Received {signum} signal. Cleaning up and exiting gracefully.")
        self.ws = None
        asyncio.get_event_loop().stop()

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

    async def send_state(self, uuid, lamp: Lamp):
        logger.debug("Received notification from %s" % uuid)
        if self.ws:
            logger.debug("Send ws message with state: %s" % (uuid, lamp.state))
            await self.ws.send(json.dumps({"uuid": uuid, "state": lamp.state}))
        else:
            logger.warning("No open websocket")

