
import chess

def apply_move(fen, move_uci):


    #board from fen 
    board = chess.Board(fen)
    
    #move 
    move = chess.Move.from_uci(move_uci)
    
    #do move
    if move in board.legal_moves:


        board.push(move)
        return board.fen()
    else:
        return "Illegal move"
    

#user input
fen = input()
move_uci = input()

# post-move and the fen string output
resulting_fen = apply_move(fen, move_uci)
print(resulting_fen)
