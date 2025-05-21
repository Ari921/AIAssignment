import os
import random
import chess
import chess.engine
from reconchess import Player
from reconchess.utilities import without_opponent_pieces, is_illegal_castle
from collections import Counter, defaultdict

_WINDOW_CACHE = {}
def _window(center):
    if center in _WINDOW_CACHE:
        return _WINDOW_CACHE[center]
    f, r = chess.square_file(center), chess.square_rank(center)
    _WINDOW_CACHE[center] = [
        chess.square(x, y)
        for x in range(f - 1, f + 2)
        for y in range(r - 1, r + 2)
        if 0 <= x < 8 and 0 <= y < 8
    ]
    return _WINDOW_CACHE[center]

def _sense_outcome(board, window):
    return tuple(
        (sq, board.piece_at(sq).symbol() if board.piece_at(sq) else None)
        for sq in window
    )

class ImprovedAgent(Player):
    def __init__(self):
        self.board = None
        self.color = None
        self.possible_boards = []
        self.board_confidence = defaultdict(lambda: 1)
        self.last_capture_sq = None
        #self.stockfish_path = './stockfish.exe'
        self.stockfish_path= chess.engine.SimpleEngine.popen_uci('/opt/stockfish/stockfish', setpgrp=True)
        self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path, setpgrp=True)

        #opening strategy
        self.current_move = 0
        self.perform_opening = True
        self.opening_moves = {
            chess.WHITE: [
                chess.Move.from_uci("c2c4"),
                chess.Move.from_uci("b1c3"),
                chess.Move.from_uci("d2d3"),
                chess.Move.from_uci("c1g5")
            ],
            chess.BLACK: [
                chess.Move.from_uci("c7c5"),
                chess.Move.from_uci("b8c6"),
                chess.Move.from_uci("d7d6"),
                chess.Move.from_uci("c8g4")
            ]
        }

    def handle_game_start(self, color, board, opponent_name):
        self.color = color
        self.board = board
        self.possible_boards = [board.fen()]
        self.last_capture_sq = None
        self.current_move = 0
        self.perform_opening = True

    def handle_opponent_move_result(self, captured_my_piece, capture_square):
        self.last_capture_sq = capture_square if captured_my_piece else None
        new_boards = set()
        for fen in self.possible_boards:
            b = chess.Board(fen)
            b.clear_stack()
            if b.turn != (not self.color):
                continue
            for mv in b.pseudo_legal_moves:
                if captured_my_piece and mv.to_square != capture_square:
                    continue
                b.push(mv)
                new_boards.add(b.fen())
                b.pop()
        if captured_my_piece:
            self.possible_boards = random.sample(list(new_boards), min(1000, len(new_boards)))
        else:
            self.possible_boards = random.sample(self.possible_boards, min(1000, len(self.possible_boards)))

    def choose_sense(self, sense_actions, move_actions, seconds_left):
        sample = random.sample(self.possible_boards, min(300, len(self.possible_boards)))
        king_heatmap = Counter()
        for fen in sample:
            b = chess.Board(fen)
            b.clear_stack()
            k = b.king(not self.color)
            if k:
                king_heatmap[k] += 1

        best_sq, best_score = None, -1
        for sq in sense_actions:
            seen = set()
            proximity_score = sum(king_heatmap[s] for s in _window(sq))
            for fen in sample:
                b = chess.Board(fen)
                b.clear_stack()
                seen.add(_sense_outcome(b, _window(sq)))
            entropy_score = len(seen)
            total_score = entropy_score + 0.5 * proximity_score 
            if total_score > best_score:
                best_sq, best_score = sq, total_score
        return best_sq

    def handle_sense_result(self, sense_result):
        def consistent(board):
            for sq, expected in sense_result:
                actual = board.piece_at(sq)
                if (actual is None) != (expected is None):
                    return False
                if actual and actual.symbol() != expected:
                    return False
            return True

        new_boards = []
        new_conf = defaultdict(int)
        for fen in self.possible_boards:
            b = chess.Board(fen)
            b.clear_stack()
            if consistent(b):
                new_boards.append(fen)
                new_conf[fen] = self.board_confidence[fen] + 1

        self.possible_boards = random.sample(new_boards, min(1000, len(new_boards)))
        self.board_confidence = new_conf

    def choose_move(self, move_actions, seconds_left):
        #opening strategy
        if self.perform_opening:
            if self.current_move < len(self.opening_moves[self.color]):
                move = self.opening_moves[self.color][self.current_move]
                if move in move_actions:
                    
                    return move
                else:
                   
                    self.perform_opening = False
            else:
                self.perform_opening = False
        

        boards = []
        for fen in self.possible_boards:
            b = chess.Board(fen)
            b.clear_stack()
            if b.turn == self.color:
                boards.append(b)

        if not boards:
            return random.choice(move_actions)

        if len(boards) > 10000:
            boards = random.sample(boards, 10000)

        stockfish_time = max(0.05, 10 / len(boards))
       
        move_counter = Counter()
        king_targets = Counter()

        for b in boards:
            enemy_king = b.king(not self.color)
            if enemy_king:
                king_targets[enemy_king] += self.board_confidence[b.fen()]

        if king_targets:
            likely_king = king_targets.most_common(1)[0][0]
            for mv in move_actions:
                if mv.to_square == likely_king:
                    return mv

        for b in boards:
            try:
                fen = b.fen()
                b.clear_stack()
                result = self.engine.play(b, chess.engine.Limit(time=stockfish_time))
                move = result.move
                if move in move_actions:
                    move_counter[move] += self.board_confidence[fen]
            except:
                continue

        if move_counter:
            return move_counter.most_common(1)[0][0]

        captures = [mv for b in boards for mv in b.generate_legal_captures() if mv in move_actions]
        return random.choice(captures or move_actions)

    def handle_move_result(self, requested_move, taken_move, captured_opponent_piece, capture_square):
        new_fens = []
        for fen in self.possible_boards:
            b = chess.Board(fen)
            b.clear_stack()
            if requested_move in b.legal_moves:
                b.push(requested_move)
                new_fens.append(b.fen())
        self.possible_boards = random.sample(new_fens, min(1000, len(new_fens)))

      
        self.current_move += 1

    def handle_game_end(self, winner_color, win_reason, game_history):
        try:
            self.engine.quit()
        except:
            pass


