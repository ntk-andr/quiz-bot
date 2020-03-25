import redis


def save_in_redis(set_key: str, set_value: dict, r: redis):
    for key in set_value:
        value = str(set_value[key])
        r.hset(set_key, key, value)
