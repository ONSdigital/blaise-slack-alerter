from lib.log_processor.utilities import (apply_argument, apply_argument_to_all,
                                         first_successful)


class TestFirstSuccessful:
    def test_it_returns_none_for_empty_list(self):
        assert first_successful([]) is None

    def test_it_returns_none_if_all_factories_return_none(self):
        assert first_successful([lambda: None, lambda: None]) is None

    def test_it_returns_the_first_successful_result(self):
        assert first_successful([lambda: None, lambda: 1, lambda: 2]) == 1


class TestApplyArgumentToAll:
    def test_it_returns_a_list_of_functions_with_the_argument_applied(self):
        fs = [
            lambda arg: arg + 2,
            lambda arg: arg + 3,
        ]

        new_fs = apply_argument_to_all(fs, 5)

        assert [f() for f in new_fs] == [7, 8]


class TestApplyArgument:
    def test_it_returns_a_function_with_the_argument_already_applied(self):
        def f(arg: int) -> int:
            return arg + 2

        applied_f = apply_argument(f, 5)

        assert applied_f() == 7
