import json
import logging

logger = logging.getLogger(__name__)

class CommandType:
    SetColor = 'color'
    SetBrightness = 'brightness'
    SetOn = 'on'
    GetState = 'state'


class Command:
    def __init__(self, cmd_type: CommandType, payload=None):
        self.type = cmd_type
        self.payload = payload


class MessageService:
    def __init__(self, redis_client, control_channel, state_channel):
        self.redis_client = redis_client
        self.pubsub = self.redis_client.pubsub()
        self.control_channel = control_channel
        self.state_channel = state_channel

    def publish_state(self, uuid, state=None):
        logger.debug(f'publish_state {state} for {uuid}')
        message = json.dumps({"uuid": uuid, "state": state})
        self.redis_client.publish(self.state_channel, message)

    def subscribe_control(self, callback):
        logger.debug("subscribed callback")
        self.pubsub.subscribe(self.control_channel)
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                callback(json.loads(message['data']))

    def update_state(self, uuid, state):
        logger.debug('new state: %s' % state)
        self.publish_state(uuid, state)
