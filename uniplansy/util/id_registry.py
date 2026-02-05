import threading
from dataclasses import dataclass, field
from threading import local
from typing import TypeVar, Generic, Optional

_module_thread_local_data = local()



_thread_sequence : int = 0
_thread_sequence_lock = threading.Lock()

def create_thread_guid(prefix: str = "thread") -> str:
    """creates a globally unique id for use as a name of a thread."""
    global _thread_sequence,_thread_sequence_lock
    with _thread_sequence_lock:
        guid: str = prefix + "*" + str(_thread_sequence)
        _thread_sequence += 1
    return guid

_module_thread_local_data.sequence = 0

def create_guid_thread_local(prefix: str ="") -> str:
    """creates a guid in the context of the current thread. Note: assumes if the current thread is named that name is globally unique (you can create globally unique thread names via the create_thread_guid function). The prefix is recommended to give context in case the guid shows up somewhere."""
    global _module_thread_local_data
    thread_id:str
    current_thread_name = threading.current_thread().name
    current_thread_has_name = current_thread_name and current_thread_name.strip()
    if current_thread_has_name:
        thread_id = current_thread_name
    else:
        thread_id = "thread:" + str(threading.get_ident())
    guid: str = prefix +"$" + thread_id + "#" + str(_module_thread_local_data.sequence)
    _module_thread_local_data.sequence += 1
    return guid

class RegistryKeyError(ValueError):
    pass

class RegistryKeyNotFoundError(RegistryKeyError):
    def __init__(self, msg='ID not registered', *args):
        super().__init__(msg, *args)

class RegistryKeyAlreadyExistsError(RegistryKeyError):
    def __init__(self, msg='ID already registered', *args):
        super().__init__(msg, *args)

Registered_Object = TypeVar('Registered_Object')

@dataclass
class IDRegistry(Generic[Registered_Object]):
    registry:dict[str, Registered_Object] = field(default_factory=dict[str, Optional[Registered_Object]], init=False)


    def __eq__(self, other):
        return self is other

    def register(self, uid:str, item:Registered_Object):
        if (uid in self.registry) and (not (item is self.registry[uid])):
            raise RegistryKeyAlreadyExistsError()
        self.registry[uid] = item

    def contains(self, uid:str) -> bool:
        return uid in self.registry

    def fetch(self, uid:str) -> Optional[Registered_Object]:
        if uid not in self.registry:
            raise RegistryKeyNotFoundError()
        return self.registry[uid]

    def retire_referred_object(self, uid:str):
        if uid not in self.registry:
            raise RegistryKeyNotFoundError()
        self.registry[uid] = None

    def retire_self(self):
        for uid in self.registry:
            self.registry[uid] = None



guid_registry:IDRegistry[object] = IDRegistry()