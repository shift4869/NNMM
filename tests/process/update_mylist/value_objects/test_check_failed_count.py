import sys
import unittest

from nnmm.process.update_mylist.value_objects.check_failed_count import CheckFailedCount


class TestCheckFailedCount(unittest.TestCase):
    def test_init(self):
        for count in range(0, 5):
            instance = CheckFailedCount(count)
            self.assertEqual(count, instance._count)

        with self.assertRaises(ValueError):
            instance = CheckFailedCount(-1)
        with self.assertRaises(ValueError):
            instance = CheckFailedCount("invalid_count")


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
