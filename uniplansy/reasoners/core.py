
#TODO: (after updating to python 3.14 (in which Annotations are lazily evaluated by default)) remove "from __future__ import annotations"
from __future__ import annotations

import copy
from abc import ABCMeta
from dataclasses import dataclass, field
from enum import Enum
from typing import TypeVar, Generic, Optional, List, Any

from uniplansy.reasoners.considerations.core import ReasonerConsideration
from uniplansy.util.id_registry import IDRegistry

#TODO: (after upgrading to python 3.12) Remove convert to new Type Parameter Syntax
Reasoner_Update_Context_Type = TypeVar('Reasoner_Update_Context_Type')
World_Type = TypeVar('World_Type')



class ReasonerException(Exception):
    pass

class ChildFailureException(ReasonerException):
    pass

class ReasonerEnterException(ReasonerException):
    pass

class TryingToEnterAFailedReasonerException(ReasonerEnterException):
    pass

class TryingToEnterARunningReasonerException(ReasonerEnterException):
    pass

class ReasonerState(Enum):
    Not_Started = ("not started",False,False)
    Waiting = ("waiting",True,False)
    Continue = ("continue", True, False)
    Running = ("running",True,False)
    Done = ("done",False,True)
    Failed = ("failed",False,True)

    def __init__(self, name:str, is_in_progress_state:bool, is_finalized_state:bool):
        self._name_:str = name
        self.is_finalized_state:bool = is_finalized_state
        self.is_in_progress_state:bool = is_in_progress_state

@dataclass
class SubReasonerStruct(Generic[Reasoner_Update_Context_Type,World_Type]):
    reasoner: Reasoner[Reasoner_Update_Context_Type,World_Type]
    active_reasoner_considerations: List[ReasonerConsideration] = field(default_factory=list)
    entered_sub_reasoner: bool = field(default=False, init=False)
    should_null_sub_reasoner: bool = field(default=False, init=False)
    last_update_state: ReasonerState = field(default=ReasonerState.Not_Started, init=False)
    enter_state: ReasonerState = field(default=ReasonerState.Not_Started, init=False)

class Reasoner(Generic[Reasoner_Update_Context_Type,World_Type],metaclass=ABCMeta):


    def __init__(self, uid:str, id_registry:IDRegistry[Reasoner], start_conditions:List[ReasonerConsideration]=None, run_conditions:List[ReasonerConsideration]=None):
        super().__init__()
        if start_conditions is None:
            start_conditions = []
        if run_conditions is None:
            run_conditions = []
        self.uid:str = uid
        self.id_registry:IDRegistry[Reasoner] = id_registry
        self.start_conditions:List[ReasonerConsideration] = start_conditions
        self.run_conditions:List[ReasonerConsideration] = run_conditions
        self.state:ReasonerState = ReasonerState.Not_Started
        self.failure_context:Optional[Exception] = None
        self.active_sub_reasoners:List[SubReasonerStruct[Reasoner_Update_Context_Type,World_Type]] = []

    # noinspection PyUnusedLocal
    def handle_self_caused_errors(self, update_context:Reasoner_Update_Context_Type, error:BaseException):
        """handles self-caused errors. In general subclasses shouldn't override this method instead they should handle the error inside the method causing it."""
        self.state = ReasonerState.Failed
        self.failure_context = error

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def think(self, update_context:Reasoner_Update_Context_Type) -> List[SubReasonerStruct[Reasoner_Update_Context_Type,World_Type]]:
        """. Here is where you set other Reasoners as a children (by returning them) as well as any ReasonerConsiderations that have to remain true for that Reasoner to remain a valid choice."""
        return []

    def handle_think_error(self, update_context:Reasoner_Update_Context_Type, error:BaseException):
        """handles self-caused errors leaving the think method. In general subclasses shouldn't override this method instead they should handle the error inside the think method."""
        self.handle_self_caused_errors(update_context, error)

    def sense(self, world:World_Type, update_context:Reasoner_Update_Context_Type) -> Reasoner_Update_Context_Type:
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
    def handle_sense_error(self, world:World_Type, update_context:Reasoner_Update_Context_Type, error:BaseException):
        """handles self-caused errors leaving the sense method. In general subclasses shouldn't override this method instead they should handle the error inside the sense method."""
        self.handle_self_caused_errors(update_context, error)

    # noinspection PyUnusedLocal
    def act(self, world:World_Type, update_context:Reasoner_Update_Context_Type):
        """preforms actions in the world. This implementation only sets the Reasoner's state to done"""
        self.state = ReasonerState.Done

    # noinspection PyUnusedLocal
    def handle_act_error(self, world: World_Type, update_context: Reasoner_Update_Context_Type,
                               error: BaseException):
        """handles self-caused errors leaving the act method. In general subclasses shouldn't override this method instead they should handle the error inside the act method."""
        self.handle_self_caused_errors(update_context, error)

    # noinspection PyUnusedLocal
    def enter(self, update_context:Reasoner_Update_Context_Type) -> ReasonerState:
        """enters the Reasoner. by default, it is a fail state to renter a running Reasoner or failed Reasoner but a finished(done) Reasoner will immediately return Done"""
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

    def exit(self, update_context:Reasoner_Update_Context_Type):
        """tells the Reasoner to clean up and exit"""
        for cur_sub_reasoner_struct in self.active_sub_reasoners:
            cur_sub_reasoner_struct.reasoner.exit(update_context)
        self.active_sub_reasoners = []
        if self.state != ReasonerState.Failed:
            self.state = ReasonerState.Done

    # noinspection PyUnusedLocal
    def handle_active_reasoner_consideration_failure(self,child:SubReasonerStruct[Reasoner_Update_Context_Type,World_Type],failed_considerations:list[ReasonerConsideration], update_context:Reasoner_Update_Context_Type, failure_context:Optional[Exception]):
        self.state = ReasonerState.Failed
        self.failure_context = failure_context

    # noinspection PyUnusedLocal
    def handle_child_failure(self, child:SubReasonerStruct[Reasoner_Update_Context_Type,World_Type], update_context:Reasoner_Update_Context_Type, failure_context:Optional[Exception]):
        self.state = ReasonerState.Failed
        new_failure_context:ChildFailureException = ChildFailureException()
        new_failure_context.__cause__ = failure_context
        self.failure_context = new_failure_context

    def handle_child_enter_failure(self, child:SubReasonerStruct[Reasoner_Update_Context_Type,World_Type], update_context:Reasoner_Update_Context_Type,failure_context:Optional[Exception]):
        self.handle_child_failure(child,update_context,failure_context)

    def handle_child_success(self, child:SubReasonerStruct[Reasoner_Update_Context_Type,World_Type], update_context:Reasoner_Update_Context_Type):
        pass

    def update(self, world:World_Type, parent_update_context:Reasoner_Update_Context_Type) -> ReasonerState:
        update_context = copy.deepcopy(parent_update_context)
        try:
            update_context = self.sense(world, update_context)
        except BaseException as error:
            self.handle_sense_error(world, update_context, error)
        if self.state.is_finalized_state:
            self.exit(update_context)
            return self.state
        for curChild in self.active_sub_reasoners:
            should_continue = True
            active_reasoner_consideration_failure_context :Optional[Exception] = None
            failed_considerations:list[ReasonerConsideration] = []
            for current_reasoner_consideration in curChild.active_reasoner_considerations:
                try:
                    if not current_reasoner_consideration.is_valid_state(world):
                        should_continue = False
                        failed_considerations.append(current_reasoner_consideration)
                except ReasonerException as e:
                    should_continue = False
                    failed_considerations.append(current_reasoner_consideration)
                    if active_reasoner_consideration_failure_context is None:
                        active_reasoner_consideration_failure_context = e
                    elif isinstance(active_reasoner_consideration_failure_context, ExceptionGroup):
                        inner_exceptions:list[Exception | ExceptionGroup[Exception | Any] | Any] = list(active_reasoner_consideration_failure_context.exceptions)
                        inner_exceptions.append(e)
                        active_reasoner_consideration_failure_context = ExceptionGroup("active reasoner considerations ExceptionGroup for Reasoner " + self.uid, inner_exceptions)
                    else:
                        inner_exceptions: list[Exception | ExceptionGroup[Exception | Any] | Any] = list()
                        inner_exceptions.append(active_reasoner_consideration_failure_context)
                        inner_exceptions.append(e)
                        active_reasoner_consideration_failure_context = ExceptionGroup("active reasoner considerations ExceptionGroup for Reasoner " + self.uid, inner_exceptions)
            if not should_continue:
                curChild.should_null_sub_reasoner = True
                self.handle_active_reasoner_consideration_failure(curChild,failed_considerations, update_context,active_reasoner_consideration_failure_context)
                if curChild.should_null_sub_reasoner:
                    curChild.reasoner.exit(update_context)
                    self.active_sub_reasoners.remove(curChild)
        """TODO: allow customization of how the active_sub_reasoners are run"""
        for curChild in self.active_sub_reasoners:
            curChild.last_update_state = curChild.reasoner.update(world, update_context)
            if curChild.last_update_state is ReasonerState.Failed:
                curChild.should_null_sub_reasoner = True
                self.handle_child_failure(update_context,curChild,curChild.reasoner.failure_context)
            elif curChild.last_update_state is ReasonerState.Done:
                curChild.should_null_sub_reasoner = True
                self.handle_child_success(update_context,curChild)
            elif self.state.is_in_progress_state:
                if curChild.last_update_state is ReasonerState.Running:
                    self.state = ReasonerState.Running
                elif self.state is ReasonerState.Continue:
                    self.state = curChild.last_update_state
            if curChild.last_update_state.is_finalized_state and curChild.should_null_sub_reasoner:
                self.active_sub_reasoners.remove(curChild)
        possible_new_sub_reasoners: List[SubReasonerStruct[Reasoner_Update_Context_Type,World_Type]] = []
        if self.state.is_in_progress_state:
            try:
                possible_new_sub_reasoners = self.think(update_context)
            except BaseException as error:
                self.handle_think_error(update_context,error)
            for curChild in possible_new_sub_reasoners:
                if self.active_sub_reasoners.count(curChild)==0:
                    self.active_sub_reasoners.append(curChild)
        if self.state.is_finalized_state:
            self.exit(update_context)
            return self.state
        if len(possible_new_sub_reasoners) >= 1:
            for curChild in possible_new_sub_reasoners:
                curChild.entered_sub_reasoner = True
                try:
                    curChild.enter_state = curChild.reasoner.enter(update_context)
                    if curChild.enter_state.is_finalized_state:
                        curChild.should_null_sub_reasoner = True
                        if curChild.enter_state is ReasonerState.Done:
                            self.handle_child_success(update_context,curChild)
                except ReasonerException as e:
                    curChild.should_null_sub_reasoner = True
                    curChild.enter_state = ReasonerState.Failed
                    self.handle_child_enter_failure(curChild,update_context,e)
                if curChild.enter_state.is_finalized_state and curChild.should_null_sub_reasoner:
                    self.active_sub_reasoners.remove(curChild)
        try:
            self.act(world,update_context)
        except BaseException as error:
            self.handle_act_error(world,update_context,error)
        if self.state.is_finalized_state:
            self.exit(update_context)
        return self.state

# basic Reasoners to use as building blocks
# Priority Sequence (short-circuiting) - invokes it's sub reasoners until one actual does work. Fails quickly if one of its sub reasoners fails.
# Priority Sequence (non-short-circuiting) - invokes it's sub reasoners until one actual does work
# Sequence (short-circuiting) - all must complete in order for success. Stops and returns failure at the first failure.
# Sequence (non-short-circuiting) - all must complete in order for success.
# Any (single threaded, short-circuiting) - any can compete successfully for this Reasoner to return success
# Any (multithreaded, short-circuiting) - any can compete successfully for this Reasoner to return success. Runs more than one sub Reasoners at the same time but all running sub Reasoners are exited after the first one completes successfully.
# Any (single threaded, non-short-circuiting) - any can compete successfully for this Reasoner to return success
# Any (multithreaded, non-short-circuiting) - any can compete successfully for this Reasoner to return success. Runs more than one sub Reasoners at the same time and all sub Reasoners allowed to complete or fail.
# All (single threaded, short-circuiting) - all must compete successfully for this Reasoner to return success but in any order
# All (multithreaded, short-circuiting) - all must compete successfully for this Reasoner to return success but in any order. Runs more than one sub Reasoners at the same time but  all running sub Reasoners are exited if one fails.
# All (single threaded, non-short-circuiting) - all must compete successfully for this Reasoner to return success but in any order
# All (multithreaded, non-short-circuiting) - all must compete successfully for this Reasoner to return success but in any order. Runs more than one sub Reasoners at the same time and all sub Reasoners allowed to complete or fail.