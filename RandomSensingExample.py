import os
import random
import chess
import chess.engine
from reconchess import Player
from reconchess.utilities import without_opponent_pieces, is_illegal_castle
from collections import Counter

def find_king_capture_move(board):
    opponent_color = not board.turn
    for move in board.legal_moves:
        board.push(move)
        if board.king(opponent_color) is None:
            board.pop()
            return move
        board.pop()
    return None

class RandomSensing(Player):
    def __init__(self):
        self.color = None
        self.board = None
        self.possible_boards = []
        self.capture_square = None
        self.engine = chess.engine.SimpleEngine.popen_uci(r'C:\stockfish.exe.exe', setpgrp=True)


    def handle_game_start(self, color, board, opponent_name):
        self.color = color
        self.board = board
        self.possible_boards = [board.fen()]
        try:
            self.engine.quit()
        except:
            pass
        self.engine = chess.engine.SimpleEngine.popen_uci(r'C:\stockfish.exe.exe', setpgrp=True)


    def handle_opponent_move_result(self, captured_my_piece, capture_square):
        self.capture_square = capture_square
        if captured_my_piece and capture_square is not None:
            filtered = []
            for fen in self.possible_boards:
                board = chess.Board(fen)
                for move in board.pseudo_legal_moves:
                    if move.to_square == capture_square:
                        newboard = board.copy()
                        newboard.push(move)
                        filtered.append(newboard.fen())
            self.possible_boards = sorted(filtered)

    def choose_sense(self, sense_actions, move_actions, seconds_left):
        non_edge_squares = [
            sq for sq in sense_actions
            if 1 <= chess.square_file(sq) <= 6 and 1 <= chess.square_rank(sq) <= 6
        ]
        return random.choice(non_edge_squares or sense_actions)

    def handle_sense_result(self, sense_result):
        def is_consistent(board):
            for square, expected in sense_result:
                actual = board.piece_at(square)
                if actual is None and expected is None:
                    continue
                if (actual is None) != (expected is None):
                    return False
                if actual.symbol() != expected.symbol():
                    return False
            return True

        self.possible_boards = [
            fen for fen in self.possible_boards if is_consistent(chess.Board(fen))
        ]

    def choose_move(self, move_actions, seconds_left):
        if not self.possible_boards:
            return random.choice(move_actions)

        # Limit the number of boards for performance reasons
        if len(self.possible_boards) > 10000:
            self.possible_boards = random.sample(self.possible_boards, 10000)

        move_counter = Counter()
        N = len(self.possible_boards)
        time_per_board = max(0.01, 10 / N)  # Distribute time among boards

        for fen in self.possible_boards:
            board = chess.Board(fen)
            board.turn = self.color

            # 1) Try king capture move first
            king_capture_move = find_king_capture_move(board)
            if king_capture_move and king_capture_move in move_actions:
                move_counter[king_capture_move] += 1000  # Large weight for king captures
                continue

            # 2) Otherwise, get engine move
            try:
                result = self.engine.play(board, chess.engine.Limit(time=time_per_board))
                move = result.move
                if move in move_actions:
                    move_counter[move] += 1
            except chess.engine.EngineTerminatedError:
                print("Stockfish engine died. Restarting...")
                self.engine = chess.engine.SimpleEngine.popen_uci(r'C:\stockfish.exe.exe', setpgrp=True)

                continue
            except chess.engine.EngineError:
                print(f"Stockfish bad state at: {board.fen()}")
                continue

            # 3) Add RBC castling moves count
            try:
                rbc_board = without_opponent_pieces(board)
                for move in rbc_board.generate_castling_moves():
                    if not is_illegal_castle(board, move) and move in move_actions:
                        move_counter[move] += 1
            except:
                pass

            # 4) Consider null move if allowed
            if chess.Move.null() in move_actions:
                move_counter[chess.Move.null()] += 1

        if move_counter:
            best_move = move_counter.most_common(1)[0][0]
            return best_move

        # Fallback random
        return random.choice(move_actions)

    def handle_move_result(self, requested_move, taken_move, captured_opponent_piece, capture_square):
        updated = []
        for fen in self.possible_boards:
            board = chess.Board(fen)
            if requested_move in board.legal_moves:
                board.push(requested_move)
                updated.append(board.fen())
        self.possible_boards = updated

    def handle_game_end(self, winner_color, win_reason, game_history):
        try:
            self.engine.quit()
        except:
            print("Engine already terminated")
