#TODO: (after upgrading to python 3.12) uncomment @override Decorators
#TODO: (after updating to python 3.14 (in which Annotations are lazily evaluated by default)) remove "from __future__ import annotations"
from __future__ import annotations
import copy
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import List, TypeAlias, Any, Optional, Self

from uniplansy.reasoners.core import Reasoner
from uniplansy.util.custom_copyable import CustomCopyable
from uniplansy.util.guid_suppliers.guid_supplier import GUIDSupplier, default_guid_supplier
from uniplansy.util.guid_suppliers.wrappers.wrappers import UniqueInIDRegistryGUIDSupplierWrapper
from uniplansy.util.id_registry import IDRegistry

@dataclass
class ReasonerBuilder(CustomCopyable,metaclass=ABCMeta):
    """builds Reasoners. Note the name is slight misnomer this class can create more than one Reasoner, the build method merely returns the root Reasoner"""
    sub_reasoner_uids: List[str] = field(default_factory=list)
    preferred_name: str = ""
    uid: Optional[str] = field(default=None, init=False)
    template_guid_supplier:Optional[GUIDSupplier] = None

    def fill_unset_fields(self,id_registry:Optional[IDRegistry[ReasonerBuilder]] = None,guid_supplier:Optional[GUIDSupplier] = None):
        """this is helper method to fill ReasonerBuilder fields not required at init time but required at build time"""
        if self.uid is None:
            guid_supplier_to_use:Optional[GUIDSupplier] = guid_supplier or self.template_guid_supplier
            if (guid_supplier_to_use is None) and (id_registry is not None):
                guid_supplier_to_use = id_registry.guid_supplier
            if guid_supplier_to_use is None:
                guid_supplier_to_use = default_guid_supplier
            old_id_registry:Optional[IDRegistry[ReasonerBuilder]]= None
            if isinstance(guid_supplier_to_use,UniqueInIDRegistryGUIDSupplierWrapper) and id_registry is not None:
                old_id_registry = guid_supplier_to_use.registry
                guid_supplier_to_use.registry = id_registry
            self.uid = guid_supplier_to_use.create_guid(self.preferred_name)
            if isinstance(guid_supplier_to_use, UniqueInIDRegistryGUIDSupplierWrapper) and old_id_registry is not None:
                guid_supplier_to_use.registry = old_id_registry

    @abstractmethod
    def build(self, id_registry:IDRegistry[ReasonerBuilder],guid_supplier:Optional[GUIDSupplier] = None) -> Reasoner:
        """builds the Reasoner. Note: id_registry may not be finalized or even contain all the uids contained in sub_reasoner_uids at the time this is called so the id_registry should be passed to the instance if needed."""
        pass

    # @override
    def set_matching_deep_copy(self, other:Self, memo):
        other.sub_reasoner_uids = copy.deepcopy(self.sub_reasoner_uids,memo)
        other.template_guid_supplier = self.template_guid_supplier
        other.uid = None



#TODO: after updating to python 3.12 change this to a type statement
ReasonerTemplate:TypeAlias = ReasonerBuilder