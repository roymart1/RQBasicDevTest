from enum import Enum


class COLOR(Enum):
    """
    Great Enum test

    """
    BLUE = "#0000FF"
    GREEN = "#00FF00"
    RED = "#FF0000"

class Test:
    """
    This is a Test of Test
    """
    def call_me(self, color_enum):
        print(f"COLOR is {color_enum}")
        print(f"COLOR value is {color_enum.value}")
        print(f"COLOR name is {color_enum.name}")

if __name__ == '__main__':
    test = Test()
    test.call_me(COLOR.GREEN)
