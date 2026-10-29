from monopoly.domain.board import STANDARD_BOARD, Board, EmptySquare, PropertySquare, StartSquare


def test_standard_board_has_sixteen_squares_starting_with_start() -> None:
    assert STANDARD_BOARD.size == 16
    assert STANDARD_BOARD.square_at(0) == StartSquare()


def test_standard_board_layout() -> None:
    properties = {
        index: (square.name, square.price)
        for index, square in enumerate(STANDARD_BOARD.squares)
        if isinstance(square, PropertySquare)
    }
    empties = [
        index
        for index, square in enumerate(STANDARD_BOARD.squares)
        if isinstance(square, EmptySquare)
    ]

    assert properties == {
        1: ("Rue Ontario", 60),
        3: ("Rue Wellington", 80),
        4: ("Avenue du Mont-Royal", 100),
        6: ("Rue Saint-Denis", 140),
        7: ("Boulevard Saint-Laurent", 160),
        9: ("Rue Sainte-Catherine", 180),
        10: ("Avenue Laurier", 200),
        12: ("Rue Sherbrooke", 240),
        13: ("Avenue du Parc", 260),
        14: ("Boulevard René-Lévesque", 300),
        15: ("Avenue Greene", 350),
    }
    assert empties == [2, 5, 8, 11]


def test_square_names() -> None:
    assert StartSquare().name == "Start"
    assert EmptySquare().name == "Empty lot"


def test_square_at_returns_the_square_at_that_index() -> None:
    board = Board(squares=(StartSquare(), PropertySquare(name="A", price=10)))

    assert board.square_at(1) == PropertySquare(name="A", price=10)
    assert board.size == 2
