"""GUID Suppliers create globally unique IDs for use in IDRegistries or PersistenceManagers
"""
from abc import ABCMeta, abstractmethod

class UIDSupplier(metaclass=ABCMeta):
    """A UIDSupplier creates unique IDs for use in IDRegistries or PersistenceManagers

    :method create_guid: creates a unique guid."""

    @abstractmethod
    def create_guid(self, prefix: str = "") -> str:
        """
        creates a unique guid.

        The prefix is recommended to give context in case the guid shows up somewhere.
        :param prefix: the prefix to give the guid
        """
        pass


class GUIDSupplier(UIDSupplier, metaclass=ABCMeta):
    """a UID UIDSupplier that creates globally unique IDs

    This is a marker interface for classes that make a best effort to create unique IDs, it isn't guaranteed"""
    pass

class LocalUIDSupplier(UIDSupplier, metaclass=ABCMeta):
    """a UID UIDSupplier that creates unique IDs across it lifetime.

    This is a marker interface for UIDSupplier that explicitly don't guarantee
    the ids generated are unique across different instances"""

