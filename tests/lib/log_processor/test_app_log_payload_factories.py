from lib.log_processor import apply_argument_to_all


def test_apply_argument_to_all_returns_a_list_of_functions_with_the_argument_applied():
    fs = [
        lambda arg: arg + 2,
        lambda arg: arg + 3,
    ]

    new_fs = apply_argument_to_all(fs, 5)

    assert [f() for f in new_fs] == [7, 8]
