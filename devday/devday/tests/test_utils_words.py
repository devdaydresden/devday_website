from unittest import TestCase

import mock
from devday.utils.words import Words


def non_random_choice(l):
    return l[0]


class WordsTest(TestCase):
    def test_words(self):
        rng = mock.Mock()
        rng.choice = mock.Mock(side_effect=non_random_choice)
        s = Words.sentence(rng)
        self.assertEqual(
            s,
            "accepting a aboard abandoned aardvark",
            "sentence built from the first word of each list respectively",
        )
