import sys
import unittest
from dataclasses import FrozenInstanceError

from NNMM.process.value_objects.textbox_upper import UpperTextbox


class TestUpperTextbox(unittest.TestCase):
    def test_init(self):
        instance = UpperTextbox("textbox_text")
        self.assertEqual("textbox_text", instance._text)
        instance = UpperTextbox("")
        with self.assertRaises(ValueError):
            instance = UpperTextbox(-1)
        with self.assertRaises(FrozenInstanceError):
            instance = UpperTextbox("textbox_text")
            instance._text = "frozen_error"

    def test_str(self):
        instance = UpperTextbox("textbox_text")
        self.assertEqual("textbox_text", str(instance))

    def test_is_empty(self):
        instance = UpperTextbox("textbox_text")
        self.assertFalse(instance.is_empty())
        instance = UpperTextbox("")
        self.assertTrue(instance.is_empty())

    def test_to_str(self):
        instance = UpperTextbox("textbox_text")
        self.assertEqual("textbox_text", instance.to_str())

    def test_text(self):
        instance = UpperTextbox("textbox_text")
        self.assertEqual("textbox_text", instance.text)

    def test_create(self):
        actual = UpperTextbox.create("textbox_text")
        expect = UpperTextbox("textbox_text")
        self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
