from __future__ import annotations
import copy
from abc import abstractmethod, ABCMeta
from builtins import ExceptionGroup
from enum import auto, Enum
from typing import List, Any, Tuple, TypeVar, Optional, Generic
from collections.abc import Iterable, Generator
from dataclasses import dataclass, field
from immutabledict import immutabledict


core_debugging_flag = True


@dataclass(frozen=True, repr=True)
class TaskDescription:
    guid:str
    human_understandable_string:str
    context:immutabledict[str, Any]

    def __str__(self) -> str:
        return f"{self.human_understandable_string}"

    def __eq__(self, other):
        if isinstance(other, TaskDescription):
            if __debug__ and (self.guid == other.guid):
                assert self.human_understandable_string == other.human_understandable_string, f"by guid \"{self.human_understandable_string}\" {self.guid} should equal \"{other.human_understandable_string}\" {self.guid} but they have different human understandable strings"
                assert self.context == other.context, f"by guid \"{self.human_understandable_string}\" \"{self.guid}\" should equal \"{other.human_understandable_string}\" \"{other.guid}\" but \"{self.human_understandable_string}\" has context {self.context} and \"{other.human_understandable_string}\" has context {other.context}"
            return self.guid == other.guid
        return NotImplemented
    
    def __hash__(self) -> int:
        return hash(self.guid)

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

@dataclass
class Task:
    description:TaskDescription
    motivation:float = field(default=0.0)
    estimated_cost: float = field(default=0.0)
    min_cost:float = field(default=0.0)
    max_cost:float = field(default=float("inf"))
    satisfied_percentage:float = field(default=0.0)


class TaskFilter(metaclass=ABCMeta):

    @abstractmethod
    def filter_tasks_generator(self, tasks : Iterable[Task]) -> Generator[Task, None, None]:
        """filter tasks based on a TaskFilter. Returns a generator of Tasks"""
        pass

    def accept_any_task(self, tasks : Iterable[Task]) -> bool:
        """returns true if any of the tasks in tasks are accepted by this filter"""
        task_filter = self.filter_tasks_generator(tasks)
        first = next(task_filter,None)
        task_filter.close()
        return first is not None

    def filter_tasks_list(self, tasks : Iterable[Task]) -> Iterable[Task]:
        """filter tasks based on a TaskFilter. Returns an Iterable of Tasks (usually a list)"""
        return list(self.filter_tasks_generator(tasks))

@dataclass
class Plan:
    guid: str


    def total_motivation(self) -> float:
        """return the total motivation of the plan"""
        pass

    def min_cost(self)  -> float:
        """return the minimum cost of the plan"""
        pass

    def estimated_cost(self) -> float:
        """return the estimated cost of the plan"""
        pass

    def max_cost(self) -> float:
        """return the maximum cost of the plan"""
        pass

    def average_satisfied_percentage(self) -> float:
        """return the average satisfied percentage of the tasks in the plan"""
        pass

    def median_satisfied_percentage(self) -> float:
        """return the median satisfied percentage of the plan"""
        pass

    def unsatisfied_tasks(self) -> List[Task]:
        """return the unsatisfied tasks"""
        pass


    def leaf_tasks(self) -> List[Task]:
        """return the leaf tasks"""
        pass


    def convert_to_executor_graph(self):
        """convert this plan to an executor graph"""
        pass


    def filter_tasks(self, task_filter : TaskFilter) -> List[Task]:
        """filter tasks based on a TaskFilter"""
        pass

class Decomposer(metaclass=ABCMeta):

    @abstractmethod
    def task_filter(self) -> TaskFilter:
        """return the Decomposer's task filter"""
        pass

    def filter_tasks_planed_for(self, task_list : List[Task]) -> Iterable[Task]:
        return self.task_filter().filter_tasks_list(task_list)

    @abstractmethod
    def decompose_tasks(self, plan:Plan) -> List[Plan]:
        """decompose the tasks in plan"""
        pass

class ReasonerConsideration(metaclass=ABCMeta):

    @abstractmethod
    def is_valid_state(self, world) -> bool:
        pass

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

Reasoner_Update_Context_Type = TypeVar('Reasoner_Update_Context_Type')
World_Type = TypeVar('World_Type')

class Reasoner((Generic[Reasoner_Update_Context_Type,World_Type]),metaclass=ABCMeta):
    sub_reasoner:Optional[Reasoner]
    active_reasoner_considerations:List[ReasonerConsideration]
    state:ReasonerState
    should_null_sub_reasoner:bool
    failure_context:Optional[Exception]
    entered_sub_reasoner:bool
    # TODO: rewrite using exceptions and try catch finally blocks
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
        return None

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def sense(self, world:World_Type, update_context:Reasoner_Update_Context_Type) -> Reasoner_Update_Context_Type:
        """updates the internal state of the Reasoner and adds notes to update_context"""
        return update_context

    # noinspection PyUnusedLocal
    def act(self, world:World_Type, update_context:Reasoner_Update_Context_Type):
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

    def null_sub_reasoner(self, update_context:Reasoner_Update_Context_Type):
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
                elif active_reasoner_consideration_failure_context is ExceptionGroup:
                    # noinspection PyTypeChecker
                    active_reasoner_consideration_failure_context_exception_group:ExceptionGroup = active_reasoner_consideration_failure_context
                    inner_exceptions:list[Exception | ExceptionGroup[Exception | Any] | Any] = list(active_reasoner_consideration_failure_context_exception_group.exceptions)
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
                self.null_sub_reasoner(update_context)

        if self.sub_reasoner is not None:
            sub_reasoner_state = self.sub_reasoner.update(world, update_context)
            if sub_reasoner_state is ReasonerState.Failed:
                self.should_null_sub_reasoner = True
                self.handle_child_failure(update_context,self.sub_reasoner.failure_context)
            elif sub_reasoner_state is ReasonerState.Done:
                self.should_null_sub_reasoner = True
            if (sub_reasoner_state is not ReasonerState.Running) and self.should_null_sub_reasoner:
                self.null_sub_reasoner(update_context)
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
                        self.null_sub_reasoner(update_context)
        else:
            self.act(world,update_context)
        if (self.state == ReasonerState.Failed) or (self.state == ReasonerState.Done):
            self.exit(update_context)
        return self.state

class PlanComparisonStrategyToken(Enum):
    motivation_over_min_cost = auto()
    motivation_over_estimated_cost = auto()
    motivation_over_max_cost = auto()
    min_cost_over_motivation = auto()
    estimated_cost_over_motivation = auto()
    max_cost_over_motivation = auto()
    min_cost = auto()
    estimated_cost = auto()
    max_cost = auto()
    motivation = auto()
    satisfied_percentage_average_asc = auto()
    satisfied_percentage_average_des = auto()
    satisfied_percentage_median_asc = auto()
    satisfied_percentage_median_des = auto()

# cost ascending motivation descending
class PlanComparisonStrategy(metaclass=ABCMeta):

    def __init__(self, order: List[PlanComparisonStrategyToken]):
        self.order = order

    def task_to_tuple_key(self, task: Task) -> Tuple:
        keys = []
        for token in self.order:
            if token == PlanComparisonStrategyToken.motivation_over_min_cost:
                try:
                    keys.append(-task.motivation/task.min_cost)
                except ZeroDivisionError:
                    if task.motivation > 0:
                        keys.append(float('-inf'))
                    elif task.motivation < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.motivation_over_estimated_cost:
                try:
                    keys.append(-task.motivation/task.estimated_cost)
                except ZeroDivisionError:
                    if task.motivation > 0:
                        keys.append(float('-inf'))
                    elif task.motivation < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.motivation_over_max_cost:
                try:
                    keys.append(-task.motivation/task.max_cost)
                except ZeroDivisionError:
                    if task.motivation > 0:
                        keys.append(float('-inf'))
                    elif task.motivation < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.min_cost_over_motivation:
                try:
                    keys.append(task.min_cost/task.motivation)
                except ZeroDivisionError:
                    if task.min_cost < 0:
                        keys.append(float('-inf'))
                    elif task.min_cost > 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.estimated_cost_over_motivation:
                try:
                    keys.append(task.estimated_cost/task.motivation)
                except ZeroDivisionError:
                    if task.estimated_cost < 0:
                        keys.append(float('-inf'))
                    elif task.estimated_cost > 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.max_cost_over_motivation:
                try:
                    keys.append(task.max_cost/task.motivation)
                except ZeroDivisionError:
                    if task.max_cost < 0:
                        keys.append(float('-inf'))
                    elif task.max_cost > 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.motivation:
                keys.append(-task.motivation)
            elif token == PlanComparisonStrategyToken.min_cost:
                keys.append(task.min_cost)
            elif token == PlanComparisonStrategyToken.estimated_cost:
                keys.append(task.estimated_cost)
            elif token == PlanComparisonStrategyToken.max_cost:
                keys.append(task.max_cost)
            elif token == PlanComparisonStrategyToken.satisfied_percentage_average_asc:
                keys.append(task.satisfied_percentage)
            elif token == PlanComparisonStrategyToken.satisfied_percentage_median_asc:
                keys.append(task.satisfied_percentage)
            elif token == PlanComparisonStrategyToken.satisfied_percentage_average_des:
                keys.append(-task.satisfied_percentage)
            elif token == PlanComparisonStrategyToken.satisfied_percentage_median_des:
                keys.append(-task.satisfied_percentage)
        # to guarantee a total ordering
        keys.append(task.description.human_understandable_string)
        keys.append(task.description.guid)
        # it actually should be totally ordered by this point but just to make extra sure.
        keys.append(task.__str__())
        keys.append(task.__hash__())
        return tuple(keys)

    def plan_to_tuple_key(self, plan: Plan) -> Tuple:
        keys = []
        for token in self.order:
            if token == PlanComparisonStrategyToken.motivation_over_min_cost:
                try:
                    keys.append(-plan.total_motivation() / plan.min_cost())
                except ZeroDivisionError:
                    if plan.total_motivation() > 0:
                        keys.append(float('-inf'))
                    elif plan.total_motivation() < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.motivation_over_estimated_cost:
                try:
                    keys.append(-plan.total_motivation() / plan.estimated_cost())
                except ZeroDivisionError:
                    if plan.total_motivation() > 0:
                        keys.append(float('-inf'))
                    elif plan.total_motivation() < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.motivation_over_max_cost:
                try:
                    keys.append(-plan.total_motivation() / plan.max_cost())
                except ZeroDivisionError:
                    if plan.total_motivation() > 0:
                        keys.append(float('-inf'))
                    elif plan.total_motivation() < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.min_cost_over_motivation:
                try:
                    keys.append(plan.min_cost() / plan.total_motivation())
                except ZeroDivisionError:
                    if plan.min_cost() < 0:
                        keys.append(float('-inf'))
                    elif plan.min_cost() > 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.estimated_cost_over_motivation:
                try:
                    keys.append(plan.estimated_cost() / plan.total_motivation())
                except ZeroDivisionError:
                    if plan.estimated_cost() < 0:
                        keys.append(float('-inf'))
                    elif plan.estimated_cost() > 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.max_cost_over_motivation:
                try:
                    keys.append(plan.max_cost() / plan.total_motivation())
                except ZeroDivisionError:
                    if plan.max_cost() < 0:
                        keys.append(float('-inf'))
                    elif plan.max_cost() > 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.motivation:
                keys.append(-plan.total_motivation())
            elif token == PlanComparisonStrategyToken.min_cost:
                keys.append(plan.min_cost())
            elif token == PlanComparisonStrategyToken.estimated_cost:
                keys.append(plan.estimated_cost())
            elif token == PlanComparisonStrategyToken.max_cost:
                keys.append(plan.max_cost())
            elif token == PlanComparisonStrategyToken.satisfied_percentage_average_asc:
                keys.append(plan.average_satisfied_percentage())
            elif token == PlanComparisonStrategyToken.satisfied_percentage_median_asc:
                keys.append(plan.median_satisfied_percentage())
            elif token == PlanComparisonStrategyToken.satisfied_percentage_average_des:
                keys.append(-plan.average_satisfied_percentage())
            elif token == PlanComparisonStrategyToken.satisfied_percentage_median_des:
                keys.append(-plan.median_satisfied_percentage())
        # to guarantee a total ordering
        keys.append(plan.guid)
        # it actually should be totally ordered by this point but just to make extra sure.
        keys.append(plan.__str__())
        keys.append(plan.__hash__())
        return tuple(keys)