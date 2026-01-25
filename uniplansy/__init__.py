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