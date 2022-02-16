import unittest
import doctest
import math
import statistics

import calc as calcmodule
from calc import calc, default_identifiers, default_unary_operators, default_binary_operators

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(calcmodule))
    return tests

class TestEval(unittest.TestCase):
    def test_default(self):
        self.assertEqual(calc("9"), 9)
        self.assertEqual(calc("9 + 3 + 6"), 9 + 3 + 6)
        self.assertEqual(calc("9 + 3 / 11"), 9 + 3.0 / 11)
        self.assertEqual(calc("(9 + 3)"), (9 + 3))
        self.assertEqual(calc("9 - 12 - 6"), 9 - 12 - 6)
        self.assertEqual(calc("2^3^2"), 2 ** 3 ** 2)
        self.assertEqual(calc("2^9"), 2 ** 9)
        self.assertEqual(calc("(9+3) / 11"), (9 + 3.0) / 11)
        self.assertEqual(calc("9 - (12 - 6)"), 9 - (12 - 6))
        self.assertEqual(calc("(2^3)^2"), (2 ** 3) ** 2)
        self.assertEqual(calc("2^(1-3)"), 2 ** (1 - 3))
        self.assertEqual(calc("2^3+2"), 2 ** 3 + 2)
        self.assertEqual(calc("2^3+5"), 2 ** 3 + 5)
        self.assertEqual(calc("sin(0)"), 0)
        self.assertEqual(calc("cos(0)"), 1)
        self.assertEqual(calc("max(0, 1)"), 1)
        self.assertEqual(calc("min(sin(0), cos(1))"), 0)

    def test_basic(self):
        i = default_identifiers
        u = default_unary_operators
        b = default_binary_operators

        self.template_test_basic(None, None, None)  # Default configuration
        self.template_test_basic(i, u, b)  # Force custom evaluator

    def test_float(self):
        i = default_identifiers
        u = default_unary_operators
        b = default_binary_operators

        self.template_test_float(None, None, None)  # Default configuration
        self.template_test_float(i, u, b)  # Force custom evaluator

    def test_order_of_operations(self):
        i = default_identifiers
        u = default_unary_operators
        b = default_binary_operators

        self.template_test_order_of_operations(None, None, None)  # Default configuration
        self.template_test_order_of_operations(i, u, b)  # Force custom evaluator

    def test_unary_operators(self):
        i = default_identifiers
        u = default_unary_operators
        b = default_binary_operators

        self.template_test_unary_operators(None, None, None)  # Default configuration
        self.template_test_unary_operators(i, u, b)  # Force custom evaluator

    def test_functions(self):
        i = default_identifiers
        u = default_unary_operators
        b = default_binary_operators

        self.template_test_functions(None, None, None)  # Default configuration
        self.template_test_functions(i, u, b)  # Force custom evaluator

    def test_variables(self):
        i = default_identifiers
        u = default_unary_operators
        b = default_binary_operators

        self.template_test_variables(None, None, None)  # Default configuration
        self.template_test_variables(i, u, b)  # Force custom evaluator

    def template_test_basic(self, i, u, b):
        self.assertEqual(calc("9", i, u, b), 9)
        self.assertEqual(calc("9 + 3 + 6", i, u, b), 9 + 3 + 6)
        self.assertEqual(calc("9 + 3 / 11", i, u, b), 9 + 3.0 / 11)
        self.assertEqual(calc("(9 + 3)", i, u, b), (9 + 3))
        self.assertEqual(calc("9 - 12 - 6", i, u, b), 9 - 12 - 6)
        self.assertEqual(calc("2^3^2", i, u, b), 2 ** 3 ** 2)
        self.assertEqual(calc("2^9", i, u, b), 2 ** 9)

    def template_test_float(self, i, u, b):
        self.assertEqual(calc("2*3.14159", i, u, b), 2 * 3.14159)
        self.assertEqual(calc("3.1415926535*3.1415926535 / 10", i, u, b), 3.1415926535 * 3.1415926535 / 10)
        self.assertEqual(calc("6.02E23 * 8.048", i, u, b), 6.02e23 * 8.048)
        self.assertEqual(calc(".02e23 * 8.", i, u, b), .02e23 * 8.)

    def template_test_order_of_operations(self, i, u, b):
        self.assertEqual(calc("(9+3) / 11", i, u, b), (9 + 3.0) / 11)
        self.assertEqual(calc("9 - (12 - 6)", i, u, b), 9 - (12 - 6))
        self.assertEqual(calc("(2^3)^2", i, u, b), (2 ** 3) ** 2)
        self.assertEqual(calc("2^(1-3)", i, u, b), 2 ** (1 - 3))
        self.assertEqual(calc("2^3+2", i, u, b), 2 ** 3 + 2)
        self.assertEqual(calc("2^3+5", i, u, b), 2 ** 3 + 5)

    def template_test_unary_operators(self, i, u, b):
        self.assertEqual(calc("-9", i, u, b), -9)
        self.assertEqual(calc("+9", i, u, b), 9)
        self.assertEqual(calc("--9", i, u, b), 9)
        self.assertEqual(
            calc("?1!", i, {
                ("?", "prefix"): lambda x: x*2,
                ("!", "postfix"): lambda x: x+1,
            }, b),
            4
        )

    def template_test_functions(self, i, u, b):
        self.assertEqual(
            calc("sin(0)", {"sin": math.sin}, u, b), 0)
        self.assertEqual(
            calc("0 + first(-1+19, 2^2, 3 + 4)", {"first": lambda a, b, c: a}, u, b), -1+19)
        self.assertEqual(
            calc("last(-1+19, 2^2, 3 + 4)", {"last": lambda a, b, c: c}, u, b), 3 + 4)
        self.assertEqual(
            calc("1 * mean(-1+19, 2^2, 3 + 4)", {"mean": lambda *args: statistics.mean(args)}, u, b),
            statistics.mean([-1+19, 2**2, 3 + 4]))
        self.assertEqual(
            calc("max_(1)", {"max": 0, "max_": lambda x: x}, u, b), 1)

    def template_test_variables(self, i, u, b):
        self.assertEqual(calc("x", {"x": 1}, u, b), 1)
        self.assertEqual(calc("x + x^x * x", {"x": 1}, u, b), 2)
        self.assertEqual(calc("x", {"x": 1, "x_": 2}, u, b), 1)
        self.assertEqual(calc("x_", {"x": 1, "x_": 2}, u, b), 2)

if __name__ == '__main__':
    unittest.main()
