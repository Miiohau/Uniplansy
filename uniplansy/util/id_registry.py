from dataclasses import dataclass, field
from typing import TypeVar, Generic, Optional, Any

from uniplansy.util.guid_suppliers.guid_supplier import GUIDSupplier, default_guid_supplier


class RegistryKeyError(ValueError):
    pass

class RegistryKeyNotFoundError(RegistryKeyError):
    def __init__(self, msg='ID not registered', *args):
        super().__init__(msg, *args)

class RegistryKeyAlreadyExistsError(RegistryKeyError):
    def __init__(self, msg='ID already registered', *args):
        super().__init__(msg, *args)

#TODO: (after upgrading to python 3.12) Remove TypeVars and convert to new Type Parameter Syntax
Registered_Object = TypeVar('Registered_Object')

@dataclass
class IDRegistry(Generic[Registered_Object]):
    uid: str = field(default_factory=default_guid_supplier.create_guid)
    _registry:dict[str, Registered_Object] = field(default_factory=dict[str, Optional[Registered_Object]], init=False)
    guid_supplier:Optional[GUIDSupplier] = None


    def __eq__(self, other):
        return self is other

    def register(self, uid:str, item:Registered_Object):
        if (uid in self._registry) and (not (item is self._registry[uid])):
            raise RegistryKeyAlreadyExistsError()
        self._registry[uid] = item

    def contains(self, uid:str) -> bool:
        return uid in self._registry

    def fetch(self, uid:str) -> Optional[Registered_Object]:
        if uid not in self._registry:
            raise RegistryKeyNotFoundError()
        return self._registry[uid]

    def retire_referred_object(self, uid:str):
        if uid not in self._registry:
            raise RegistryKeyNotFoundError()
        self._registry[uid] = None

    def retire_self(self):
        for uid in self._registry:
            self._registry[uid] = None



id_registry_registry:IDRegistry[IDRegistry[Any]] = IDRegistry(uid="__internal__.id_registry_registry")