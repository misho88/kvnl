class Corruption(Exception):
    pass


class MalformedSpecification(Corruption):
    pass


class HashMismatch(Corruption):
    def __init__(self, actual, expected):
        super().__init__(f'expected {expected}, got {actual}')
