import json
import os
import redis
from decouple import config
from .message import MessageService, CommandType

# Check if the .env file exists
if os.path.exists('.env'):
    # If the .env file exists, read configuration variables from it
    config.read('.env')
else:
    # If the .env file doesn't exist, read from environment variables
    pass  # No need to do anything since config() will use environment variables by default


# Access environment variables
REDIS_HOST = config('REDIS_HOST', default='localhost')
REDIS_PORT = config('REDIS_PORT', default=6379)
REDIS_CHANNEL = config('REDIS_CHANNEL', default='lamp_control')


def message_handler(self, message):
    # Parse the received message as JSON
    payload = json.loads(message)

    if payload['command'] and payload['uuid']:
        self.set_state(payload['uuid'], payload['command'])
    else:
        print("Received an invalid message:", payload)


def daemon():
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    message_service = MessageService(redis_client, REDIS_CHANNEL, "lamp_state")
    # Subscribe to the channel with the message_handler
    message_service.subscribe(message_handler)

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
