import sys
import unittest
from dataclasses import FrozenInstanceError

from NNMM.process.value_objects.textbox_bottom import BottomTextbox


class TestBottomTextbox(unittest.TestCase):
    def test_init(self):
        instance = BottomTextbox("textbox_text")
        self.assertEqual("textbox_text", instance._text)
        instance = BottomTextbox("")
        with self.assertRaises(ValueError):
            instance = BottomTextbox(-1)
        with self.assertRaises(FrozenInstanceError):
            instance = BottomTextbox("textbox_text")
            instance._text = "frozen_error"

    def test_str(self):
        instance = BottomTextbox("textbox_text")
        self.assertEqual("textbox_text", str(instance))

    def test_is_empty(self):
        instance = BottomTextbox("textbox_text")
        self.assertFalse(instance.is_empty())
        instance = BottomTextbox("")
        self.assertTrue(instance.is_empty())

    def test_to_str(self):
        instance = BottomTextbox("textbox_text")
        self.assertEqual("textbox_text", instance.to_str())

    def test_text(self):
        instance = BottomTextbox("textbox_text")
        self.assertEqual("textbox_text", instance.text)

    def test_create(self):
        actual = BottomTextbox.create("textbox_text")
        expect = BottomTextbox("textbox_text")
        self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
