"""
Provides a dataclass for shared variables across server processes
"""
from dataclasses import dataclass
from multiprocessing import Barrier, Value


@dataclass
class SharedVariables:
    """Shared variables used across the server processes"""

    compute_barrier: Barrier
    write_barrier: Barrier
    price_shared: Value
    weather_shared: Value
