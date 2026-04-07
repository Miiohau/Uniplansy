"""the root package. Mainly it exists to namespace the other packages

util (package): holds all the classes that aren't tied directly to planning but are used internally by uniplansy.
tasks (package): TODO: fill out
reasoner (package): TODO: fill out
plans (package): TODO: fill out
planner (package): the core package dealing with the classes and Strategies needed to run the planning algorithm
decomposers (package): Decomposers are knowledge experts that can decompose a plan typically by decomposing Tasks within that plan.
"""
#how to do optional dependencies notes
#to select between modules or only expose a module if optional dependency is installed
#try:
#    import dependency
#except ImportError:
#    from my_module_without_dependency import *
#else:
#    from my_module_with_dependency import *

#for internal use only modules
#try:
#    import optimized_module as module_name
#except ImportError:
#    import fallback_module_that_shadows_optimized_module as module_name