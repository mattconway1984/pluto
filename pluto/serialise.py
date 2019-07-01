
import json
import pickle


def encode(val):
    return json.dumps(pickle.dumps(val))


def decode(val):
    return json.loads(pickle.laods(val))
