import chess

def is_board_consistent_with_window(board, windowdesc):
    entries = windowdesc.strip().split(';')
    for entry in entries:
        if not entry:
            continue
        squarestr, expected = entry.split(':')
        squareindex = chess.parse_square(squarestr)
        piece = board.piece_at(squareindex)

        if piece:
            actual = piece.symbol()
        else:
            actual='?'

        if actual != expected:
            return False
    return True

#filters a list of FEN strings,returning only those boards that matchthe given sensing window
def filterconsistentstates(fenlist, windowdesc):
    consistent=[]
    for fen in fenlist:
        board=chess.Board(fen)
        if is_board_consistent_with_window(board, windowdesc):
            consistent.append(fen)
    return sorted(consistent)


        
N = int(input())
    
fenstr = []
for y in range(N):
    fenstr.append(input())
        
#the sensing window
window=input()
result=filterconsistentstates(fenstr, window)
for i in result:
    print(i)

 

#1k6/1ppn4/8/8/8/1P1P4/PN3P2/2K5 w - - 0 32
#1k6/1ppnP3/8/8/8/1P1P4/PN3P2/2K5 w - - 0 32
#1k6/1ppn1p2/8/8/8/1P1P4/PN3P2/2K5 w - - 0 32
#c8:?;d8:?;e8:?;c7:p;d7:n;e7:?;c6:?;d6:?;e6:?