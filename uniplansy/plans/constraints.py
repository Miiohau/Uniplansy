""" TODO: docString

Constraint(class):A Constraint represents a condition that must remain true for the plan to remain valid
"""
from abc import ABCMeta, abstractmethod

from uniplansy.plans.plan import Plan
from uniplansy.util.global_type_vars import World_Type


class Constraint(metaclass=ABCMeta):
    """A Constraint represents a condition that must remain true for the plan to remain valid"""

    @abstractmethod
    def satisfied(self, plan: Plan, world: World_Type):
        """ returns if the Constraint is satisfied.

        :param world: the world context to check the constraint in
        :param plan: a pointer to the plan the constraint being checked in the context of
        """
        pass