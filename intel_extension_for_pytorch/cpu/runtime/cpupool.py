import torch
import functools
import warnings
import numpy as np
import intel_extension_for_pytorch as ipex
from .runtime_utils import get_core_list_of_node_id

class CPUPool(object):
    r"""An abstraction of a pool of CPU cores to be used for intra-op parallelism.
        Args:
            core_ids (list): A list of CPU cores' id used for intra-op parallelism.
            node_id (int): A numa node id with all CPU cores among this numa node. node_id doesn't work if input parameter of core_ids exist.
        Returns:
            CPUPool: New created object with type of CPUPool.
    """
    def __init__(self, core_ids: list = None, node_id: int = None):
        if core_ids is not None:
            if node_id is not None:
                warnings.warn("Both of core_ids and node_id are inputed. core_ids will be used with priority.")
            if type(core_ids) is range:
                core_ids = list(core_ids)
            assert type(core_ids) is list, "Input of core_ids must be the type of list[Int]"
            self.core_ids = core_ids
        else:
            assert node_id is not None, "Neither core_ids or node_id has been implemented"
            self.core_ids = get_core_list_of_node_id(node_id)
        self.cpu_pool = ipex._C.CPUPool(self.core_ids)

class pin(object):
    r"""Apply the given CPU pool to the master thread that runs the scoped code region or the function/method def.
        Args:
            cpu_pool (CPUPool): A object with type CPUPool includes all the CPU cores used by following operations.
        Returns:
            pin: New created object with type of pin which can be used as `with` context or function decorator.
    """
    def __init__(self, cpu_pool: CPUPool):
        self.cpu_pool = cpu_pool
        ipex._C.init_runtime_ext()

    def __enter__(self):
        assert type(self.cpu_pool) is CPUPool
        ipex._C.pin_cpu_cores(self.cpu_pool.core_ids)

    def __exit__(self, *args):
        pass

    # Support decorator
    def __call__(self, func):
        @functools.wraps(func)
        def decorate_pin(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return decorate_pin

def is_runtime_ext_enabled():
    r"""Helper function to check whether runtime extension is enabled or not.
        Args:
            None
        Returns:
            bool: Whether the runtime exetension is enabled or not.
    """
    return ipex._C.is_runtime_ext_enabled() == 1