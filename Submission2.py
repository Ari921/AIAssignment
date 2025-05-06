import chess
import chess.engine

def find_king_capture_move(board):
    for move in board.legal_moves:
        board.push(move)
        if board.king(chess.BLACK) is None:
            board.pop()
            return move
        board.pop()
    return None

def get_best_move(fen, engine):
    board = chess.Board(fen)
    move = find_king_capture_move(board)

    if move is None:
        result = engine.play(board, chess.engine.Limit(time=0.03))  
        move = result.move

    return move.uci()

def analyze_moves(fen_list):
    move_counts = {}

    with chess.engine.SimpleEngine.popen_uci('/opt/stockfish/stockfish') as engine:
        for fen in fen_list:
            move = get_best_move(fen, engine)
            move_counts[move] = move_counts.get(move, 0) + 1

    most_common_move = max(move_counts.items(), key=lambda x: (x[1], -ord(x[0][0])))
    print(most_common_move[0])


n = int(input())
fen_list = [input() for _ in range(n)]

analyze_moves(fen_list)
