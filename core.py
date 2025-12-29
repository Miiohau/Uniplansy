from __future__ import annotations
import copy
from abc import abstractmethod, ABCMeta
from enum import auto, Enum
from typing import List, Any
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
            if self.guid == other.guid:
                assert self.human_understandable_string == other.human_understandable_string, f"by guid \"{self.human_understandable_string}\" should equal \"{other.human_understandable_string}\" but they have different human understandable strings"
                assert self.context == other.context, f"by guid {self.human_understandable_string} should equal {other.human_understandable_string} but \"{self.human_understandable_string}\" has context {self.context} and \"{other.human_understandable_string}\" has context {other.context}"
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
    priority:float = field(default=0.0)
    estimated_cost: float = field(default=0.0)
    min_cost:float = field(default=0.0)
    max_cost:float = field(default=float("inf"))
    satisfied_percentage:float = field(default=0.0)


class TaskFilter(metaclass=ABCMeta):

    @abstractmethod
    def filter_tasks_generator(self, tasks : Iterable[TaskDescription]) -> Generator[TaskDescription, None, None]:
        """filter tasks based on a TaskFilter. Returns a generator of Tasks"""
        pass

    def accept_any_task(self, tasks : Iterable[TaskDescription]) -> bool:
        """returns true if any of the tasks in tasks are accepted by this filter"""
        task_filter = self.filter_tasks_generator(tasks)
        first = next(task_filter)
        task_filter.close()
        return first is not None

    def filter_tasks_list(self, tasks : Iterable[TaskDescription]) -> Iterable[TaskDescription]:
        """filter tasks based on a TaskFilter. Returns an Iterable of Tasks (usually a list)"""
        return list(self.filter_tasks_generator(tasks))


class Plan(metaclass=ABCMeta):

    @abstractmethod
    def min_cost(self)  -> float:
        """return the minimum cost of the plan"""
        pass

    @abstractmethod
    def estimated_cost(self) -> float:
        """return the estimated cost of the plan"""
        pass

    @abstractmethod
    def unsatisfied_tasks(self) -> List[TaskDescription]:
        """return the unsatisfied tasks"""
        pass

    @abstractmethod
    def leaf_tasks(self) -> List[TaskDescription]:
        """return the leaf tasks"""
        pass

    @abstractmethod
    def convert_to_executor_graph(self):
        """convert this plan to an executor graph"""
        pass

    @abstractmethod
    def filter_tasks(self, task_filter : TaskFilter) -> List[TaskDescription]:
        """filter tasks based on a TaskFilter"""
        pass



class Decomposer(metaclass=ABCMeta):

    @abstractmethod
    def task_filter(self) -> TaskFilter:
        """return the Decomposer's task filter"""
        pass

    @abstractmethod
    def filter_tasks_planed_for(self, task_list : List[TaskDescription]) -> List[TaskDescription]:
        """filter task_list based on the tasks that can be planned for by this Decomposer"""
        pass

    @abstractmethod
    def decompose_tasks(self, plan:Plan) -> List[Plan]:
        """decompose the tasks in plan"""
        pass

class ReasonerConsideration(metaclass=ABCMeta):

    @abstractmethod
    def is_valid_state(self, world) -> bool:
        pass

class ReasonerState(Enum):
    Running = auto()
    Done = auto()
    Failed = auto()

class Reasoner(metaclass=ABCMeta):

    def __init__(self):
        self.active_reasoner_considerations = []
        self.sub_reasoner = None
        self.state = ReasonerState.Running

    @abstractmethod
    def think(self, update_context):
        pass

    @abstractmethod
    def sense(self, world, update_context):
        """updates the internal state of the Reasoner and adds notes to update_context"""
        return update_context

    @abstractmethod
    def act(self, world, update_context):
        pass

    @abstractmethod
    def exit(self, update_context):
        """tells the Reasoner to clean up and exit"""
        if self.sub_reasoner is not None:
            self.sub_reasoner.exit(update_context)
            self.active_reasoner_considerations = []
            self.sub_reasoner = None
        if self.state == ReasonerState.Running:
            self.state = ReasonerState.Done

    @abstractmethod
    def handle_active_reasoner_consideration_failure(self, update_context):
        pass

    @abstractmethod
    def handle_child_failure(self, update_context):
        pass

    def update(self, world, parent_update_context) -> ReasonerState:
        update_context = copy.deepcopy(parent_update_context)
        update_context = self.sense(world, update_context)
        should_continue = True
        for current_reasoner_consideration in self.active_reasoner_considerations:
            should_continue = should_continue and current_reasoner_consideration.is_valid_state(world)
        if not should_continue:
            self.handle_active_reasoner_consideration_failure(update_context)
            self.sub_reasoner.exit(update_context)
            self.active_reasoner_considerations = []
            self.sub_reasoner = None
        if self.sub_reasoner is not None:
            sub_reasoner_state = self.sub_reasoner.update(world, update_context)
            if sub_reasoner_state is ReasonerState.Failed:
                self.handle_child_failure(update_context)
            if sub_reasoner_state is not ReasonerState.Running:
                self.active_reasoner_considerations=[]
                self.sub_reasoner = None
        elif self.state == ReasonerState.Running:
            self.sub_reasoner, self.active_reasoner_considerations = self.think(update_context)
        if self.state != ReasonerState.Running:
            self.exit(update_context)
            return self.state
        if self.sub_reasoner is None:
            self.act(world,update_context)
        if (self.state == ReasonerState.Failed) or (self.state == ReasonerState.Done):
            self.exit(update_context)
        return self.state