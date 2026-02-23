from uniplansy.util.uid_suppliers.uid_supplier import LocalUIDSupplier


class CounterBasedLocalLocalUIDSupplier(LocalUIDSupplier):

    def __init__(self):
        super().__init__()
        self._counter = 0

    def create_guid(self, prefix: str = "") -> str:
        uid: str = prefix + "#" + str(self._counter)
        self._counter += 1
        return uid
