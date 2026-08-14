"""contains errors related to plans

CyclicPlanError(ValueError): an error raised when a plan when a cyclical graph is passed where one when
an acyclic graph is expected
"""


class CyclicPlanError(ValueError):
    """an error raised when a plan when a cyclical graph is passed where one when an acyclic graph is expected"""
    pass