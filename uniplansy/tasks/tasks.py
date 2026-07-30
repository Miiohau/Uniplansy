""" contains the core of the Task framework

Task(class): a class that represents a task.
It contains a TaskDescription, cost metrics, motivation and a satisfied_percentage
TaskDescription(class): an immutable description of a task that is safe to reuse across different Plans
TaskFilter(class): a filter that can filter tasks
"""
#TODO: (after upgrading to python 3.12) uncomment @override Decorators
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from fractions import Fraction
from math import isfinite
from typing import Any, Self, Optional, ClassVar, Iterable, Generator, List

from immutabledict import immutabledict

from uniplansy.plans.plan_graph_node import PlanGraphNode
from uniplansy.util.has_uid import HasRequiredUID
from uniplansy.util.id_registry import IDRegistry, id_registry_registry


@dataclass(frozen=True, repr=True)
class TaskDescription(HasRequiredUID):
    """an immutable description of a task that is safe to reuse across different Plans

    uid(attribute): the UID of the task
    human_understandable_string(attribute): a human understandable string of the task
    context(attribute): the context of the task
    """
    uid: str
    human_understandable_string: str
    context: immutabledict[str, Any] = immutabledict({})

    # @override
    def __str__(self) -> str:
        return f"{self.human_understandable_string}"

    # @override
    def __eq__(self, other):
        if isinstance(other, TaskDescription):
            if self.uid == other.uid:
                if __debug__ :
                    assert self.human_understandable_string == other.human_understandable_string, \
                        (f"by guid \"{self.human_understandable_string}\" {self.uid} "
                         f"should equal \"{other.human_understandable_string}\" {self.uid} but "
                         f"they have different human understandable strings")
                    assert self.context == other.context, \
                        (f"by guid \"{self.human_understandable_string}\" \"{self.uid}\" should equal "
                         f"\"{other.human_understandable_string}\" \"{other.uid}\" but "
                         f"\"{self.human_understandable_string}\" has context {self.context} and "
                         f"\"{other.human_understandable_string}\" has context {other.context}")
                return True
            return (self.human_understandable_string == other.human_understandable_string and
                    self.context == other.context)
        return NotImplemented

    # @override
    def __hash__(self) -> int:
        return hash(self.uid)

    # @override
    def __copy__(self):
        return self

    # @override
    def __deepcopy__(self, memo):
        return self

@dataclass(init=False)
class Task(PlanGraphNode):
    """a class that represents a task.

    It contains a TaskDescription, cost metrics, motivation and a satisfied_percentage
    description(attribute): a description of the task
    motivation(attribute): the AI motivation for the task.
    The particular application will define what exactly this means.
    estimated_cost(attribute): the estimated cost needed to complete the task.
    The particular application will define if this the average cost or the median cost.
    min_cost(attribute): the minimum cost needed to complete the task.
    Note: there is no actual need for this to be the minimum cost. This can be a best guess.
    Though in some setups it is best if it is under estimate.
    max_cost(attribute): the maximum cost needed to complete the task.
    Note: there is no actual need for this to be the maximum cost. This can be a best guess.
    satisfied_percentage(attribute): How much the task is already satisfied in the Plan. Should be between 0.0 and 1.0.
    Used to scale the other values when calculating Plan statistics.
    task_description_id_context(attribute): the IDRegistry where the TaskDescription is registered.
    Used when saving and loading plans to the disk.
    get_clamped_satisfied_percentage(method): clamps the satisfied_percentage between two values.
    defaults to between 0.0 and 1.0."""
    description: TaskDescription = field(kw_only=True)
    task_description_id_context: Optional[IDRegistry[TaskDescription]] = field(default=None)
    motivation: float | Fraction = 0.0
    estimated_cost: float | Fraction = 0.0
    min_cost: float | Fraction = 0.0
    max_cost: float | Fraction = float("inf")
    satisfied_percentage: float | Fraction = 0.0

    def __init__(self,
                 uid: str,
                 description: TaskDescription,
                 node_id_context: Optional[IDRegistry[PlanGraphNode]] = None,
                 task_description_id_context: Optional[IDRegistry[TaskDescription]] = None,
                 motivation: float | Fraction = 0.0,
                 estimated_cost: float = 0.0,
                 min_cost: float | Fraction = 0.0,
                 max_cost: float | Fraction = float("inf"),
                 cache_prefix: str = "_cache",
                 *,
                 children: Optional[set[PlanGraphNode]] = None,
                 parents: Optional[set[PlanGraphNode]] = None,
                 ):
        super().__init__(uid=uid,
                         node_id_context=node_id_context,
                         cache_prefix=cache_prefix,
                         children=children,
                         parents=parents)
        self.description = description
        self.task_description_id_context = task_description_id_context
        self.motivation = motivation
        self.estimated_cost = estimated_cost
        self.min_cost = min_cost
        self.max_cost = max_cost

    def get_clamped_satisfied_percentage(self,
                                         min_value: float | Fraction = 0.0,
                                         max_value: float | Fraction = 1.0) -> float | Fraction:
        """TODO: Docstring for get_clamped_satisfied_percentage.

        :param min_value:
        :param max_value:
        :return:
        """
        if isinstance(self.satisfied_percentage, Fraction):
            min_value = Fraction(min_value)
            max_value = Fraction(max_value)
        elif isinstance(self.satisfied_percentage, float):
            min_value = float(min_value)
            max_value = float(max_value)
        return min(max(self.satisfied_percentage, min_value), max_value)

    # @override
    def is_compatible_with(self, other: PlanGraphNode) -> bool:
        if isinstance(other, Task):
            return self.description == other.description
        return NotImplemented

    def could_be_equal(self, other) -> bool:
        if not super().could_be_equal(other):
            return False
        if self.description != other.description:
            return False
        if self.task_description_id_context != other.task_description_id_context:
            return False
        return ((self.motivation == other.motivation) and
                (self.estimated_cost == other.estimated_cost) and
                (self.min_cost == other.min_cost) and
                (self.max_cost == other.max_cost) and
                (self.satisfied_percentage == other.satisfied_percentage))

    def set_matching_deep_copy(self,other:Self,memo):
        super().set_matching_deep_copy(other,memo)
        self.motivation = other.motivation
        self.estimated_cost = other.estimated_cost
        self.min_cost = other.min_cost
        self.max_cost = other.max_cost
        self.satisfied_percentage = other.satisfied_percentage
        self.task_description_id_context = other.task_description_id_context

    def __deepcopy__(self, memo):
        new_copy = type(self)(uid=self.uid, description=self.description)
        self.set_matching_deep_copy(new_copy, memo)
        return new_copy

    def __getstate__(self):
        state = super().__getstate__()
        state['task_description_id_context_id'] = self.task_description_id_context.uid
        del state['task_description_id_context']
        state['description_id'] = self.description.uid
        del state['description']
        return state

    # TODO:see if we can find a way to connect unpickled Tasks to their old notes
    def __setstate__(self,state):
        super().__setstate__(state)
        self.task_description_id_context = id_registry_registry.fetch(state['task_description_id_context_id'])
        del self.__dict__['task_description_id_context_id']
        self.description = self.task_description_id_context.fetch(state['description_id'])
        del self.__dict__['description_id']

    def __str__(self):
        return ("description:" + str(self.description) + " uid:" + str(self.uid) +
                "motivation:" + str(self.motivation) + "estimated_cost:" + str(self.estimated_cost) +
                "min_cost:" + str(self.min_cost) + "max_cost:" + str(self.max_cost) +
                "satisfied_percentage:" + str(self.satisfied_percentage))

    if __debug__:
        NO_SPECIAL_VALUES_ALLOWED_ATTRIBUTES: ClassVar[list[str]] = ['motivation', 'estimated_cost', 'min_cost',
                                                                     'satisfied_percentage']

        def __setattr__(self, name, value):
            if name in Task.NO_SPECIAL_VALUES_ALLOWED_ATTRIBUTES:
                if isinstance(value, float) and not isfinite(value):
                    raise TypeError(f"{value} is not finite. floats assigned to {name} must be finite")
            super().__setattr__(name, value)

class TaskFilter(metaclass=ABCMeta):
    """a filter that can filter tasks

    accept_task(abstractmethod): return true if task is accepted by this filter.
    This is the only method subclasses need to implement.
    filter_tasks_generator(method): filter tasks based on a TaskFilter. Returns a generator of Tasks
    accept_any_task(method): returns true if any of the tasks in tasks are accepted by this filter
    filter_tasks_list(method): filter tasks based on a TaskFilter. Returns a List of Tasks."""

    @abstractmethod
    def accept_task(self, task: Task) -> bool:
        """return true if task is accepted by this filter"""
        pass

    def filter_tasks_generator(self, tasks: Iterable[Task]) -> Generator[Task, None, None]:
        """filter tasks based on a TaskFilter. Returns a generator of Tasks"""
        for task in tasks:
            if not self.accept_task(task):
                yield task

    def accept_any_task(self, tasks: Iterable[Task]) -> bool:
        """returns true if any of the tasks in tasks are accepted by this filter"""
        task_filter = self.filter_tasks_generator(tasks)
        first = next(task_filter, None)
        task_filter.close()
        return first is not None

    def filter_tasks_list(self, tasks: Iterable[Task]) -> List[Task]:
        """filter tasks based on a TaskFilter. Returns a List of Tasks"""
        return list(self.filter_tasks_generator(tasks))