

class Square:
    """
    Vive les squares!
    """
    def __init__(self):
        pass

    def set_color(self, name):
        """
        Set the color
        :param name: color name to be use for testing
        :return:
        """
        print("Allo " + name)


if __name__ == '__main__':
    pObj = Square()
    pObj.set_color("Mike")

