from typing import Callable, TypeVar

Message = TypeVar("Message")

SendAlert = Callable[[Message], None]
