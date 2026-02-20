"""GUID Suppliers create globally unique IDs for use in IDRegistries or PersistenceManagers
"""
from abc import ABCMeta, abstractmethod

from uniplansy.util.guid_suppliers.thread_local.thread_local_guid_supplier import ThreadLocalGuidSupplier


class GUIDSupplier(metaclass=ABCMeta):
    """A GUID Supplier creates globally unique IDs for use in IDRegistries or PersistenceManagers

    :method create_guid: creates a unique guid."""

    @abstractmethod
    def create_guid(self, prefix: str = "") -> str:
        """
        creates a unique guid.

        The prefix is recommended to give context in case the guid shows up somewhere.
        :param prefix: the prefix to give the guid
        """
        pass


default_guid_supplier = ThreadLocalGuidSupplier()