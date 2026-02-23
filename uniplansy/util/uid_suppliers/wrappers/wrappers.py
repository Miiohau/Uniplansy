from typing import Any

from uniplansy.util.uid_suppliers.uid_supplier import UIDSupplier
from uniplansy.util.id_registry import IDRegistry


class UniqueInIDRegistryUIDSupplierWrapper(UIDSupplier):

    def __init__(self, registry: IDRegistry, delegate: UIDSupplier):
        self.registry = registry
        self.delegate = delegate

    def create_guid(self, prefix: str = "") -> str:
        possible_uid: str
        while True:
            possible_uid = self.delegate.create_guid(prefix)
            if not self.registry.contains(possible_uid):
                break
        return possible_uid


class UniqueInDictUIDSupplierWrapper(UIDSupplier):

    def __init__(self, wrapped_dict: dict[str, Any], delegate: UIDSupplier):
        self.wrapped_dict = wrapped_dict
        self.delegate = delegate

    def create_guid(self, prefix: str = "") -> str:
        possible_uid: str
        while True:
            possible_uid = self.delegate.create_guid(prefix)
            if not (possible_uid in self.wrapped_dict.keys()):
                break
        return possible_uid