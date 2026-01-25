#TODO: (after upgrading to python 3.12) Remove convert to new Type Parameter Syntax
#TODO: (after updating to python 3.14 (in which Annotations are lazily evaluated by default)) remove "from __future__ import annotations"
from __future__ import annotations

import copy
from abc import ABCMeta, abstractmethod
from enum import Enum, auto
from typing import TypeVar, Generic, Optional, List, Tuple, Any

from uniplansy.reasoners.considerations.core import ReasonerConsideration

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
    Not_Started = auto()
    Running = auto()
    Done = auto()
    Failed = auto()

class Reasoner((Generic[Reasoner_Update_Context_Type,World_Type]),metaclass=ABCMeta):
    sub_reasoner:Optional[Reasoner]
    active_reasoner_considerations:List[ReasonerConsideration]
    state:ReasonerState
    should_null_sub_reasoner:bool
    failure_context:Optional[Exception]
    entered_sub_reasoner:bool

    def __init__(self, guid:str):
        self.guid = guid
        self.active_reasoner_considerations = []
        self.sub_reasoner = None
        self.state = ReasonerState.Not_Started
        self.should_null_sub_reasoner = False
        self.entered_sub_reasoner = False
        self.failure_context = None

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def think(self, update_context:Reasoner_Update_Context_Type) -> Optional[Tuple[Reasoner, Optional[List[ReasonerConsideration]]]]:
        """. Here is where you set another Reasoner as a child (by returning it) as well as any ReasonerConsiderations that have to remain true for that Reasoner to remain a valid choice."""
        return None

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def sense(self, world:World_Type, update_context:Reasoner_Update_Context_Type) -> Reasoner_Update_Context_Type:
        """updates the internal state of the Reasoner and adds notes to update_context"""
        return update_context

    # noinspection PyUnusedLocal
    def act(self, world:World_Type, update_context:Reasoner_Update_Context_Type):
        """preforms actions in the world. This implementation only sets the Reasoner's state to done"""
        self.state = ReasonerState.Done

    # noinspection PyUnusedLocal
    def enter(self, update_context:Reasoner_Update_Context_Type) -> ReasonerState:
        """enters the Reasoner. by default, it is a fail state to renter a running Reasoner or failed Reasoner but a finished(done) Reasoner will immediately return Done"""
        if self.state == ReasonerState.Running:
            raise TryingToEnterARunningReasonerException()
        if self.state == ReasonerState.Failed:
            raise TryingToEnterAFailedReasonerException() from self.failure_context
        if self.state == ReasonerState.Not_Started:
            self.state = ReasonerState.Running
        return self.state

    def exit(self, update_context:Reasoner_Update_Context_Type):
        """tells the Reasoner to clean up and exit"""
        if self.sub_reasoner is not None:
            self.sub_reasoner.exit(update_context)
            self.active_reasoner_considerations = []
            self.sub_reasoner = None
        if self.state != ReasonerState.Failed:
            self.state = ReasonerState.Done

    # noinspection PyUnusedLocal
    def handle_active_reasoner_consideration_failure(self, update_context:Reasoner_Update_Context_Type, failure_context:Optional[Exception]):
        self.state = ReasonerState.Failed
        self.failure_context = failure_context

    # noinspection PyUnusedLocal
    def handle_child_failure(self, update_context:Reasoner_Update_Context_Type, failure_context:Optional[Exception]):
        self.state = ReasonerState.Failed
        new_failure_context:ChildFailureException = ChildFailureException()
        new_failure_context.__cause__ = failure_context
        self.failure_context = new_failure_context

    def handle_child_enter_failure(self, update_context:Reasoner_Update_Context_Type,failure_context:Optional[Exception]):
        self.handle_child_failure(update_context,failure_context)

    # noinspection PyUnusedLocal
    def _null_sub_reasoner(self, update_context:Reasoner_Update_Context_Type):
        self.active_reasoner_considerations = []
        self.sub_reasoner = None
        self.entered_sub_reasoner = False

    def update(self, world:World_Type, parent_update_context:Reasoner_Update_Context_Type) -> ReasonerState:
        update_context = copy.deepcopy(parent_update_context)
        update_context = self.sense(world, update_context)
        should_continue = True
        active_reasoner_consideration_failure_context :Optional[Exception] = None
        for current_reasoner_consideration in self.active_reasoner_considerations:
            try:
                should_continue = should_continue and current_reasoner_consideration.is_valid_state(world)
            except ReasonerException as e:
                if active_reasoner_consideration_failure_context is None:
                    active_reasoner_consideration_failure_context = e
                elif isinstance(active_reasoner_consideration_failure_context, ExceptionGroup):
                    inner_exceptions:list[Exception | ExceptionGroup[Exception | Any] | Any] = list(active_reasoner_consideration_failure_context.exceptions)
                    inner_exceptions.append(e)
                    active_reasoner_consideration_failure_context = ExceptionGroup("active reasoner considerations ExceptionGroup for Reasoner " + self.guid,inner_exceptions)
                else:
                    inner_exceptions: list[Exception | ExceptionGroup[Exception | Any] | Any] = list()
                    inner_exceptions.append(active_reasoner_consideration_failure_context)
                    inner_exceptions.append(e)
                    active_reasoner_consideration_failure_context = ExceptionGroup("active reasoner considerations ExceptionGroup for Reasoner " + self.guid, inner_exceptions)
        if not should_continue:
            self.should_null_sub_reasoner = True
            self.handle_active_reasoner_consideration_failure(update_context,active_reasoner_consideration_failure_context)
            if self.should_null_sub_reasoner:
                self.sub_reasoner.exit(update_context)
                self._null_sub_reasoner(update_context)

        if self.sub_reasoner is not None:
            sub_reasoner_state = self.sub_reasoner.update(world, update_context)
            if sub_reasoner_state is ReasonerState.Failed:
                self.should_null_sub_reasoner = True
                self.handle_child_failure(update_context,self.sub_reasoner.failure_context)
            elif sub_reasoner_state is ReasonerState.Done:
                self.should_null_sub_reasoner = True
            if (sub_reasoner_state is not ReasonerState.Running) and self.should_null_sub_reasoner:
                self._null_sub_reasoner(update_context)
        elif self.state == ReasonerState.Running:
            self.sub_reasoner, self.active_reasoner_considerations = self.think(update_context)
        if self.state != ReasonerState.Running:
            self.exit(update_context)
            return self.state
        if self.sub_reasoner is not None:
            if not self.entered_sub_reasoner:
                self.entered_sub_reasoner = True
                try:
                    sub_reasoner_enter_state = self.sub_reasoner.enter(update_context)
                except ReasonerException as e:
                    self.should_null_sub_reasoner = True
                    self.handle_child_enter_failure(update_context,e)
                else:
                    if (sub_reasoner_enter_state is not ReasonerState.Running) and self.should_null_sub_reasoner:
                        self._null_sub_reasoner(update_context)
        else:
            self.act(world,update_context)
        if (self.state == ReasonerState.Failed) or (self.state == ReasonerState.Done):
            self.exit(update_context)
        return self.state

