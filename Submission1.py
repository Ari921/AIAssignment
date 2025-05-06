import chess.engine

def find_king_capture_move(board):
    for move in board.legal_moves:
        board.push(move)
        if not any(piece.symbol() == 'k' for piece in board.piece_map().values()):
            board.pop()
            return move
        board.pop()
    return None

def get_best_move(fen):
    board = chess.Board(fen)
    move = find_king_capture_move(board)

    if move is None:
        with chess.engine.SimpleEngine.popen_uci('/opt/stockfish/stockfish') as engine:
            result = engine.play(board, chess.engine.Limit(time=0.5))
            move = result.move

    return move.uci()

fen_input = input()
print(get_best_move(fen_input))
