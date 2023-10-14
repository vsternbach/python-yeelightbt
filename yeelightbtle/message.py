import json


class CommandType:
    SetColor = 'setColor'
    SetBrightness = 'setBrightness'
    SetStatus = 'setStatus'
    SetMode = 'setMode'
    GetState = 'getState'


class MessageService:
    def __init__(self, redis_client, channel_name, state_key_prefix):
        self.redis_client = redis_client
        self.channel_name = channel_name
        self.state_key_prefix = state_key_prefix

    def publish_message(self, message):
        self.redis_client.publish(self.channel_name, message)

    def subscribe(self, callback):
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(self.channel_name)
        for message in pubsub.listen():
            if message['type'] == 'message':
                callback(message['data'])

    def set_state(self, uuid, command):
        state_key = f"{self.state_key_prefix}:{uuid}"
        state = self.get_state(uuid) or {}

        if command['type'] == CommandType.SetColor:
            state['color'] = command['payload']
        elif command['type'] == CommandType.SetBrightness:
            state['brightness'] = command['payload']
        elif command['type'] == CommandType.SetStatus:
            state['status'] = command['payload']
        elif command['type'] == CommandType.SetMode:
            state['mode'] = command['payload']
        else:
            print(f"Unsupported command type: {command['type']}")
            return

        self.redis_client.set(state_key, json.dumps(state))

        # Publish a message when the state changes
        message = json.dumps({"uuid": uuid, "state": state})
        self.publish_message(message)

    def get_state(self, uuid):
        state_key = f"{self.state_key_prefix}:{uuid}"
        state_json = self.redis_client.get(state_key)
        if state_json:
            return json.loads(state_json)
        else:
            default_state = {
                "color": "FFFFFF",
                "brightness": 0,
                "status": "off",
                "mode": 0
            }
            return default_state



