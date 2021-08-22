"""Evaluate simple mathematical expressions.

The main interface to this module is the `calc` function. Somewhat like `eval`, you can pass a string containing a
mathematical expression to evaluate. Unlike `builtins.eval`, `calc` is completely safe - it supports only the
operators, variables and functions you specify, and is confined to a simple set of grammar rules.

Known variables and functions can be added in the `identifiers` parameter. Additionally, you can specify custom unary
and binary operators.
`identifiers`: a dict with entries `{name: function or variable}` -
    function or variable name, matched to the actual function to call or a value.
`unary_operators`: a dict with entries `{(token, "prefix"/"postfix"): function}` -
    a prefix/postfix token (`!`, `-`, `+`, `~`, etc.) mapped to a function taking one argument.
    Postfix operators are executed before prefix operators.
`binary_operators`: a dict with entries `{(token, precedence[, "lr"/"rl"]): function}` -
    a token with a precedence controlling order of operations (lower number is higher precedence),
    optionally with right-to-left or left-to-right order of operations specified. For example,
    power operator `^` would be right-to-left and highest precedence, so it could be specified as
    `("^", 1, "rl"): lambda x, y: x**y`.


An example of these parameters can be imported from this module:
```
default_unary_operators = {
    ("-", "prefix"): lambda x: -x,
    ("+", "prefix"): lambda x: x
}

default_binary_operators = {
    ("+", 3): operator.add,
    ("-", 3): operator.sub,
    ("*", 2): operator.mul,
    ("/", 2): operator.truediv,
    ("%", 2): math.remainder,
    ("^", 1, "rl"): operator.pow,
}

default_identifiers = {
    "min": min,
    "max": max,
    "floor": math.floor,
    "ceil": math.ceil,
    "round": round,
    "clamp": lambda val, low, high: min(max(low, val), high),
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "atan2": math.atan2,
}
```

If you need to customize the set of operators, but don't change them afterwards, it may be more efficient to create a
`Parser(unary_operators, binary_operators)` instance, and use `parser.calc(identifiers)` instead of module-level `calc`.

Examples:
```
    >>> calc("2 + 2")
    4
    >>> calc("x^3", {"x": 1.25})
    1.953125
    >>> import math
    >>> calc("sin(pi/2)", {
    ...     "sin": math.sin,
    ...     "pi": math.pi
    ... })
    1.0

```
"""
from collections import OrderedDict
import operator
import math
import re
from textwrap import dedent
from typing import Any, Union, Callable
import lark

__all__ = [
    "calc", 
    "Parser", 
    "default_unary_operators", 
    "default_binary_operators",
    "default_identifiers"
]

class Transformer(lark.Transformer):
    re_binary_op = re.compile(r"eb(rl|lr)(-?\d+)")

    def __init__(self, identifiers: dict[str, Any] = None,
        oul = None,
        our = None,
        oblr = None,
        obrl = None):

        super().__init__()
        self.identifiers = identifiers or {}

        self.oul = oul or {}
        self.our = our or {}
        self.oblr = oblr or {}
        self.obrl = obrl or {}

    def number(self, tokens):
        """Number."""
        s = tokens[0].value
        try:
            return int(s)
        except ValueError:
            return float(s)

    def identifier(self, tokens):
        """Identifier."""
        s = tokens[0].value
        return self.identifiers[s]
    
    def function(self, tokens):
        """Function."""
        name = tokens[0].value
        return self.identifiers[name](*tokens[1:])
    
    def eul(self, tokens):
        """Expression Unary Left-side (prefix)."""
        op = tokens[0].value
        value = tokens[1]

        try:
            return self.oul[op](value)
        except KeyError:
            raise ValueError(f"unknown unary prefix operator '{op}'") from None
    
    def eur(self, tokens):
        """Expression Unary Right-side (postfix)."""
        op = tokens[1].value
        value = tokens[0]

        try:
            return self.our[op](value)
        except KeyError:
            raise ValueError(f"unknown unary postfix operator '{op}'") from None
    
    def eblr(self, precedence, tokens):
        """Expression Binary Left to Right."""
        op = tokens[1].value
        lhs = tokens[0]
        rhs = tokens[2]

        try:
            return self.oblr[precedence][op](lhs, rhs)
        except IndexError:
            raise ValueError(f"unknown order {precedence} binary left-to-right operator '{op}'") from None
    
    def ebrl(self, precedence, tokens):
        """Expression Binary Right to Left."""
        op = tokens[1].value
        lhs = tokens[0]
        rhs = tokens[2]

        try:
            return self.obrl[precedence][op](lhs, rhs)
        except IndexError:
            raise ValueError(f"unknown order {precedence} binary right-to-left operator '{op}'") from None

    def __getattr__(self, attr):
        # Implement a special function for parsing binary operators of any order of precedence
        if attr.startswith("eb"):
            match = re.search(self.re_binary_op, attr)
            precedence = int(match[2])
            
            if match[1] == "lr":
                return lambda tokens: self.eblr(precedence, tokens)
            else:
                return lambda tokens: self.ebrl(precedence, tokens)
        
        raise AttributeError


class Parser:
    """A parser that allows specifying unary and binary operators, valid in an expression.

    If you are doing many calculations with the same set of operators, it may be more efficient to create a Parser
    instance, and call `parser.calc` instead of module-level `calc`. Identifiers can still be specified using this
    method.

    More information on parameters available in module docstring.
    """

    grammar_template = dedent(r"""
        %import common.NUMBER
        %import common.CNAME  -> IDENTIFIER
        %import common.WS
        %ignore WS

        ?expr: eblr

        {eblr}
        {ebrl}
        {eul}
        {eur}
        
        ?atom: number | identifier | function | parens
        
        ?number:     NUMBER                              -> number
        ?function:   IDENTIFIER "(" expr ["," expr]* ")" -> function
        ?identifier: IDENTIFIER                          -> identifier
        ?parens:     "(" expr ")"

        {oblr}
        {obrl}
        {oul}
        {our}
    """).strip()

    def __init__(self,
        unary_operators: dict[tuple[str, Union["prefix", "postfix"]], Callable] = None,
        binary_operators: Union[
            dict[tuple[str, int], Callable],
            dict[tuple[str, int, Union["lr", "rl"]], Callable]
        ] = None):

        unary_operators = unary_operators or default_unary_operators
        binary_operators = binary_operators or default_binary_operators

        self.oul = {tag[0]: value for tag, value in unary_operators.items() if tag[1] == "prefix"}
        self.our = {tag[0]: value for tag, value in unary_operators.items() if tag[1] == "postfix"}
        
        self.oblr = OrderedDict()
        self.obrl = OrderedDict()
        """A dict of dicts, with outer keys being order of precedence (lower number is higher precedence),
        and inner keys being operator strings (`+`, `-`, etc.).
        rl - right-to-left operations, executed first
        lr - left-to-right operations
        """

        for tag, value in binary_operators.items():
            if len(tag) == 2 or tag[2] == "lr":
                data = self.oblr.get(tag[1], {})
                data[tag[0]] = value
                self.oblr[tag[1]] = data
            elif tag[2] == "rl":
                data = self.obrl.get(tag[1], {})
                data[tag[0]] = value
                self.obrl[tag[1]] = data
            else:
                raise ValueError("binary operator tag's third member must be 'lr' or 'rl'")
        
        self.grammar = self.make_grammar(
            our=self.our,
            oul=self.oul,
            oblr=self.oblr,
            obrl=self.obrl
        )

        self.parser = lark.Lark(self.grammar, parser="lalr", start="expr")
        self.transformer = Transformer({}, oul=self.oul, our=self.our, oblr=self.oblr, obrl=self.obrl)

    @classmethod
    def make_grammar(cls, oul: dict, our: dict, oblr: dict, obrl: dict):
        """Create grammar for the particular set of:
            our:  Operators Unary Right-side
            oul:  Operators Unary Left-side
            oblr: Operators Binary Left-to-Right
            obrl: Operators Binary Right-to-Left
        """
        # Additional abbreviations used in this function:
        # When prefixed by 'l', the variable is a list of strings for grammar.
        # When prefixed by 's', the variable is a string for grammar.

        # Binary operators
        loblr = cls.make_binary_ops(oblr, rl=False)
        lobrl = cls.make_binary_ops(obrl, rl=True)

        leblr = cls.make_binary_exprs(oblr, rl=False)
        lebrl = cls.make_binary_exprs(obrl, rl=True)
        
        # Unary operators
        if oul:
            seul = "?eul: eur | OUL eul -> eul"
            soul = "OUL: " + " | ".join(f'"{x}"' for x in oul)
        else:
            seul = "?eul: eur"
            soul = ""
        
        if our:
            seur = "?eur: atom | eur OUR -> eur"
            sour = "OUR: " + " | ".join(f'"{x}"' for x in our)
        else:
            seur = "?eur: atom"
            sour = ""

        return cls.grammar_template.format(
            eblr="\n".join(leblr),
            ebrl="\n".join(lebrl),
            eul=seul,
            eur=seur,
            oblr="\n".join(loblr),
            obrl="\n".join(lobrl),
            oul=soul,
            our=sour,
        )

    @classmethod
    def make_binary_exprs(cls, operators: dict, rl):
        if rl:
            final_rule = "eul"
            edir = "rl"
            odir = "RL"
        else:
            final_rule = "ebrl"
            edir = "lr"
            odir = "LR"

        exprs = []
        precedences = list(operators)

        if len(precedences) > 0:
            begin_rule = f"?eb{edir}: eb{edir}{precedences[0]}"
        else:
            begin_rule = f"?eb{edir}: {final_rule}"

        exprs.append(begin_rule)

        for i in range(len(precedences)):
            # Example: Expression Binary of precedence 1
            # eblr1 = eblr2 | eblr1 OBRL2 eblr2 -> eblr2
            pr = precedences[i]

            if i == len(precedences)-1:
                next_expr = final_rule
            else:
                next_expr = f"eb{edir}{precedences[i+1]}"

            expr = f"eb{edir}{pr}"
            op   = f"OB{odir}{pr}"

            if rl:
                expr = f"?{expr}: {next_expr} | {next_expr} {op} {expr}"
            else:
                expr = f"?{expr}: {next_expr} | {expr} {op} {next_expr}"

            exprs.append(expr)
        
        return exprs

    @classmethod
    def make_binary_ops(cls, ops_dict, rl):
        """Compose grammar for binary operators. If `rl` is True, compose for right-to-left grammar."""
        if rl:
            odir = "RL"
        else:
            odir = "LR"

        ops = []
        for precedence, operators in ops_dict.items():
            # Example: Operator Binary Left to Right
            # OBLR2: "*" | "/" | "%"
            op = f"OB{odir}{precedence}: " + " | ".join(f'"{x}"' for x in operators.keys())
            
            ops.append(op)

        return ops

    def calc(self, string, identifiers: dict[str, Any] = None):
        """Evaluate a mathematical expression.
        See module docstring for more info.
        """
        self.transformer.identifiers = identifiers or {}
        tree = self.parser.parse(string)

        return self.transformer.transform(tree) 


default_unary_operators = {
    ("-", "prefix"): lambda x: -x,
    ("+", "prefix"): lambda x: x
}

default_binary_operators = {
    ("+", 3): operator.add,
    ("-", 3): operator.sub,
    ("*", 2): operator.mul,
    ("/", 2): operator.truediv,
    ("%", 2): math.remainder,
    ("^", 1, "rl"): operator.pow,
}

default_identifiers = {
    "min": min,
    "max": max,
    "floor": math.floor,
    "ceil": math.ceil,
    "round": round,
    "clamp": lambda val, low, high: min(max(low, val), high),
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "atan2": math.atan2,
}

_default_parser = Parser(
    unary_operators=default_unary_operators,
    binary_operators=default_binary_operators
)

def calc(string,
    identifiers: dict[str, Any] = None,
    unary_operators: dict[tuple[str, Union["prefix", "postfix"]], Callable] = None,
    binary_operators: Union[
        dict[tuple[str, int], Callable],
        dict[tuple[str, int, Union["lr", "rl"]], Callable]
    ] = None):
    """Evaluate a mathematical expression.
    See module docstring for more info.
    """

    if unary_operators is None and binary_operators is None:
        return _default_parser.calc(string, identifiers)

    unary_operators = unary_operators or default_unary_operators
    binary_operators = binary_operators or default_binary_operators
    identifiers = identifiers or default_identifiers

    p = Parser(unary_operators, binary_operators)
    return p.calc(string, identifiers)
