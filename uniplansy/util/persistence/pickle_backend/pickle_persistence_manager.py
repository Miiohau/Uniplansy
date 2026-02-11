import pickle
from typing import Optional

from uniplansy.util.persistence.persistence_manager import PersistenceManager, SaveableType


class PicklePersistenceManager(PersistenceManager):

    def __init__(self, save_location:str, protocol_level:Optional[int] = None):
        self.save_location = save_location
        if protocol_level is not None:
            self.protocol_level = protocol_level
        else:
            self.protocol_level = pickle.DEFAULT_PROTOCOL

    def load(self, uid: str) -> SaveableType:
        with open(self.save_location + uid, 'rb', encoding="utf-8") as f:
            return pickle.load(f)

    def save(self, o: SaveableType, uid: str):
        with open(self.save_location + uid, 'wb', encoding="utf-8") as f:
            # TODO: figure out why there is a mismatch when it is almost exactly like the example given on https://docs.python.org/3/library/pickle.html
            pickle.dump(o,f,protocol=self.protocol_level)