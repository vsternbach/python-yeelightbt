import atexit
import json
import os
import redis

from .proxy import ProxyService
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
REDIS_CONTROL_CHANNEL = 'lamp_control'  # config('REDIS_CHANNEL', default='lamp_control')
REDIS_STATE_CHANNEL = 'lamp_state'  # config('REDIS_CHANNEL', default='lamp_state')
REDIS_KEY = 'lamp_state'  # config('REDIS_CHANNEL', default='lamp_state')


# class Daemon:
#     def __init__(self, redis_client):
#         # self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
#         # print("Redis client is running on %s:%s" % (REDIS_HOST, REDIS_PORT))
#         self._message_service = MessageService(redis_client, REDIS_CONTROL_CHANNEL, REDIS_STATE_CHANNEL, REDIS_KEY)
#         # print("Message service is on channel %s" % REDIS_CONTROL_CHANNEL)
#         self._message_service.subscribe(self._message_handler)
#         self._proxy_service = ProxyService(self._message_service)
#         # Register the cleanup method with atexit
#         # atexit.register(self.cleanup)
#
#     def _message_handler(self, message):
#         # Parse the received message as JSON
#         payload = json.loads(message)
#         (uuid, command) = payload
#         if uuid and command:
#             self._proxy_service.cmd(uuid, Command(command['type'], command['payload']))
#             self._message_service.set_state(uuid, command)
#         else:
#             print("Received an invalid message:", payload)
#
#     def cleanup(self):
#         # This method is called when the program exits
#         if self.redis_client is not None:
#             self.redis_client.close()
#             print("Redis connection closed.")

def message_handler(ctx, message):
    # Parse the received message as JSON
    data = json.loads(message)
    uuid = data['uuid']
    command = data['command']
    type = command['type']
    payload = command['payload']
    print('received message from %s: command=%s and payload=%s' % (uuid, type, payload))
    if uuid and command:
        ctx['proxy_service'].cmd(uuid, Command(type, payload))
        ctx['message_service'].set_state(uuid, command)
    else:
        print("Received an invalid message:", payload)

def run():
    ctx = {}
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    message_service = MessageService(redis_client, REDIS_CONTROL_CHANNEL, REDIS_STATE_CHANNEL, REDIS_KEY)
    proxy_service = ProxyService(message_service)
    ctx['message_service'] = message_service
    ctx['proxy_service'] = proxy_service
    message_service.subscribe(lambda message: message_handler(ctx, message))
    atexit.register(redis_client.close())


if __name__ == '__main__':
    run()
