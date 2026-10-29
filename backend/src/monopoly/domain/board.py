from dataclasses import dataclass
from typing import TypeAlias


@dataclass(frozen=True)
class StartSquare:
    name: str = "Start"


@dataclass(frozen=True)
class EmptySquare:
    name: str = "Empty lot"


@dataclass(frozen=True)
class PropertySquare:
    name: str
    price: int
    rent: int


Square: TypeAlias = StartSquare | EmptySquare | PropertySquare


@dataclass(frozen=True)
class Board:
    squares: tuple[Square, ...]

    @property
    def size(self) -> int:
        return len(self.squares)

    def square_at(self, index: int) -> Square:
        return self.squares[index]


STANDARD_BOARD = Board(
    squares=(
        StartSquare(),
        PropertySquare(name="Rue Ontario", price=60, rent=30),
        EmptySquare(),
        PropertySquare(name="Rue Wellington", price=80, rent=40),
        PropertySquare(name="Avenue du Mont-Royal", price=100, rent=50),
        EmptySquare(),
        PropertySquare(name="Rue Saint-Denis", price=140, rent=70),
        PropertySquare(name="Boulevard Saint-Laurent", price=160, rent=80),
        EmptySquare(),
        PropertySquare(name="Rue Sainte-Catherine", price=180, rent=90),
        PropertySquare(name="Avenue Laurier", price=200, rent=100),
        EmptySquare(),
        PropertySquare(name="Rue Sherbrooke", price=240, rent=120),
        PropertySquare(name="Avenue du Parc", price=260, rent=130),
        PropertySquare(name="Boulevard René-Lévesque", price=300, rent=150),
        PropertySquare(name="Avenue Greene", price=350, rent=175),
    )
)
