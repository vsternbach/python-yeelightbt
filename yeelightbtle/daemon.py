import atexit
import logging
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


def message_handler(proxy_service, message):
    # Parse the received message as JSON
    # data = json.loads(message)
    uuid, command = message.get('uuid'), message.get('command', None)
    if uuid and command:
        type, payload = command.get('type'), command.get('payload', None)
        print('received message from %s: command=%s and payload=%s' % (uuid, type, payload))
        proxy_service.cmd(uuid, Command(type, payload))
    else:
        print("Received an invalid message:", message)


def run():
    # daemon = Daemon()
    # daemon.start()
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    message_service = MessageService(redis_client, REDIS_CONTROL_CHANNEL, REDIS_STATE_CHANNEL, REDIS_KEY)
    proxy_service = ProxyService(message_service)
    message_service.subscribe_control(lambda message: message_handler(proxy_service, message))
    atexit.register(redis_client.close())


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    run()
