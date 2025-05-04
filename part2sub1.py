import chess
from reconchess.utilities import without_opponent_pieces, is_illegal_castle

def nextmoveprediction(fen):
    board = chess.Board(fen)
    moves = set()

    for move in board.pseudo_legal_moves:
        moves.add(move.uci())

   
    moves.add("0000")

    #castling moves under RBC rules
    rbcboard = without_opponent_pieces(board)
    for move in rbcboard.generate_castling_moves():
        if not is_illegal_castle(board, move):
            moves.add(move.uci())

    return sorted(moves)


if __name__ == "__main__":
   
    str= input()
    for move in nextmoveprediction(str):
        print(move)

 
#8/5k2/8/8/8/p1p1p2n/P1P1P3/RB2K2R w K - 12 45
#8/8/8/8/7q/p2p1p1k/P2P1P2/Rn2K2R w KQ - 23 30