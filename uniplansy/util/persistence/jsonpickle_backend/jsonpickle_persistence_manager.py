from typing import Optional

import jsonpickle

from uniplansy.util.persistence.persistence_manager import PersistenceManager, SaveableType


class JsonPicklePersistenceManager(PersistenceManager):

    def __init__(self, save_location:str, preferred_backend:Optional[str]=None):
        self.save_location = save_location
        if preferred_backend is not None:
            jsonpickle.set_preferred_backend(preferred_backend)

    def load(self, uid: str) -> SaveableType:
        with open(self.save_location + uid, 'r', encoding="utf-8") as f:
            return jsonpickle.decode(f.read())

    def save(self, o: SaveableType, uid: str):
        to_save:str = jsonpickle.encode(o, unpicklable=False, keys=True)
        with open(self.save_location + uid, 'w', encoding="utf-8") as f:
            f.write(to_save)

