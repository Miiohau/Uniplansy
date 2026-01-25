from abc import ABCMeta, abstractmethod
from typing import List, Iterable

from uniplansy.plans.plan import Plan
from uniplansy.tasks.task_filter import TaskFilter
from uniplansy.tasks.tasks import Task


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