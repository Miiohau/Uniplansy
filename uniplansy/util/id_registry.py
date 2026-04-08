"""defines IDRegistry and supporting errors and globals

IDRegistry(Class): a registry of objects with unique ID
RegistryKeyError(Error): an error raised when there is a problem with a key used in an IDRegistry
RegistryKeyNotFoundError(Error): an error raised when a key is not found in an IDRegistry
RegistryKeyAlreadyExistsError(Error): an error raised when a key already exists in an IDRegistry
id_registry_registry(global): the global registry of IDIDRegistries
"""
from dataclasses import dataclass, field
from typing import TypeVar, Generic, Optional, Any

from uniplansy.util.uid_suppliers.default_guid_supplier import default_guid_supplier
from uniplansy.util.uid_suppliers.uid_supplier import UIDSupplier
from uniplansy.util.has_uid import HasRequiredUID


class RegistryKeyError(ValueError):
    """an error raised when there is a problem with a key used in an IDRegistry"""

    UID_REGEX: str = "<key>"
    pass


class RegistryKeyNotFoundError(RegistryKeyError):
    """an error raised a key isn't found in an IDRegistry"""

    def __init__(self, msg='ID (' + RegistryKeyError.UID_REGEX + ') not registered', uid='', *args):
        final_msg = msg.replace(RegistryKeyError.UID_REGEX, uid)
        super().__init__(final_msg, *args)


class RegistryKeyAlreadyExistsError(RegistryKeyError):
    """an error raised when trying to register an object under a key that already exists"""

    def __init__(self, msg='ID (' + RegistryKeyError.UID_REGEX + ') already registered', uid='', *args):
        final_msg = msg.replace(RegistryKeyError.UID_REGEX, uid)
        super().__init__(final_msg, *args)


#TODO: (after upgrading to python 3.12) Remove TypeVars and convert to new Type Parameter Syntax
Registered_Object = TypeVar('Registered_Object')


@dataclass
class IDRegistry(HasRequiredUID, Generic[Registered_Object]):
    """a registry of objects with unique IDs.

    register(method): registers an object under a unique ID
    fetch(method): fetch an object from the registry
    retire_referred_object(method): retires an object from the registry
    retire_self(method): retires this registry and all contained objects
    contains(method): checks whether uid is in registry
    reregister(method): reregister an object under its unique ID. In practice a looser register that allows replacement
    if that UID is currently None (likely because it was retired)
    replace(method):replaces the object registered a unique ID. Should rarely be needed.
    The point of an IDRegistry is to be a stable lookup table for objects.
    """
    uid: str = field(default_factory=default_guid_supplier.create_guid)
    _registry: dict[str, Registered_Object] = field(default_factory=dict[str, Optional[Registered_Object]], init=False)
    guid_supplier: Optional[UIDSupplier] = None

    def __eq__(self, other):
        return self is other

    def register(self, uid: str, item: Registered_Object):
        """register an object under a unique ID
        :param uid: the unique ID to register the object under
        :param item: the object to be registered
        :throws RegistryKeyNotFoundError: if uid is already registered
        """
        if (uid in self._registry.keys()) and (not (item is self._registry[uid])):
            raise RegistryKeyAlreadyExistsError(uid=uid)
        self._registry[uid] = item

    def reregister(self, uid: str, item: Registered_Object):
        """reregister an object under its unique ID

        in practice a looser register that allows replacement if that UID is currently None
        (likely because it was retired)
        :param uid: the unique ID to reregister the object under
        :param item: the object to be reregistered"""
        if (uid in self._registry.keys()) and (not (item is self._registry[uid])) and (self._registry[uid] is not None):
            raise RegistryKeyAlreadyExistsError(uid=uid)
        self._registry[uid] = item

    def replace(self, uid: str, item: Registered_Object) -> Optional[Registered_Object]:
        """replaces the object registered a unique ID

        should rarely be needed. The point of an IDRegistry is to be a stable lookup table for objects.
        :param uid: the unique ID to replace the object registered
        :param item: the object to replace the existing object with
        :returns: the replaced object"""
        return_value = self._registry[uid]
        self._registry[uid] = item
        return return_value

    def contains(self, uid: str) -> bool:
        """check whether uid is in registry
        :param uid: the unique ID to check
        :return: whether uid is in registry
        """
        return uid in self._registry

    def fetch(self, uid: str) -> Optional[Registered_Object]:
        """fetch an object from the registry.

        may be None if the object has been retired.
        :param uid: the ID of the object to be fetched
        :return: the object if the id isn't retired, otherwise None
        :throws RegistryKeyNotFoundError: if uid is not registered
        """
        if uid not in self._registry:
            raise RegistryKeyNotFoundError(uid=uid)
        return self._registry[uid]

    def retire_referred_object(self, uid: str):
        """retires an object from the registry.

        :param uid: the ID of the object to be retired
        :throws RegistryKeyNotFoundError: if uid is not registered
        """
        if uid not in self._registry:
            raise RegistryKeyNotFoundError("Can't retire an object (" + uid + ") that was never registered")
        self._registry[uid] = None

    def retire_self(self):
        """retires this registry and all contained objects"""
        for uid in self._registry:
            self._registry[uid] = None
        try:
            id_registry_registry.retire_referred_object(self.uid)
        except RegistryKeyNotFoundError:
            pass


"""the global registry of IDIDRegistries"""
id_registry_registry: IDRegistry[IDRegistry[Any]] = IDRegistry(uid="__internal__.id_registry_registry")