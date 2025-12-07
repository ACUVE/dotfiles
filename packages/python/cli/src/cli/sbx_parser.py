"""Simple parser for Lisp-like syntax (for testing purposes only)."""

import re
from typing import List

from .sbx_ast import ASTNode, Integer, Regex, SExpression, String, Symbol


class ParseError(Exception):
    """Raised when parsing fails."""

    pass


class Tokenizer:
    """Tokenizes Lisp-like syntax."""

    TOKEN_REGEX = re.compile(
        r"""
        \s*                           # Skip whitespace
        (?:
            ;[^\n]*                   # Comment
            |
            (\(|\))                   # Parentheses
            |
            ("(?:[^"\\]|\\.)*")       # String literal
            |
            (\#"(?:[^"\\]|\\.)*")     # Regex literal
            |
            (-?\d+)                   # Integer
            |
            ([^\s()";]+)              # Symbol
        )
    """,
        re.VERBOSE,
    )

    def __init__(self, text: str):
        self.text = text
        self.tokens: List[tuple[str, str]] = []
        self._tokenize()
        self.pos = 0

    def _tokenize(self) -> None:
        """Tokenize the input text."""
        for match in self.TOKEN_REGEX.finditer(self.text):
            lparen, string, regex, integer, symbol = match.groups()
            if lparen == "(":
                self.tokens.append(("LPAREN", "("))
            elif lparen == ")":
                self.tokens.append(("RPAREN", ")"))
            elif string:
                # Unescape string content
                content = string[1:-1]  # Remove quotes
                content = (
                    content.replace("\\n", "\n")
                    .replace("\\t", "\t")
                    .replace('\\"', '"')
                    .replace("\\\\", "\\")
                )
                self.tokens.append(("STRING", content))
            elif regex:
                # Regex literal (#"...")
                content = regex[2:-1]  # Remove #" and "
                # Unescape regex content
                content = (
                    content.replace("\\n", "\n")
                    .replace("\\t", "\t")
                    .replace('\\"', '"')
                    .replace("\\\\", "\\")
                )
                self.tokens.append(("REGEX", content))
            elif integer:
                self.tokens.append(("INTEGER", integer))
            elif symbol:
                self.tokens.append(("SYMBOL", symbol))

    def peek(self) -> tuple[str, str] | None:
        """Peek at the current token without consuming it."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self) -> tuple[str, str] | None:
        """Consume and return the current token."""
        token = self.peek()
        if token:
            self.pos += 1
        return token


class Parser:
    """Parses Lisp-like syntax into AST nodes."""

    def __init__(self, text: str):
        self.tokenizer = Tokenizer(text)

    def parse(self) -> List[ASTNode]:
        """Parse the input and return a list of top-level nodes."""
        nodes = []
        while self.tokenizer.peek():
            node = self._parse_node()
            if node:
                nodes.append(node)
        return nodes

    def _parse_node(self) -> ASTNode | None:
        """Parse a single node."""
        token = self.tokenizer.peek()
        if not token:
            return None

        token_type, token_value = token

        if token_type == "LPAREN":
            return self._parse_sexpression()
        elif token_type == "STRING":
            self.tokenizer.consume()
            return String(token_value)
        elif token_type == "REGEX":
            self.tokenizer.consume()
            return Regex(token_value)
        elif token_type == "INTEGER":
            self.tokenizer.consume()
            return Integer(int(token_value))
        elif token_type == "SYMBOL":
            self.tokenizer.consume()
            return Symbol(token_value)
        elif token_type == "RPAREN":
            raise ParseError("Unexpected closing parenthesis")
        else:
            raise ParseError(f"Unexpected token: {token_type}")

    def _parse_sexpression(self) -> SExpression:
        """Parse an S-expression."""
        token = self.tokenizer.consume()
        if not token or token[0] != "LPAREN":
            raise ParseError("Expected opening parenthesis")

        elements = []
        while True:
            token = self.tokenizer.peek()
            if not token:
                raise ParseError(
                    "Unexpected end of input, expected closing parenthesis"
                )

            if token[0] == "RPAREN":
                self.tokenizer.consume()
                break

            node = self._parse_node()
            if node:
                elements.append(node)

        return SExpression(elements)


def parse(text: str) -> List[ASTNode]:
    """Parse Lisp-like syntax and return AST nodes."""
    parser = Parser(text)
    return parser.parse()
