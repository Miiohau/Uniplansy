#TODO: (after upgrading to python 3.12) uncomment @override Decorators
#TODO: (after updating to python 3.14 (in which Annotations are lazily evaluated by default)) remove "from __future__ import annotations"
from __future__ import annotations
import copy
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import List, TypeAlias, Optional, Self, Generic, Callable, ClassVar

from uniplansy.reasoners.considerations.core import ReasonerConsideration
from uniplansy.reasoners.core import Reasoner, ReasonerState, ThreadableCommonConjunctionReasoner, \
    PrioritySequenceReasoner, \
    World_Type, Reasoner_Update_Context_Type, SimpleReasoner
from uniplansy.util.custom_copyable import CustomCopyable
from uniplansy.util.uid_suppliers.uid_supplier import GUIDSupplier, default_guid_supplier
from uniplansy.util.uid_suppliers.wrappers.wrappers import UniqueInIDRegistryUIDSupplierWrapper
from uniplansy.util.has_preferred_name import HasPreferredName
from uniplansy.util.has_uid import HasOptionalUID
from uniplansy.util.id_registry import IDRegistry

@dataclass
class ReasonerBuilder(CustomCopyable,HasOptionalUID,metaclass=ABCMeta):
    """builds Reasoners. Note the name is slight misnomer this class can create more than one Reasoner,
    the build method merely returns the root Reasoner

    TODO:finish docstring"""
    """the reasoner's uid """
    uid: Optional[str] = field(default=None, init=False)

    def fill_unset_fields(self, id_registry: Optional[IDRegistry[ReasonerBuilder]] = None,
                          guid_supplier: Optional[GUIDSupplier] = None):
        """this is helper method to fill ReasonerBuilder fields not required at init time but required at build time

        TODO:finish docstring"""
        pass

    @abstractmethod
    def build(self, id_registry:IDRegistry[ReasonerBuilder],guid_supplier:Optional[GUIDSupplier] = None) -> Reasoner:
        """builds the Reasoner. Note: id_registry may not be finalized or even contain all the uids contained in
        sub_reasoner_uids at the time this is called so the id_registry should be passed to the instance if needed.

        TODO:finish docstring"""
        pass

    # @override
    def set_matching_deep_copy(self, other: Self, memo):
        other.uid = None


@dataclass
class ReasonerBuilderBase(ReasonerBuilder, HasPreferredName,metaclass=ABCMeta):
    preferred_name: str = ""
    template_guid_supplier: Optional[GUIDSupplier] = None
    start_conditions: List[ReasonerConsideration] = None,
    run_conditions: List[ReasonerConsideration] = None

    # @override
    def set_matching_deep_copy(self, other: Self, memo):
        super().set_matching_deep_copy(other, memo)
        other.preferred_name = self.preferred_name
        other.template_guid_supplier = self.template_guid_supplier
        other.start_conditions = copy.deepcopy(other.start_conditions)
        other.run_conditions = copy.deepcopy(other.run_conditions)


    def fill_unset_fields(self,id_registry:Optional[IDRegistry[ReasonerBuilder]] = None,guid_supplier:Optional[GUIDSupplier] = None):
        """this is helper method to fill ReasonerBuilder fields not required at init time but required at build time"""
        if self.uid is None:
            guid_supplier_to_use:Optional[GUIDSupplier] = guid_supplier or self.template_guid_supplier
            if (guid_supplier_to_use is None) and (id_registry is not None):
                guid_supplier_to_use = id_registry.guid_supplier
            if guid_supplier_to_use is None:
                guid_supplier_to_use = default_guid_supplier
            old_id_registry:Optional[IDRegistry[ReasonerBuilder]]= None
            if isinstance(guid_supplier_to_use, UniqueInIDRegistryUIDSupplierWrapper) and id_registry is not None:
                old_id_registry = guid_supplier_to_use.registry
                guid_supplier_to_use.registry = id_registry
            self.uid = guid_supplier_to_use.create_guid(self.preferred_name)
            if isinstance(guid_supplier_to_use, UniqueInIDRegistryUIDSupplierWrapper) and old_id_registry is not None:
                guid_supplier_to_use.registry = old_id_registry

    def __deepcopy__(self, memo):
        new_copy:Self = type(self)()
        self.set_matching_deep_copy(new_copy, memo)
        return new_copy

@dataclass
class CommonConjunctionReasonerBuilder(ReasonerBuilderBase):
    sub_reasoner_uids: List[str] = field(default_factory=list)
    all_semantics: Optional[bool] = None,
    any_semantics: Optional[bool] = None,
    multithreaded: bool = False,
    short_circuiting: bool = True,
    default_finished_state: Optional[ReasonerState] = None,

    # @override
    def fill_unset_fields(self,id_registry:Optional[IDRegistry[ReasonerBuilder]] = None,guid_supplier:Optional[GUIDSupplier] = None):
        super().fill_unset_fields(id_registry,guid_supplier)
        if (self.all_semantics is None) and (self.any_semantics is not None):
            self.all_semantics = not self.any_semantics
        elif (self.all_semantics is not None) and (self.any_semantics is None):
            self.any_semantics = not self.all_semantics

    # @override
    def set_matching_deep_copy(self, other: Self, memo):
        other.sub_reasoner_uids = copy.deepcopy(self.sub_reasoner_uids, memo)
        other.all_semantics = self.all_semantics
        other.any_semantics = self.any_semantics
        other.multithreaded = other.multithreaded
        other.short_circuiting = other.short_circuiting
        other.default_finished_state = other.default_finished_state

    # @override
    def build(self, id_registry: IDRegistry[ReasonerBuilder], guid_supplier: Optional[GUIDSupplier] = None) -> Reasoner:
        self.fill_unset_fields(id_registry=id_registry, guid_supplier=guid_supplier)
        return ThreadableCommonConjunctionReasoner(uid=self.uid,
                                                   id_registry=id_registry,
                                                   sub_reasoner_uids=self.sub_reasoner_uids,
                                                   short_circuiting=self.short_circuiting,
                                                   multithreaded=self.multithreaded,
                                                   all_semantics=self.all_semantics,
                                                   any_semantics=self.any_semantics,
                                                   default_finished_state=self.default_finished_state,
                                                   start_conditions=self.start_conditions,
                                                   run_conditions=self.run_conditions,)

@dataclass
class PrioritySequenceReasonerBuilder(ReasonerBuilderBase):
    sub_reasoner_uids: List[str] = field(default_factory=list)
    all_semantics: Optional[bool] = True,
    any_semantics: Optional[bool] = None,
    short_circuiting: bool = True,
    default_finished_state: Optional[ReasonerState] = ReasonerState.Done

    # @override
    def fill_unset_fields(self,id_registry:Optional[IDRegistry[ReasonerBuilder]] = None,guid_supplier:Optional[GUIDSupplier] = None):
        super().fill_unset_fields(id_registry,guid_supplier)
        if (self.all_semantics is None) and (self.any_semantics is not None):
            self.all_semantics = not self.any_semantics
        elif (self.all_semantics is not None) and (self.any_semantics is None):
            self.any_semantics = not self.all_semantics

    # @override
    def set_matching_deep_copy(self, other: Self, memo):
        other.all_semantics = self.all_semantics
        other.any_semantics = self.any_semantics
        other.short_circuiting = other.short_circuiting
        other.default_finished_state = other.default_finished_state

    # @override
    def build(self, id_registry: IDRegistry[ReasonerBuilder], guid_supplier: Optional[GUIDSupplier] = None) -> Reasoner:
        self.fill_unset_fields(id_registry=id_registry, guid_supplier=guid_supplier)
        return PrioritySequenceReasoner(uid=self.uid,
                                        id_registry=id_registry,
                                        sub_reasoner_uids=self.sub_reasoner_uids,
                                        short_circuiting=self.short_circuiting,
                                        all_semantics=self.all_semantics,
                                        any_semantics=self.any_semantics,
                                        default_finished_state=self.default_finished_state,
                                        start_conditions=self.start_conditions,
                                        run_conditions=self.run_conditions)

@dataclass
class SimpleReasonerBuilder(Generic[World_Type,Reasoner_Update_Context_Type,],ReasonerBuilderBase):
    sense_delegate: Optional[Callable[[World_Type, Reasoner_Update_Context_Type], Reasoner_Update_Context_Type]] = None,
    act_delegate: Optional[Callable[[World_Type, Reasoner_Update_Context_Type], bool]] = None,

    def build(self, id_registry: IDRegistry[ReasonerBuilder], guid_supplier: Optional[GUIDSupplier] = None) -> Reasoner:
        self.fill_unset_fields(id_registry=id_registry, guid_supplier=guid_supplier)
        return SimpleReasoner(uid=self.uid,
                              id_registry=id_registry,
                              start_conditions=self.start_conditions,
                              run_conditions=self.run_conditions,
                              sense_delegate=self.sense_delegate,
                              act_delegate=self.act_delegate,)


@dataclass
class BaseReasonerBuilderWrapper(ReasonerBuilder, HasPreferredName, metaclass=ABCMeta):
    # TODO:Figure out why the linter says uid isn't set in the __init__ method without this redefinition(Should be set to None)
    uid: Optional[str] = field(default=None, init=False)
    wrapped_reasoner_builder: ReasonerBuilder
    preferred_name: str = ""
    template_guid_supplier: Optional[GUIDSupplier] = None

    WRAPPED_BUILDER_NAME:ClassVar[str] = "{wrapped_builder_name}"

    # @override
    def fill_unset_fields(self, id_registry: Optional[IDRegistry[ReasonerBuilder]] = None,
                          guid_supplier: Optional[GUIDSupplier] = None):
        """this is helper method to fill ReasonerBuilder fields not required at init time but required at build time

        TODO:finish docstring"""
        self.wrapped_reasoner_builder.fill_unset_fields(id_registry=id_registry, guid_supplier=guid_supplier)
        if self.preferred_name is None:
            self.preferred_name = self.__class__.__name__ + "@" + BaseReasonerBuilderWrapper.WRAPPED_BUILDER_NAME
        if isinstance(self.wrapped_reasoner_builder, HasPreferredName):
            self.preferred_name = self.preferred_name.replace(BaseReasonerBuilderWrapper.WRAPPED_BUILDER_NAME, self.wrapped_reasoner_builder.preferred_name)
        else:
            self.preferred_name = self.preferred_name.replace(BaseReasonerBuilderWrapper.WRAPPED_BUILDER_NAME,
                                                              self.wrapped_reasoner_builder.__class__.__name__)

        if self.uid is None:
            guid_supplier_to_use: Optional[GUIDSupplier] = guid_supplier or self.template_guid_supplier
            if (guid_supplier_to_use is None) and (id_registry is not None):
                guid_supplier_to_use = id_registry.guid_supplier
            if guid_supplier_to_use is None:
                guid_supplier_to_use = default_guid_supplier
            old_id_registry: Optional[IDRegistry[ReasonerBuilder]] = None
            if isinstance(guid_supplier_to_use, UniqueInIDRegistryUIDSupplierWrapper) and id_registry is not None:
                old_id_registry = guid_supplier_to_use.registry
                guid_supplier_to_use.registry = id_registry
            self.uid = guid_supplier_to_use.create_guid(self.preferred_name)
            if isinstance(guid_supplier_to_use, UniqueInIDRegistryUIDSupplierWrapper) and old_id_registry is not None:
                guid_supplier_to_use.registry = old_id_registry

    # @override
    def set_matching_deep_copy(self, other: Self, memo):
        super().set_matching_deep_copy(other, memo)
        other.wrapped_reasoner_builder = copy.deepcopy(self.wrapped_reasoner_builder, memo)
        other.preferred_name = self.preferred_name
        other.template_guid_supplier = self.template_guid_supplier

    # @override
    def __setattr__(self, name, value):
        if name in dir(self):
            super().__setattr__(name, value)
        else:
            setattr(self.wrapped_reasoner_builder, name, value)

    # @override
    def __delattr__(self, name):
        if name in dir(self):
            super().__delattr__(name)
        else:
            delattr(self.wrapped_reasoner_builder, name)

    # @override
    def __getattr__(self, name):
        return getattr(self.wrapped_reasoner_builder, name)

    # @override
    def __getattribute__(self, name):
        if name in dir(self):
            return super().__getattribute__(name)
        else:
            return getattr(self.wrapped_reasoner_builder, name)


@dataclass
class SingletonReasonerBuilderWrapper(BaseReasonerBuilderWrapper):
    singleton:Optional[Reasoner] = field(default=None, init=False)

    # @override
    # noinspection PyMethodMayBeStatic
    def set_matching_deep_copy(self, other: Self, memo):
        super().set_matching_deep_copy(other,memo)
        other.singleton = None


    def build(self, id_registry: IDRegistry[ReasonerBuilder], guid_supplier: Optional[GUIDSupplier] = None) -> Reasoner:
        if self.singleton is None:
            self.fill_unset_fields(id_registry=id_registry, guid_supplier=guid_supplier)
            self.singleton = self.wrapped_reasoner_builder.build(id_registry=id_registry, guid_supplier=guid_supplier)
        return self.singleton

#TODO: after updating to python 3.12 change this to a type statement
ReasonerTemplate:TypeAlias = ReasonerBuilder