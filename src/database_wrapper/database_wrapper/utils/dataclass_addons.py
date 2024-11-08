from typing import Any, Callable, Type, TypeVar

T = TypeVar("T", bound=Type[Any])


def ignore_unknown_kwargs() -> Callable[[T], T]:
    """
    Class decorator factory that modifies the __init__ method to ignore unknown keyword arguments.
    """

    def decorator(cls: T) -> T:
        originalInit = cls.__init__

        # @wraps(originalInit)
        def newInit(self: Any, *args: Any, **kwargs: Any):
            # Filter out kwargs that are not properties of the class
            valid_kwargs = {k: v for k, v in kwargs.items() if hasattr(self, k)}
            originalInit(self, *args, **valid_kwargs)

        cls.__init__ = newInit  # type: ignore
        return cls

    return decorator
