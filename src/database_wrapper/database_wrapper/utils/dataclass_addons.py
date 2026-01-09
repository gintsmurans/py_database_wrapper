from collections.abc import Callable
from typing import Any, TypeVar

AnyDataType = TypeVar("AnyDataType", bound=type[Any])


def ignore_unknown_kwargs() -> Callable[[AnyDataType], AnyDataType]:
    """
    Class decorator factory that modifies the __init__ method to ignore unknown keyword arguments.
    """

    def decorator(cls: AnyDataType) -> AnyDataType:
        original_init = cls.__init__

        # @wraps(original_init)
        def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
            # Filter out kwargs that are not properties of the class
            valid_kwargs = {k: v for k, v in kwargs.items() if hasattr(self, k)}
            original_init(self, *args, **valid_kwargs)

        cls.__init__ = new_init
        return cls

    return decorator
