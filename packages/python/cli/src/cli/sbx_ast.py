"""AST nodes for Lisp-like syntax used in sandbox profiles."""

from abc import ABC, abstractmethod
from typing import Union


class Node(ABC):
    """Base class for all AST nodes."""

    @abstractmethod
    def to_string(self) -> str:
        """Convert the node to a string representation."""
        pass

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.to_string()!r})"


class Symbol(Node):
    """Represents a symbol (identifier) in the syntax."""

    def __init__(self, name: str):
        self.name = name

    def to_string(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Symbol) and self.name == other.name


class String(Node):
    """Represents a string literal."""

    def __init__(self, value: str):
        self.value = value

    def to_string(self) -> str:
        # Escape special characters
        escaped = (
            self.value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\t", "\\t")
        )
        return f'"{escaped}"'

    def __eq__(self, other: object) -> bool:
        return isinstance(other, String) and self.value == other.value


class Integer(Node):
    """Represents an integer literal."""

    def __init__(self, value: int):
        self.value = value

    def to_string(self) -> str:
        return str(self.value)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Integer) and self.value == other.value


class SExpression(Node):
    """Represents an S-expression (list of nodes)."""

    def __init__(self, elements: list["ASTNode"]):
        self.elements = elements

    def to_string(self) -> str:
        if not self.elements:
            return "()"

        # Check if this is a simple single-line expression
        inner = " ".join(el.to_string() for el in self.elements)
        if len(inner) < 60 and "\n" not in inner:
            return f"({inner})"

        # Multi-line formatting for complex expressions
        result = ["("]
        for i, element in enumerate(self.elements):
            element_str = element.to_string()
            if i == 0:
                result.append(element_str)
            else:
                # Indent nested elements
                indented = "\n  ".join(element_str.split("\n"))
                result.append(f"\n  {indented}")
        result.append(")")
        return "".join(result)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SExpression) and self.elements == other.elements


# Type alias for any AST node
ASTNode = Union[Symbol, String, Integer, SExpression]
