from uniplansy.util.guid_suppliers.guid_supplier import GUIDSupplier
from uniplansy.util.id_registry import IDRegistry


class UniqueInIDRegistryGUIDSupplierWrapper(GUIDSupplier):

    def __init__(self, registry:IDRegistry, delegate:GUIDSupplier):
        self.registry = registry
        self.delegate = delegate

    def create_guid(self, prefix: str = "") -> str:
        possible_guid: str
        while True:
            possible_guid = self.delegate.create_guid(prefix)
            if not self.registry.contains(possible_guid):
                break
        return possible_guid
