from typing import List, Callable, Optional, TypeVar

Arg = TypeVar("Arg")
Return = TypeVar("Return")


def first_successful(
    factories: List[Callable[[], Optional[Return]]]
) -> Optional[Return]:
    for create in factories:
        result = create()
        if result is not None:
            return result
    return None


def apply_argument_to_all(
    fs: List[Callable[[Arg], Return]], argument: Arg
) -> List[Callable[[], Return]]:
    return [apply_argument(create, argument) for create in fs]


def apply_argument(f: Callable[[Arg], Return], argument: Arg) -> Callable[[], Return]:
    return lambda: f(argument)
