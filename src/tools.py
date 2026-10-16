# 2. Create python tools

def validate_numbers(a: float, b: float) -> None:
    if isinstance(a, bool) or not isinstance(a, (int, float)):
        raise TypeError("a must be a number")

    if isinstance(b, bool) or not isinstance(b, (int, float)):
        raise TypeError("b must be a number")


def add_numbers(a: float, b: float) -> float:
    """Add two numbers and return their sum."""
    validate_numbers(a, b)
    return a + b


def multiply_numbers(a: float, b: float) -> float:
    """Multiply two numbers and return their product."""
    validate_numbers(a, b)
    return a * b