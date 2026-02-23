import threading
from math import sqrt
from random import Random
from threading import local
from typing import Optional

from uniplansy.util.uid_suppliers.uid_supplier import GUIDSupplier


class RandomGUIDSupplier(GUIDSupplier):
    """a guid supplier that uses a random number generator to generate a guid

    this guid supplier will expand its random range if the chance of a collision roughly exceeds collision_chance
    TODO:finish docstring"""

    def __init__(self, start_max: int = 4294967296, collision_chance:float = .5, seed: Optional[int] = None):
        super().__init__()
        self.max: int = start_max
        self.collision_chance: float = collision_chance
        self.guid_generated: int = 0
        self.bound = sqrt(2 * self.max * self.collision_chance)
        self._rnd = Random(seed)

    def create_guid(self, prefix: str = "") -> str:
        self.guid_generated += 1
        if self.guid_generated > self.bound:
            self.max *= self.max
            self.bound = sqrt(2 * self.max * self.collision_chance)
        return prefix + "#" + str(self._rnd.randrange(self.max))


class ThreadedRandomGUIDSupplier(GUIDSupplier):
    """a version of RandomGUIDSupplier that may be faster in multithreaded environments because
    each thread has it own Random instance.

    like RandomGUIDSupplier, ThreadedRandomGUIDSupplier will expand its random range if the chance of a collision
    roughly exceeds collision_chance.
    TODO:finish docstring"""

    def __init__(self, start_max: int = 4294967296, collision_chance:float = .5, seed_prefix: Optional[int] = None):
        super().__init__()
        self._thread_local_data = local()
        self.start_max: int = start_max
        self.collision_chance: float = collision_chance
        self.start_bound: float = sqrt(self.start_max)
        self.seed_prefix: Optional[int] = seed_prefix

    _thread_sequence_lock = threading.Lock()
    _thread_guid_generated = 0
    _thread_max = 4294967296
    _thread_bound = 65536
    _thread_random = Random()

    @staticmethod
    def create_thread_guid(prefix: str = "thread") -> str:
        """
        creates a globally unique id for use as a name of a thread.

        :param prefix: the prefix to give the guid
        """
        with (ThreadedRandomGUIDSupplier._thread_sequence_lock):
            ThreadedRandomGUIDSupplier._thread_guid_generated += 1
            if ThreadedRandomGUIDSupplier._thread_guid_generated > ThreadedRandomGUIDSupplier._thread_bound:
                ThreadedRandomGUIDSupplier._thread_bound = ThreadedRandomGUIDSupplier._thread_max
                ThreadedRandomGUIDSupplier._thread_max *= ThreadedRandomGUIDSupplier._thread_max
            guid: str = prefix + "*" + str(
                ThreadedRandomGUIDSupplier._thread_random.randrange(ThreadedRandomGUIDSupplier._thread_max)
            )

        return guid

    def create_guid(self, prefix: str = "") -> str:
        """creates a guid in the context of the current thread.

        Note: assumes if the current thread is named that name is globally unique (you can create globally unique
        thread names via the create_thread_guid function).
        :param prefix: the prefix to give the guid
        """
        if self._thread_local_data.max is None:
            self._thread_local_data.max = self.start_max
            self._thread_local_data.bound = self.start_bound
            self._thread_local_data.guid_generated = 0
            if self.seed_prefix is not None:
                self._thread_local_data.rnd = Random(self.seed_prefix + threading.get_ident())
            else:
                self._thread_local_data.rnd = Random(threading.get_ident())
        self._thread_local_data.guid_generated += 1
        if self._thread_local_data.guid_generated > self._thread_local_data.bound:
            self._thread_local_data.max *= self._thread_local_data.max
            self._thread_local_data.bound = sqrt(2 * self._thread_local_data.max * self.collision_chance)
        thread_id: str
        current_thread_name = threading.current_thread().name
        current_thread_has_name = current_thread_name and current_thread_name.strip()
        if current_thread_has_name:
            thread_id = current_thread_name
        else:
            thread_id = "thread:" + str(threading.get_ident())
        return prefix + "$" + thread_id + "#" + str(self._thread_local_data.rnd.randrange(self._thread_local_data.max))