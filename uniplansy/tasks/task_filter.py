from abc import ABCMeta, abstractmethod
from typing import Iterable, Generator, List

from uniplansy.tasks.tasks import Task


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