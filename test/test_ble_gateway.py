from ble_gateway import ble_gateway


def test_fib() -> None:
    assert ble_gateway.fib(0) == 0
    assert ble_gateway.fib(1) == 1
    assert ble_gateway.fib(2) == 1
    assert ble_gateway.fib(3) == 2
    assert ble_gateway.fib(4) == 3
    assert ble_gateway.fib(5) == 5
    assert ble_gateway.fib(10) == 55
