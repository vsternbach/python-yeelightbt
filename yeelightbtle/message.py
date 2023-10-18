import json
import logging


class CommandType:
    SetColor = 'color'
    SetBrightness = 'brightness'
    SetOn = 'on'
    GetState = 'state'


class Command:
    def __init__(self, type: CommandType, payload=None):
        self.type = type
        self.payload = payload


class MessageService:
    def __init__(self, redis_client, control_channel, state_channel, state_key_prefix):
        self.redis_client = redis_client
        self.pubsub = self.redis_client.pubsub()
        self.control_channel = control_channel
        self.state_channel = state_channel
        self.state_key_prefix = state_key_prefix
        for key in redis_client.scan_iter():
            logging.debug(f"{key}: {self.redis_client.get(key)}")

    def state_key(self, uuid):
        return f"{self.state_key_prefix}:{uuid}"

    def publish_state(self, uuid, state=None):
        logging.debug(f'message: publish_state {state} for {uuid}')
        # if not state:
        #     state = self.get_state(uuid)
        message = json.dumps({"uuid": uuid, "state": state})
        self.redis_client.publish(self.state_channel, message)

    def subscribe_control(self, callback):
        logging.debug("message: subscribed callback")
        self.pubsub.subscribe(self.control_channel)
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                callback(json.loads(message['data']))

    def update_state(self, uuid, state):
        # logging.debug('message: Previous state: %s' % self.get_state(uuid))
        state_key = self.state_key(uuid)
        logging.debug('message: New state: %s' % state)
        # self.redis_client.set(state_key, json.dumps(state))
        self.publish_state(uuid, state)

    # def get_state(self, uuid):
    #     state_json = self.redis_client.get(self.state_key(uuid))
    #     if state_json:
    #         return json.loads(state_json)
    #     else:
    #         return {}
