"""
Randomness Budget Enforcement

Enforces the rule that:
- Computed modules: NO RNG calls allowed (raises on violation)
- Control/phase3_synthesis modules: RNG allowed but seed MUST be recorded

This prevents accidental non-reproducibility in analytical code paths.
"""

import functools
import logging
import random
import threading
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, TypeVar

logger = logging.getLogger(__name__)


class RandomnessViolationError(Exception):
    """Raised when RNG is used in a no-randomness context."""
    def __init__(self, context: str, caller: str = ""):
        self.context = context
        self.caller = caller
        super().__init__(
            f"RANDOMNESS VIOLATION: Random call in '{context}' context. "
            f"Computed code paths must be deterministic. Caller: {caller}"
        )


@dataclass
class SeedRecord:
    """Record of a seed used for randomness."""
    module: str
    seed: int
    timestamp: datetime
    purpose: str = ""


class RandomnessController:
    """
    Controls and tracks randomness usage.

    Modes:
    - FORBIDDEN: No RNG calls allowed (raises exception)
    - SEEDED: RNG allowed but seed must be registered
    - UNRESTRICTED: Any RNG allowed (legacy mode, not recommended)
    """

    FORBIDDEN = "forbidden"
    SEEDED = "seeded"
    UNRESTRICTED = "unrestricted"

    _instance: Optional["RandomnessController"] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._thread_local = threading.local()
        self._seed_log: list[SeedRecord] = []
        self._original_random = random.random
        self._original_randint = random.randint
        self._original_uniform = random.uniform
        self._original_choice = random.choice
        self._original_shuffle = random.shuffle
        self._patched = False

    def _get_mode(self) -> str:
        """Get current thread's randomness mode."""
        return getattr(self._thread_local, "mode", self.FORBIDDEN)

    def _set_mode(self, mode: str):
        """Set current thread's randomness mode."""
        self._thread_local.mode = mode

    def _get_context(self) -> str:
        """Get current thread's context name."""
        return getattr(self._thread_local, "context", "unknown")

    def _set_context(self, context: str):
        """Set current thread's context name."""
        self._thread_local.context = context

    def _check_allowed(self) -> None:
        """Check if random calls are allowed; raise if not."""
        mode = self._get_mode()
        if mode == self.FORBIDDEN:
            raise RandomnessViolationError(
                context=self._get_context(),
            )

    def patch_random_module(self):
        """
        Patch the random module to enforce randomness control.

        Call this early in your application startup.
        """
        if self._patched:
            return

        controller = self

        def guarded_random():
            controller._check_allowed()
            return controller._original_random()

        def guarded_randint(a, b):
            controller._check_allowed()
            return controller._original_randint(a, b)

        def guarded_uniform(a, b):
            controller._check_allowed()
            return controller._original_uniform(a, b)

        def guarded_choice(seq):
            controller._check_allowed()
            return controller._original_choice(seq)

        def guarded_shuffle(x, random_func=None):
            """Wrapper around ``random.shuffle``. Mutates ``x`` in-place."""
            controller._check_allowed()
            return controller._original_shuffle(x, random_func)

        random.random = guarded_random
        random.randint = guarded_randint
        random.uniform = guarded_uniform
        random.choice = guarded_choice
        random.shuffle = guarded_shuffle

        self._patched = True

    def unpatch_random_module(self):
        """Restore original random module functions."""
        if not self._patched:
            return

        random.random = self._original_random
        random.randint = self._original_randint
        random.uniform = self._original_uniform
        random.choice = self._original_choice
        random.shuffle = self._original_shuffle

        self._patched = False

    def register_seed(self, module: str, seed: int, purpose: str = ""):
        """
        Register a seed for provenance tracking.

        Required when in SEEDED mode.
        """
        record = SeedRecord(
            module=module,
            seed=seed,
            timestamp=datetime.utcnow(),
            purpose=purpose,
        )
        self._seed_log.append(record)
        return seed

    def get_seed_log(self) -> list[SeedRecord]:
        """Get all registered seeds."""
        return list(self._seed_log)

    def clear_seed_log(self):
        """Clear the seed log (for testing)."""
        self._seed_log.clear()

    @contextmanager
    def forbidden_context(self, name: str):
        """
        Context where NO randomness is allowed.

        Use for computed/analytical code paths.
        """
        old_mode = self._get_mode()
        old_context = self._get_context()

        self._set_mode(self.FORBIDDEN)
        self._set_context(name)
        try:
            yield
        finally:
            self._set_mode(old_mode)
            self._set_context(old_context)

    @contextmanager
    def seeded_context(self, name: str, seed: int, purpose: str = ""):
        """
        Context where randomness is allowed with a registered seed.

        Use for control generation, synthetic data, etc.
        """
        old_mode = self._get_mode()
        old_context = self._get_context()

        self.register_seed(name, seed, purpose)
        random.seed(seed)

        self._set_mode(self.SEEDED)
        self._set_context(name)
        try:
            yield
        finally:
            self._set_mode(old_mode)
            self._set_context(old_context)

    @contextmanager
    def unrestricted_context(self):
        """
        Context where any randomness is allowed.

        Use for legacy code or where seeding is not yet implemented.
        """
        old_mode = self._get_mode()
        self._set_mode(self.UNRESTRICTED)
        try:
            yield
        finally:
            self._set_mode(old_mode)


# Global controller instance
_controller = RandomnessController()


def get_randomness_controller() -> RandomnessController:
    """Get the global randomness controller."""
    return _controller


# Decorator for computed functions (no randomness allowed)
F = TypeVar("F", bound=Callable[..., Any])


def no_randomness(func: F) -> F:
    """
    Decorator that enforces no randomness in a function.

    Use on computed/analytical functions to ensure determinism.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        controller = get_randomness_controller()
        with controller.forbidden_context(func.__qualname__):
            return func(*args, **kwargs)
    return wrapper  # type: ignore


def requires_seed(seed_param: str = "seed"):
    """
    Decorator for functions that require a seed parameter.

    Use on phase3_synthesis/control generation functions.

    Args:
        seed_param: Name of the seed parameter in the function signature.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract seed from kwargs or args
            seed = kwargs.get(seed_param)
            if seed is None:
                raise ValueError(
                    f"Function {func.__qualname__} requires '{seed_param}' parameter "
                    "for reproducibility. Pass an explicit seed."
                )

            controller = get_randomness_controller()
            with controller.seeded_context(func.__qualname__, seed, "function call"):
                return func(*args, **kwargs)
        return wrapper  # type: ignore
    return decorator
