import redis


class Notifier:
    def __init__(self):
        import redis
        self._r = redis.Redis(host='redis', port=6379)
        self._p = self._r.pubsub()

    def notify(self, message, action=None):
        self._r.publish('main',
                        json.dumps({
                            'message': message,
                            'action': action
                        }))
