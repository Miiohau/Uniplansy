from __future__ import annotations

import copy
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Self, TypeVar, Generic, List, final

from uniplansy.reasoners.considerations.core import ReasonerConsideration
from uniplansy.util.custom_copyable import CustomCopyable
from uniplansy.util.global_type_vars import World_Type
from uniplansy.util.has_uid import HasOptionalUID, HasRequiredUID
from uniplansy.util.id_registry import IDRegistry
from uniplansy.util.uid_suppliers.uid_supplier import GUIDSupplier

#TODO: (after upgrading to python 3.12) Remove convert to new Type Parameter Syntax
Reasoner_Update_Context_Type: TypeVar = TypeVar('Reasoner_Update_Context_Type')


class ReasonerException(Exception):
    pass


class ChildFailureException(ReasonerException):

    def __init__(self, child: Optional[Reasoner], msg: Optional[str] = None, *args):
        if (msg is None) and (child is not None):
            msg = "ChildFailureException for child " + child.uid
        super().__init__(msg, *args)


class ReasonerEnterException(ReasonerException):
    pass


class TryingToEnterAFailedReasonerException(ReasonerEnterException):
    pass


class TryingToEnterARunningReasonerException(ReasonerEnterException):
    pass


class ReasonerState(Enum):
    Not_Started = ("not started", False, False)
    Waiting = ("waiting", True, False)
    Continue = ("continue", True, False)
    Running = ("running", True, False)
    Done = ("done", False, True)
    Failed = ("failed", False, True)

    def __init__(self, name: str, is_in_progress_state: bool, is_finalized_state: bool):
        self._name_: str = name
        self.is_finalized_state: bool = is_finalized_state
        self.is_in_progress_state: bool = is_in_progress_state


@dataclass
class SubReasonerStruct(Generic[Reasoner_Update_Context_Type, World_Type]):
    reasoner: Reasoner[Reasoner_Update_Context_Type, World_Type]
    active_reasoner_considerations: List[ReasonerConsideration] = field(default_factory=list)
    entered_sub_reasoner: bool = field(default=False, init=False)
    should_null_sub_reasoner: bool = field(default=False, init=False)
    last_update_state: ReasonerState = field(default=ReasonerState.Not_Started, init=False)
    enter_state: ReasonerState = field(default=ReasonerState.Not_Started, init=False)


class Reasoner(HasRequiredUID, Generic[Reasoner_Update_Context_Type, World_Type], metaclass=ABCMeta):

    def __init__(self, uid: str,
                 id_registry: IDRegistry[ReasonerBuilder],
                 start_conditions: List[ReasonerConsideration] = None,
                 run_conditions: List[ReasonerConsideration] = None):
        super().__init__()
        if start_conditions is None:
            start_conditions = []
        if run_conditions is None:
            run_conditions = []
        self.uid: str = uid
        self.id_registry: IDRegistry[ReasonerBuilder] = id_registry
        self.start_conditions: List[ReasonerConsideration] = start_conditions
        self.run_conditions: List[ReasonerConsideration] = run_conditions
        self.state: ReasonerState = ReasonerState.Not_Started
        self.failure_context: Optional[Exception] = None
        self.active_sub_reasoners: List[SubReasonerStruct[Reasoner_Update_Context_Type, World_Type]] = []

    def _build_failure_context(self, new_context: Exception, existing_context: Optional[Exception]) \
            -> Optional[Exception]:
        """Helper to build/collapse ExceptionGroups consistently."""
        if existing_context is None:
            return new_context
        elif isinstance(existing_context, ExceptionGroup):
            new_exceptions = list(existing_context.exceptions)
            new_exceptions.append(new_context)
            return ExceptionGroup(f"failure ExceptionGroup for Reasoner {self.uid}", new_exceptions)
        else:
            return ExceptionGroup(f"failure ExceptionGroup for Reasoner {self.uid}", [existing_context, new_context])

    # noinspection PyUnusedLocal
    def handle_self_caused_errors(self, update_context: Reasoner_Update_Context_Type, error: BaseException):
        """handles self-caused errors.

        In general subclasses shouldn't override this method instead they should handle the error inside
        the method causing it."""
        self.state = ReasonerState.Failed
        self.failure_context = error

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def think(self, update_context: Reasoner_Update_Context_Type) \
            -> List[SubReasonerStruct[Reasoner_Update_Context_Type, World_Type]]:
        """. Here is where you set other Reasoners as a children (by returning them) as well as any
        ReasonerConsiderations that have to remain true for that Reasoner to remain a valid choice.

        TODO:finish doc"""
        return []

    def handle_think_error(self, update_context: Reasoner_Update_Context_Type, error: BaseException):
        """handles self-caused errors leaving the think method.

        In general subclasses shouldn't override this method instead they should handle the error inside
        the think method."""
        self.handle_self_caused_errors(update_context, error)

    def sense(self, world: World_Type, update_context: Reasoner_Update_Context_Type) -> Reasoner_Update_Context_Type:
        """updates the internal state of the Reasoner and adds notes to update_context"""
        if not self.state.is_finalized_state:
            can_run = True
            for cur_condition in self.start_conditions:
                can_run = can_run and cur_condition.is_valid_state(world)
            if can_run:
                self.state = ReasonerState.Continue
            else:
                self.state = ReasonerState.Waiting
        failed = False
        for cur_condition in self.run_conditions:
            failed = failed or not cur_condition.is_valid_state(world)
        if failed:
            self.state = ReasonerState.Failed
        return update_context

    # noinspection PyUnusedLocal
    def handle_sense_error(self, world: World_Type, update_context: Reasoner_Update_Context_Type, error: BaseException):
        """handles self-caused errors leaving the sense method.

        In general subclasses shouldn't override this method instead they should handle the error inside
        the sense method."""
        self.handle_self_caused_errors(update_context, error)

    # noinspection PyUnusedLocal
    def act(self, world: World_Type, update_context: Reasoner_Update_Context_Type):
        """preforms actions in the world. This implementation only sets the Reasoner's state to done"""
        self.state = ReasonerState.Done

    # noinspection PyUnusedLocal
    def handle_act_error(self, world: World_Type, update_context: Reasoner_Update_Context_Type,
                         error: BaseException):
        """handles self-caused errors leaving the act method.

        In general subclasses shouldn't override this method instead they should handle the error inside
        the act method."""
        self.handle_self_caused_errors(update_context, error)

    # noinspection PyUnusedLocal
    def enter(self, update_context: Reasoner_Update_Context_Type) -> ReasonerState:
        """enters the Reasoner. by default, it is a fail state to renter a running Reasoner or failed Reasoner but
        a finished(done) Reasoner will immediately return Done"""
        if self.state == ReasonerState.Running:
            raise TryingToEnterARunningReasonerException()
        if self.state == ReasonerState.Failed:
            raise TryingToEnterAFailedReasonerException() from self.failure_context
        if self.state == ReasonerState.Not_Started:
            if len(self.start_conditions) == 0:
                self.state = ReasonerState.Running
            else:
                self.state = ReasonerState.Waiting
        return self.state

    def exit(self, update_context: Reasoner_Update_Context_Type):
        """tells the Reasoner to clean up and exit"""
        for cur_sub_reasoner_struct in self.active_sub_reasoners:
            cur_sub_reasoner_struct.reasoner.exit(update_context)
        self.active_sub_reasoners = []
        if self.state != ReasonerState.Failed:
            self.state = ReasonerState.Done

    # noinspection PyUnusedLocal
    def handle_active_reasoner_consideration_failure(self,
                                                     child: SubReasonerStruct[Reasoner_Update_Context_Type, World_Type],
                                                     failed_considerations: list[ReasonerConsideration],
                                                     update_context: Reasoner_Update_Context_Type,
                                                     failure_context: Optional[Exception]):
        self.state = ReasonerState.Failed
        self.failure_context = failure_context

    # noinspection PyUnusedLocal
    def handle_child_failure(self,
                             child: SubReasonerStruct[Reasoner_Update_Context_Type, World_Type],
                             update_context: Reasoner_Update_Context_Type,
                             failure_context: Optional[Exception]):
        self.state = ReasonerState.Failed
        new_failure_context: ChildFailureException = ChildFailureException(child=child.reasoner)
        new_failure_context.__cause__ = failure_context
        self.failure_context = new_failure_context

    def handle_child_enter_failure(self,
                                   child: SubReasonerStruct[Reasoner_Update_Context_Type, World_Type],
                                   update_context: Reasoner_Update_Context_Type,
                                   failure_context: Optional[Exception]):
        self.handle_child_failure(child, update_context, failure_context)

    def handle_child_success(self, child: SubReasonerStruct[Reasoner_Update_Context_Type, World_Type],
                             update_context: Reasoner_Update_Context_Type):
        pass

    def run_child(self,
                  child: SubReasonerStruct[Reasoner_Update_Context_Type, World_Type],
                  world: World_Type,
                  update_context: Reasoner_Update_Context_Type) -> ReasonerState:
        child.last_update_state = child.reasoner.update(world, update_context)
        if child.last_update_state is ReasonerState.Failed:
            child.should_null_sub_reasoner = True
            self.handle_child_failure(update_context, child, child.reasoner.failure_context)
        elif child.last_update_state is ReasonerState.Done:
            child.should_null_sub_reasoner = True
            self.handle_child_success(update_context, child)
        elif self.state.is_in_progress_state:
            if child.last_update_state is ReasonerState.Running:
                self.state = ReasonerState.Running
            elif self.state is ReasonerState.Continue:
                self.state = child.last_update_state
        if child.last_update_state.is_finalized_state and child.should_null_sub_reasoner:
            self.active_sub_reasoners.remove(child)
        return child.reasoner.state

    def run_children(self,
                     active_sub_reasoners: List[SubReasonerStruct[Reasoner_Update_Context_Type, World_Type]],
                     world: World_Type,
                     update_context: Reasoner_Update_Context_Type):
        for curChild in active_sub_reasoners:
            self.run_child(curChild, world, update_context)

    def _validate_child_considerations(self, child: SubReasonerStruct[Reasoner_Update_Context_Type, World_Type],
                                       world: World_Type, update_context: Reasoner_Update_Context_Type):
        """Check and validate child's considerations"""
        should_continue = True
        failure_context: Optional[Exception] = None
        failed_considerations = []
        for consideration in child.active_reasoner_considerations:
            try:
                if not consideration.is_valid_state(world):
                    should_continue = False
                    failed_considerations.append(consideration)
            except ReasonerException as e:
                should_continue = False
                failed_considerations.append(consideration)
                failure_context = self._build_failure_context(e, failure_context)
        if not should_continue:
            child.should_null_sub_reasoner = True
            self.handle_active_reasoner_consideration_failure(
                child, failed_considerations, update_context, failure_context
            )
            if child.should_null_sub_reasoner:
                child.reasoner.exit(update_context)
                self.active_sub_reasoners.remove(child)

    def _handle_new_sub_reasoners(self, update_context: Reasoner_Update_Context_Type):
        """Process newly discovered sub-reasoners"""
        new_reasoners = []
        if self.state.is_in_progress_state:
            try:
                new_reasoners = self.think(update_context)
            except BaseException as error:
                self.handle_think_error(update_context, error)
        for child in new_reasoners:
            if self.active_sub_reasoners.count(child) == 0:
                self.active_sub_reasoners.append(child)
                child.entered_sub_reasoner = True
                try:
                    child.enter_state = child.reasoner.enter(update_context)
                    if child.enter_state.is_finalized_state:
                        child.should_null_sub_reasoner = True
                        if child.enter_state is ReasonerState.Done:
                            self.handle_child_success(update_context, child)
                except ReasonerException as e:
                    child.should_null_sub_reasoner = True
                    child.enter_state = ReasonerState.Failed
                    self.handle_child_enter_failure(child, update_context, e)
                if child.enter_state.is_finalized_state and child.should_null_sub_reasoner:
                    self.active_sub_reasoners.remove(child)

    @final
    def update(self, world: World_Type, parent_update_context: Reasoner_Update_Context_Type) -> ReasonerState:
        update_context = copy.deepcopy(parent_update_context)
        # Sense and early exit
        try:
            update_context = self.sense(world, update_context)
        except BaseException as error:
            self.handle_sense_error(world, update_context, error)
        if self.state.is_finalized_state:
            self.exit(update_context)
            return self.state
        # Process children
        for child in self.active_sub_reasoners:
            self._validate_child_considerations(child, world, update_context)
        self.run_children(self.active_sub_reasoners, world, update_context)
        self._handle_new_sub_reasoners(update_context)
        if self.state.is_finalized_state:
            self.exit(update_context)
            return self.state
        # Perform action
        try:
            self.act(world, update_context)
        except BaseException as error:
            self.handle_act_error(world, update_context, error)
        if self.state.is_finalized_state:
            self.exit(update_context)
        return self.state


@dataclass
class ReasonerBuilder(HasOptionalUID, CustomCopyable, metaclass=ABCMeta):
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
    def build(self, id_registry: IDRegistry[ReasonerBuilder], guid_supplier: Optional[GUIDSupplier] = None) -> Reasoner:
        """builds the Reasoner. Note: id_registry may not be finalized or even contain all the uids contained in
        sub_reasoner_uids at the time this is called so the id_registry should be passed to the instance if needed.

        TODO:finish docstring"""
        pass

    # @override
    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def set_matching_deep_copy(self, other: Self, memo):
        other.uid = None
