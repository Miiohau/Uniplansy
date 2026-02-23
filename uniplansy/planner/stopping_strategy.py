from abc import ABCMeta, abstractmethod

from uniplansy.planner.core import PlanningContext


class StoppingStrategy(metaclass=ABCMeta):

    @abstractmethod
    def should_stop(self, context: PlanningContext) -> bool:
        """returns True if planning should stop

        :param context: the planning context
        """
        pass