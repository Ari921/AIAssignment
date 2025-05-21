import chess

def print_ascii_board(fen):
    board = chess.Board(fen)
    for rank in range(8, 0, -1):
        line = ''
        for file in range(8):
            square = chess.square(file, rank - 1)
            piece = board.piece_at(square)
            if piece is None:
                line += '. '
            else:
                line += piece.symbol() + ' '
        print(line.strip())

#user input
fen = input()

#here's the output
print_ascii_board(fen)
