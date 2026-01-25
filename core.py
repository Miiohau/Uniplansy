from __future__ import annotations
import copy
import statistics
from abc import abstractmethod, ABCMeta
from builtins import ExceptionGroup
from copy import deepcopy
from enum import auto, Enum
from typing import List, Any, Tuple, TypeVar, Optional, Generic
from collections.abc import Iterable, Generator
from dataclasses import dataclass, FrozenInstanceError, field
from immutabledict import immutabledict


core_debugging_flag = True

class FreezableObject:
    """an object that can be frozen and unfrozen. The """
    frozen: bool = False

    def freeze(self):
        """freeze the object. Meaning it is protected from modification"""
        self.frozen = True

    def unfreeze(self):
        """unfreeze the object. Meaning it is no longer protected from modification"""
        self.frozen = False

    def thaw(self):
        """alias for unfreeze. Subclasses should override that method, if they need to change the unfreeze behavior."""
        self.unfreeze()

    def deep_copy_and_unfreeze(self):
        """deep copy and unfreezes the copy of the FreezableObject. Always safe because a deep copy should be completely independent of the original object"""
        new_copy = deepcopy(self)
        new_copy.unfreeze()
        return new_copy

    def __setattr__(self, name, value):
        if self.frozen:
            raise FrozenInstanceError()
        super().__setattr__(name, value)

    def __delattr__(self, name):
        if self.frozen:
            raise FrozenInstanceError()
        super().__delattr__(name)

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
class PlanGraphNode(FreezableObject):
    children:set[PlanGraphNode] = field(default_factory=set, kw_only=True)
    parents: set[PlanGraphNode] = field(default_factory=set, kw_only=True)
    frozen_children:Optional[frozenset[PlanGraphNode]] = field(default=None, init=False)
    frozen_parents:Optional[frozenset[PlanGraphNode]] = field(default=None, init=False)

    def __getattribute__(self, name):
        if not self.frozen:
            return super().__getattribute__(name)
        elif name == "children":
            if self.frozen_children is None:
                self.frozen_children = frozenset(super().__getattribute__(name))
            return self.frozen_children
        elif name == "parents":
            if self.frozen_parents is None:
                self.frozen_parents = frozenset(super().__getattribute__(name))
            return self.frozen_parents
        else:
            return super().__getattribute__(name)

    def unfreeze(self):
        super().unfreeze()
        self.frozen_children = None
        self.frozen_parents = None

@dataclass
class Task(PlanGraphNode):
    description:TaskDescription
    motivation:float = 0.0
    estimated_cost: float = 0.0
    min_cost:float = 0.0
    max_cost:float = float("inf")
    satisfied_percentage:float = 0.0

    def get_clamped_satisfied_percentage(self,min_value:float,max_value:float):
        return min(max(self.satisfied_percentage,min_value),max_value)

@dataclass
class DecomposerNode(PlanGraphNode):
    node_decomposer:Decomposer

    def __deepcopy__(self, memo):
        return DecomposerNode(children=deepcopy(self.children,memo), parents=deepcopy(self.parents,memo),node_decomposer=self.node_decomposer)

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

    def filter_tasks_list(self, tasks : Iterable[Task]) -> List[Task]:
        """filter tasks based on a TaskFilter. Returns a List of Tasks"""
        return list(self.filter_tasks_generator(tasks))

@dataclass(init=True,repr=True,eq=True)
class Plan(FreezableObject):
    tasks_by_GUID:dict[str,Task]
    decomposer_id_to_DecomposerNodes:dict[str,DecomposerNode]
    node_dump:set[PlanGraphNode]

    def total_motivation(self) -> float:
        """return the total motivation of the plan"""
        total:float = 0
        for cur_task in self.tasks_by_GUID.values():
            total += (cur_task.motivation * (1-cur_task.get_clamped_satisfied_percentage(0,1)))
        return total

    def min_cost(self)  -> float:
        """return the minimum cost of the plan"""
        total: float = 0
        for cur_task in self.tasks_by_GUID.values():
            total += (cur_task.min_cost * (1 - cur_task.get_clamped_satisfied_percentage(0, 1)))
        return total

    def estimated_cost(self) -> float:
        """return the estimated cost of the plan"""
        total: float = 0
        for cur_task in self.tasks_by_GUID.values():
            total += (cur_task.estimated_cost * (1 - cur_task.get_clamped_satisfied_percentage(0, 1)))
        return total

    def max_cost(self) -> float:
        """return the maximum cost of the plan"""
        total: float = 0
        for cur_task in self.tasks_by_GUID.values():
            total += (cur_task.estimated_cost * (1 - cur_task.get_clamped_satisfied_percentage(0, 1)))
        return total

    def average_satisfied_percentage(self) -> float:
        """return the average satisfied percentage of the tasks in the plan"""
        total: float = 0
        for cur_task in self.tasks_by_GUID.values():
            total += cur_task.satisfied_percentage
        return total / len(self.tasks_by_GUID)

    def median_satisfied_percentage(self) -> float:
        """return the median satisfied percentage of the plan"""
        satisfied_percentage_values: list[float] = []
        for cur_task in self.tasks_by_GUID.values():
            satisfied_percentage_values.append(cur_task.satisfied_percentage)
        return statistics.median(satisfied_percentage_values)

    def unsatisfied_tasks(self) -> List[Task]:
        """return the unsatisfied tasks"""
        r_values: list[Task] = []
        for cur_task in self.tasks_by_GUID.values():
            if cur_task.satisfied_percentage <= 1:
                r_values.append(cur_task)
        return r_values

    def leaf_tasks(self) -> List[Task]:
        """return the leaf tasks"""
        r_values: list[Task] = []
        for cur_task in self.tasks_by_GUID.values():
            if len(cur_task.children) == 0:
                r_values.append(cur_task)
        return r_values


    def convert_to_reasoner_graph(self):
        """convert this plan to a reasoner graph"""
        #TODO: Implement
        pass


    def filter_tasks(self, task_filter : TaskFilter) -> List[Task]:
        """filter tasks based on a TaskFilter"""
        return list(task_filter.filter_tasks_list(self.tasks_by_GUID.values()))

    def add_node(self, new_node: PlanGraphNode) -> bool:
        """add a task to this plan. Returns true if the node wasn't already in the plan"""
        if self.frozen:
            raise FrozenInstanceError()
        if isinstance(new_node,Task):
            if not new_node.description.guid in self.tasks_by_GUID:
                self.tasks_by_GUID[new_node.description.guid] = new_node
                self._add_node_recurse(new_node)
                return True
        elif isinstance(new_node,DecomposerNode):
            if not new_node.node_decomposer.id in self.decomposer_id_to_DecomposerNodes:
                self.decomposer_id_to_DecomposerNodes[new_node.node_decomposer.id] = new_node
                self._add_node_recurse(new_node)
                return True
        else:
            if not new_node in self.node_dump:
                self.node_dump.add(new_node)
                self._add_node_recurse(new_node)
                return True
        return False

    def _add_node_recurse(self, new_node: PlanGraphNode):
        """add a task to this plan"""
        for cur_parent in new_node.parents:
            if not new_node in cur_parent.children:
                cur_parent.children.add(new_node)
            self.add_node(cur_parent)
        for cur_child in new_node.children:
            if not new_node in cur_child.parents:
                cur_child.parents.add(new_node)
            self.add_node(cur_child)

    def freeze(self):
        """freeze the plan. Meaning it is protected from modification"""
        for node in self.node_dump:
            node.freeze()
        for node in self.decomposer_id_to_DecomposerNodes.values():
            node.freeze()
        for node in self.tasks_by_GUID.values():
            node.freeze()
        super().freeze()

    def unfreeze(self):
        """unfreeze the plan. Meaning it is no longer protected from modification"""
        super().unfreeze()
        for node in self.node_dump:
            node.unfreeze()
        for node in self.decomposer_id_to_DecomposerNodes.values():
            node.unfreeze()
        for node in self.tasks_by_GUID.values():
            node.unfreeze()

class Decomposer(metaclass=ABCMeta):
    id:str

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

Reasoner_Update_Context_Type = TypeVar('Reasoner_Update_Context_Type')
World_Type = TypeVar('World_Type')

class ReasonerConsideration(Generic[World_Type],metaclass=ABCMeta):

    @abstractmethod
    def is_valid_state(self, world:World_Type) -> bool:
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

    # noinspection PyUnusedLocal
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
        #keys.append(plan.guid)
        # it actually should be totally ordered by this point but just to make extra sure.
        keys.append(plan.__str__())
        keys.append(plan.__hash__())
        return tuple(keys)