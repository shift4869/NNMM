from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class UpperTextbox():
    _text: str

    def __post_init__(self) -> None:
        """空文字列は許容する
        """
        if not isinstance(self._text, str):
            raise ValueError("textbox must be str.")

    def __str__(self) -> str:
        return self._text

    def is_empty(self) -> bool:
        return self._text == ""

    def to_str(self) -> str:
        return self._text

    @property
    def text(self):
        return self._text

    @classmethod
    def create(cls, input_text: str) -> Self:
        """上部のテキストボックスに入力されている文字列を扱う

        Args:
            input_text (str): 
                上部のテキストボックスに入力されている文字列
                主に values["-INPUT1-"] を受け取る

        Returns:
            Self: UpperTextbox インスタンス
        """        
        return cls(input_text)


if __name__ == "__main__":
    text = "test"
    textbox = UpperTextbox(text)
    print(textbox)
    print(textbox.is_empty())

    text = ""
    textbox = UpperTextbox(text)
    print(textbox)
    print(textbox.is_empty())
