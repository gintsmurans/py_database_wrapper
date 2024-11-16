from typing import Any, Callable, Type, TypeVar

AnyDataType = TypeVar("AnyDataType", bound=Type[Any])


def ignore_unknown_kwargs() -> Callable[[AnyDataType], AnyDataType]:
    """
    Class decorator factory that modifies the __init__ method to ignore unknown keyword arguments.
    """

    def decorator(cls: AnyDataType) -> AnyDataType:
        originalInit = cls.__init__

        # @wraps(originalInit)
        def newInit(self: Any, *args: Any, **kwargs: Any) -> None:
            # Filter out kwargs that are not properties of the class
            valid_kwargs = {k: v for k, v in kwargs.items() if hasattr(self, k)}
            originalInit(self, *args, **valid_kwargs)

        cls.__init__ = newInit  # type: ignore
        return cls

    return decorator
