from collections import Counter

from rectifier.get_random_key import get_random_key


def test_rotating_keys():
    keys = [get_random_key(['a', 'b', 'c']) for _ in range(0, 100)]
    most_common_element_occurrences = Counter(keys).most_common(1)[0][1]
    assert most_common_element_occurrences != 100


def test_rotating_keys_no_elements():
    assert get_random_key([]) is None
    assert get_random_key(None) is None
