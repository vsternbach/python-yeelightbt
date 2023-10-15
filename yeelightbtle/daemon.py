import atexit
import json
import os
import redis

from .proxy import ProxyService
from .lamp import Lamp
# from decouple import config
from .message import MessageService, CommandType, Command

# Check if the .env file exists
# if os.path.exists('.env'):
#     # If the .env file exists, read configuration variables from it
#     config.read('.env')
# else:
#     # If the .env file doesn't exist, read from environment variables
#     pass  # No need to do anything since config() will use environment variables by default


# Access environment variables
REDIS_HOST = 'localhost'  # config('REDIS_HOST', default='localhost')
REDIS_PORT = 6379  # config('REDIS_PORT', default=6379)
REDIS_CHANNEL = 'lamp_control'  # config('REDIS_CHANNEL', default='lamp_control')


class Daemon:
    def __init__(self):
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        print("Redis client is running on %s:%s" % (REDIS_HOST, REDIS_PORT))
        self._message_service = MessageService(self.redis_client, REDIS_CHANNEL, "lamp_state")
        print("Message service is on channel %s" % REDIS_CHANNEL)
        self._message_service.subscribe(self._message_handler)
        self._proxy_service = ProxyService(self._message_service)
        # Register the cleanup method with atexit
        atexit.register(self.cleanup)

    def _message_handler(self, message):
        # Parse the received message as JSON
        payload = json.loads(message)
        (uuid, command) = payload
        if uuid and command:
            self._proxy_service.cmd(uuid, Command(command['type'], command['payload']))
            self._message_service.set_state(uuid, command)
        else:
            print("Received an invalid message:", payload)

    def cleanup(self):
        # This method is called when the program exits
        if self.redis_client is not None:
            self.redis_client.close()
            print("Redis connection closed.")


def daemon():
    Daemon()


#     redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)
#     message_service = MessageService(redis_client, REDIS_CHANNEL, "lamp_state")
#     proxy_service = ProxyService(message_service)
#     # Subscribe to the channel with the message_handler
#     message_service.subscribe(message_handler)
#     message_service.publish()


if __name__ == '__main__':
    daemon()

    # while True:
    #     command_type = input("Enter a command type (setColor, setBrightness, setStatus, setMode, getState): ")
    #     uuid = input("Enter a UUID for the lamp: ")
    #
    #     if command_type in [CommandType.SetColor, CommandType.SetBrightness, CommandType.SetStatus, CommandType.SetMode,
    #                         CommandType.GetState]:
    #         data = input("Enter command data: ")
    #         command = {"type": command_type, "data": data}
    #
    #         # Publish the formatted command as a JSON message
    #         message = {"uuid": uuid, "command": command}
    #         message_service.publish_message(json.dumps(message))
    #     else:
    #         print("Unsupported command type:", command_type)
