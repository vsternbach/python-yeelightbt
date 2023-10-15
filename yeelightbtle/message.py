import json

# from yeelightbtle.daemon import LampService


class CommandType:
    SetColor = 'setColor'
    SetBrightness = 'setBrightness'
    SetStatus = 'setStatus'
    SetMode = 'setMode'
    GetState = 'getState'

class Command:
    def __init__(self, type: CommandType, payload=None):
        self.type = type
        self.payload = payload

class MessageService:
    def __init__(self, redis_client, control_channel, state_channel, state_key_prefix):
        # self.lamp_service = lamp_service
        self.redis_client = redis_client
        self.pubsub = self.redis_client.pubsub()
        self.control_channel = control_channel
        self.state_channel = state_channel
        self.state_key_prefix = state_key_prefix

    def publish(self, message):
        self.redis_client.publish(self.state_channel, message)

    def subscribe(self, callback):
        print("Message service is subscribed")
        self.pubsub.subscribe(self.control_channel)
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                callback(message['data'])

    def set_state(self, uuid, command):
        state_key = f"{self.state_key_prefix}:{uuid}"
        state = self.get_state(uuid)

        if command['type'] == CommandType.SetColor:
            state['color'] = command['payload']
        elif command['type'] == CommandType.SetBrightness:
            state['brightness'] = command['payload']
        elif command['type'] == CommandType.SetStatus:
            state['status'] = command['payload']
        elif command['type'] == CommandType.SetMode:
            state['mode'] = command['payload']
        elif command['type'] == CommandType.GetState:
            pass
        else:
            print(f"Unsupported command type: {command['type']}")
            return

        self.redis_client.set(state_key, json.dumps(state))

        # Publish a message when the state changes
        message = json.dumps({"uuid": uuid, "state": state})
        self.publish(message)

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



