"""
defines IDRegistry supporting errors and globals
"""
from dataclasses import dataclass, field
from typing import TypeVar, Generic, Optional, Any

from uniplansy.util.guid_suppliers.guid_supplier import GUIDSupplier, default_guid_supplier
from uniplansy.util.has_uid import HasRequiredUID


class RegistryKeyError(ValueError):
    """an error raised when there is a problem with a key used in an IDRegistry"""
    pass

class RegistryKeyNotFoundError(RegistryKeyError):
    """an error raised a key isn't found in an IDRegistry"""

    def __init__(self, msg='ID not registered', *args):
        super().__init__(msg, *args)


class RegistryKeyAlreadyExistsError(RegistryKeyError):
    """an error raised when trying to register an object under a key that already exists"""

    def __init__(self, msg='ID already registered', *args):
        super().__init__(msg, *args)


#TODO: (after upgrading to python 3.12) Remove TypeVars and convert to new Type Parameter Syntax
Registered_Object = TypeVar('Registered_Object')

@dataclass
class IDRegistry(Generic[Registered_Object],HasRequiredUID):
    """a registry of objects with unique IDs"""
    uid: str = field(default_factory=default_guid_supplier.create_guid)
    _registry:dict[str, Registered_Object] = field(default_factory=dict[str, Optional[Registered_Object]], init=False)
    guid_supplier:Optional[GUIDSupplier] = None

    def __eq__(self, other):
        return self is other

    def register(self, uid: str, item: Registered_Object):
        """
        register an object under a unique ID
        :param uid: the unique ID to register the object under
        :param item: the object to be registered
        """
        if (uid in self._registry) and (not (item is self._registry[uid])):
            raise RegistryKeyAlreadyExistsError()
        self._registry[uid] = item

    def contains(self, uid: str) -> bool:
        """
        check whether uid is in registry
        :param uid: the unique ID to check
        :return: whether uid is in registry
        """
        return uid in self._registry

    def fetch(self, uid:str) -> Optional[Registered_Object]:
        """
        fetch an object from registry.

        may be None if the object has been retired.
        :param uid: the ID of the object to be fetched
        :return: the object if the id isn't retired, otherwise None
        """
        if uid not in self._registry:
            raise RegistryKeyNotFoundError()
        return self._registry[uid]

    def retire_referred_object(self, uid:str):
        """
        retires an object from the registry.
        :param uid: the ID of the object to be retired
        """
        if uid not in self._registry:
            raise RegistryKeyNotFoundError("Can't retire an object that was never registered")
        self._registry[uid] = None

    def retire_self(self):
        """
        retires this registry and all contained objects
        """
        for uid in self._registry:
            self._registry[uid] = None
        try:
            id_registry_registry.retire_referred_object(self.uid)
        except RegistryKeyNotFoundError:
            pass


"""the global registry of IDIDRegistries"""
id_registry_registry: IDRegistry[IDRegistry[Any]] = IDRegistry(uid="__internal__.id_registry_registry")