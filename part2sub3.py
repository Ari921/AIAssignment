import chess

def nextstatepredictionwithcaptures(fen, capturesquarestring):
    board = chess.Board(fen)
    targetsquare = chess.parse_square(capturesquarestring) #convert the capture square from algebraic eg:d6 to board index
    capturestates = []

    #loop through all moves that are valid in RBC
    for move in board.pseudo_legal_moves:
        #only care about moves where the piece lands on the square where a capture was reported.
        if move.to_square == targetsquare:
            newboard = board.copy()
            newboard.push(move)
            capturestates.append(newboard.fen())

    return sorted(capturestates)


str=input()
square=input()
for fen in nextstatepredictionwithcaptures(str, square):
    print(fen)


#k1n1n3/p2p1p2/P2P1P2/8/8/8/8/7K b - - 23 30
#d6
#r1bqk2r/pppp1ppp/2n2n2/4p3/1b2P3/1P3N2/PBPP1PPP/RN1QKB1R w KQkq - 0 5
#e5
