from app.agent import calculate, get_current_time


def test_calculate_basic() -> None:
    result = calculate("15 * 24 + 100")
    assert "Result: 460" in result


def test_calculate_functions() -> None:
    result = calculate("sqrt(144) + pow(2, 3)")
    assert "Result: 20.0" in result


def test_calculate_error() -> None:
    result = calculate("invalid_var + 10")
    assert "Error evaluating expression" in result


def test_get_current_time() -> None:
    result = get_current_time("Tokyo")
    assert "Tokyo" in result
    assert "Asia/Tokyo" in result
