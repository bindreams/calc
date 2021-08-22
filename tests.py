import unittest
import doctest
import math
import statistics

import calc as calcmodule
from calc import calc

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(calcmodule))
    return tests

class TestEval(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(calc("9"), 9)
        self.assertEqual(calc("9 + 3 + 6"), 9 + 3 + 6)
        self.assertEqual(calc("9 + 3 / 11"), 9 + 3.0 / 11)
        self.assertEqual(calc("(9 + 3)"), (9 + 3))
        self.assertEqual(calc("9 - 12 - 6"), 9 - 12 - 6)
        self.assertEqual(calc("2^3^2"), 2 ** 3 ** 2)
        self.assertEqual(calc("2^9"), 2 ** 9)
    
    def test_float(self):
        self.assertEqual(calc("2*3.14159"), 2 * 3.14159)
        self.assertEqual(calc("3.1415926535*3.1415926535 / 10"), 3.1415926535 * 3.1415926535 / 10)
        self.assertEqual(calc("6.02E23 * 8.048"), 6.02e23 * 8.048)
        self.assertEqual(calc(".02e23 * 8."), .02e23 * 8.)

    def test_order_of_operations(self):
        self.assertEqual(calc("(9+3) / 11"), (9 + 3.0) / 11)
        self.assertEqual(calc("9 - (12 - 6)"), 9 - (12 - 6))
        self.assertEqual(calc("(2^3)^2"), (2 ** 3) ** 2)
        self.assertEqual(calc("2^(1-3)"), 2 ** (1 - 3))
        self.assertEqual(calc("2^3+2"), 2 ** 3 + 2)
        self.assertEqual(calc("2^3+5"), 2 ** 3 + 5)

    def test_unary_operators(self):
        self.assertEqual(calc("-9"), -9)
        self.assertEqual(calc("+9"), 9)
        self.assertEqual(calc("--9"), 9)
        self.assertEqual(
            calc("a1b", unary_operators={
                ("a", "prefix"): lambda x: x*2, 
                ("b", "postfix"): lambda x: x+1, 
            }),
            4
        )

    def test_functions(self):
        self.assertEqual(
            calc("sin(0)", {"sin": math.sin}), 0)
        self.assertEqual(
            calc("0 + first(-1+19, 2^2, 3 + 4)", {"first": lambda a, b, c: a}), -1+19)
        self.assertEqual(
            calc("last(-1+19, 2^2, 3 + 4)", {"last": lambda a, b, c: c}), 3 + 4)
        self.assertEqual(
            calc("1 * mean(-1+19, 2^2, 3 + 4)", {"mean": lambda *args: statistics.mean(args)}),
            statistics.mean([-1+19, 2**2, 3 + 4]))
        self.assertEqual(
            calc("max_(1)", {"max": 0, "max_": lambda x: x}), 1)

    def test_variables(self):
        self.assertEqual(calc("x", {"x": 1}), 1)
        self.assertEqual(calc("x + x^x * x", {"x": 1}), 2)
        self.assertEqual(calc("x", {"x": 1, "x_": 2}), 1)
        self.assertEqual(calc("x_", {"x": 1, "x_": 2}), 2)

if __name__ == '__main__':
    unittest.main()
