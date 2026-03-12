""" TODO: docString

Constraint(class):A Constraint represents a condition that must remain true for the plan to remain valid
"""
from abc import ABCMeta, abstractmethod

from uniplansy.plans.plan import Plan


class Constraint(metaclass=ABCMeta):
    """A Constraint represents a condition that must remain true for the plan to remain valid"""

    @abstractmethod
    def satisfied(self, plan: Plan):
        """ returns if the Constraint is satisfied.

        :param plan: a pointer to the plan the constraint being checked in the context of
        """
        pass