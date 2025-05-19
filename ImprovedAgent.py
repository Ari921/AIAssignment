import os, random, math
import chess, chess.engine
from reconchess import *
from reconchess.utilities import without_opponent_pieces, is_illegal_castle
from collections import defaultdict, Counter


_WINDOW_CACHE = {}
def _window(c):
    if c in _WINDOW_CACHE:
        return _WINDOW_CACHE[c]
    f, r = chess.square_file(c), chess.square_rank(c)
    _WINDOW_CACHE[c] = [chess.square(i, j)
                        for i in range(f-1, f+2)
                        for j in range(r-1, r+2)
                        if 0 <= i < 8 and 0 <= j < 8]
    return _WINDOW_CACHE[c]

def _sense_outcome(b, win):
    return tuple((sq,
                  b.piece_at(sq).symbol() if b.piece_at(sq) else None)
                 for sq in win)



class ImprovedAgent(Player):
    def __init__(self):
        self.board, self.color  = None, None
        self.possible_boards    = []
        self.last_capture_sq    = None
        self.stockfish_path     = '/opt/stockfish/stockfish'
        # self.stockfish_path     = './stockfish.exe'
        if not os.path.exists(self.stockfish_path):
            raise FileNotFoundError('Stockfish not found')
        self.engine = chess.engine.SimpleEngine.popen_uci(
            self.stockfish_path, setpgrp=True)

   
    def handle_game_start(self, color, board, opponent_name):
        self.color           = color
        self.board           = board
        self.possible_boards = [board.fen()]
        self.last_capture_sq = None
        try: self.engine.quit()
        except: pass
        self.engine = chess.engine.SimpleEngine.popen_uci(
            self.stockfish_path, setpgrp=True)

    def handle_opponent_move_result(self,
                                    captured_my_piece: bool,
                                    capture_square: Optional[Square]):
        self.last_capture_sq = capture_square if captured_my_piece else None
        if not (captured_my_piece and capture_square):
            return

        nxt, seen = [], set()
        for fen in self.possible_boards:
            b = chess.Board(fen)
            for mv in b.generate_legal_captures():
                if mv.to_square == capture_square:
                    b.push(mv); nf = b.fen(); b.pop()
                    if nf not in seen:
                        nxt.append(nf); seen.add(nf)
                    break
        self.possible_boards = nxt[:2_000]                          

    
    def choose_sense(self, sense_actions, move_actions, seconds_left):
        
        if self.last_capture_sq and self.last_capture_sq in sense_actions:
            return self.last_capture_sq

        if len(self.possible_boards) == 1:
            return random.choice(sense_actions)

        #dangerous squares 
        danger = Counter()
        for fen in random.sample(self.possible_boards,
                                 min(1000, len(self.possible_boards))):
            b = chess.Board(fen); b.turn = not self.color
            for mv in b.generate_legal_captures():
                danger[mv.to_square] += 1
        if danger:
            hot = danger.most_common(1)[0][0]
            if hot in sense_actions:
                return hot

        # maximal-entropy window
        sample = random.sample(self.possible_boards,
                               min(1000, len(self.possible_boards)))
        best_sq, best_ent = None, -1
        for sq in sense_actions:
            win = _window(sq)
            hist = Counter(_sense_outcome(chess.Board(fen), win) for fen in sample)
            tot  = sum(hist.values())
            ent  = -sum(c/tot * math.log(c/tot) for c in hist.values())
            if ent > best_ent:
                best_sq, best_ent = sq, ent
        return best_sq

    def handle_sense_result(self, sense_result):
        def consistent(b):
            for sq, exp in sense_result:
                act = b.piece_at(sq)
                if (act is None) != (exp is None):
                    return False
                if act and act.symbol() != exp.symbol():
                    return False
            return True
        self.possible_boards = [f for f in self.possible_boards
                                if consistent(chess.Board(f))]
        if len(self.possible_boards) > 3_000:                   
            self.possible_boards = random.sample(self.possible_boards, 3_000)  


    def choose_move(self, legal_moves, _seconds_left):
        if not self.possible_boards:
            return random.choice(legal_moves)

        self.possible_boards = list(dict.fromkeys(self.possible_boards))
        if len(self.possible_boards) > 2_000:                 
            self.possible_boards = random.sample(self.possible_boards, 2_000) 

        W, scores  = 1 / len(self.possible_boards), defaultdict(float)
        t_per      = max(.02, 4 / len(self.possible_boards))     
        restarted  = False

        for fen in self.possible_boards:
            b = chess.Board(fen); b.turn = self.color
            if (not b.is_valid()
                or b.king(chess.WHITE) is None
                or b.king(chess.BLACK) is None):
                continue

            #immediate mate / king capture
            enemy_king = b.king(not self.color)
            if enemy_king:
                for mv in b.pseudo_legal_moves:
                    if mv.to_square == enemy_king and mv in legal_moves:
                        scores[mv] += 1000 * W

            
            for mv in b.generate_legal_captures():
                if mv in legal_moves:
                    scores[mv] += 80 * W
            for sq, pc in b.piece_map().items():
                if pc.color == self.color and b.is_attacked_by(not self.color, sq):
                    for mv in b.pseudo_legal_moves:
                        if mv.from_square == sq and mv in legal_moves:
                            scores[mv] += 40 * W

           
            try:
                rbc = without_opponent_pieces(b)
                for mv in rbc.generate_castling_moves():
                    if mv in legal_moves and not is_illegal_castle(b, mv):
                        scores[mv] += 150 * W
            except: pass

           
            try:
                res = self.engine.play(b, chess.engine.Limit(time=t_per))
            except (chess.engine.EngineError,
                    chess.engine.EngineTerminatedError):
                if not restarted:
                    self.engine = chess.engine.SimpleEngine.popen_uci(
                        self.stockfish_path, setpgrp=True)
                    restarted = True
                continue
            if res.move is None:                              
                continue
            mv = res.move
            if mv in legal_moves:
                sc = res.info.get("score")
                if sc:
                    scores[mv] += sc.pov(self.color).score(mate_score=10_000) * W
                b.push(mv)
                if b.is_checkmate():
                    scores[mv] += 50 * W
                b.pop()

            if chess.Move.null() in legal_moves:
                scores[chess.Move.null()] += .1 * W

        return max(scores, key=scores.get) if scores else random.choice(legal_moves)

   
    def handle_move_result(self, requested_move, taken, captured_opponent_piece, capture_square):
        if captured_opponent_piece:                                            
            self.last_capture_sq = None                          
        nxt = []
        for fen in self.possible_boards:
            b = chess.Board(fen)
            if requested_move in b.legal_moves:
                b.push(requested_move); nxt.append(b.fen())
        self.possible_boards = nxt[:2_000]                       

    def handle_game_end(self, winner_color, win_reason, game_history):
        try: self.engine.quit()
        except: pass
