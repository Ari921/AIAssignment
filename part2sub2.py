import chess

def nextstateprediction(fen):
    board = chess.Board(fen)
    nextstates= []

    #generate all pseudolegal moves
    for move in board.pseudo_legal_moves:
        newboard = board.copy()
        newboard.push(move)
        nextstates.append(newboard.fen())

    #null move-player does nothing on their turn 
    nullboard = board.copy()
    nullboard.push(chess.Move.null())
    nextstates.append(nullboard.fen())

    return sorted(nextstates)



if __name__ == "__main__":
  
    str=input()
    for fen in nextstateprediction(str):
        print(fen)

#8/8/8/8/k7/8/7K/3B4 w - - 48 32
#k7/p2p1p2/P2P1P2/8/8/8/8/7K b - - 23 30