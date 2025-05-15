import chess.engine
import random
from reconchess import *
import os
from typing import Optional, List, Tuple

class TroutBot(Player):
    """
    TroutBot uses the Stockfish chess engine to choose moves.
    Make sure stockfish.exe is in the same folder or update the path below.
    """

    def __init__(self):
        self.board = None
        self.color = None
        self.my_piece_captured_square = None

        # Path with double .exe.exe as requested
        stockfish_path = "C:\\stockfish.exe.exe"

        if not os.path.exists(stockfish_path):
            raise ValueError(f'No stockfish executable found at "{stockfish_path}"')

        # initialize the stockfish engine (removed setpgrp=True for Windows)
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)

    def handle_game_start(self, color: Color, board: chess.Board, opponent_name: str):
        self.board = board
        self.color = color

    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: Optional[Square]):
        # if the opponent captured our piece, remove it from our board.
        self.my_piece_captured_square = capture_square
        if captured_my_piece and capture_square is not None:
            self.board.remove_piece_at(capture_square)

    def choose_sense(self, sense_actions: List[Square], move_actions: List[chess.Move], seconds_left: float) -> Optional[Square]:
        # if our piece was just captured, sense where it was captured
        if self.my_piece_captured_square:
            return self.my_piece_captured_square

        # if we might capture a piece when we move, sense where the capture will occur
        future_move = self.choose_move(move_actions, seconds_left)
        if future_move is not None and self.board.piece_at(future_move.to_square) is not None:
            return future_move.to_square

        # otherwise, just randomly choose a sense action, avoiding known friendly pieces
        safe_sense_squares = [sq for sq in sense_actions if self.board.piece_at(sq) is None or self.board.piece_at(sq).color != self.color]
        return random.choice(safe_sense_squares) if safe_sense_squares else random.choice(sense_actions)

    def handle_sense_result(self, sense_result: List[Tuple[Square, Optional[chess.Piece]]]):
        # add the pieces in the sense result to our board
        for square, piece in sense_result:
            self.board.set_piece_at(square, piece)

    def choose_move(self, move_actions: List[chess.Move], seconds_left: float) -> Optional[chess.Move]:
        # try to take the enemy king if we know where it is
        enemy_king_square = self.board.king(not self.color)
        if enemy_king_square:
            enemy_king_attackers = self.board.attackers(self.color, enemy_king_square)
            if enemy_king_attackers:
                attacker_square = enemy_king_attackers.pop()
                return chess.Move(attacker_square, enemy_king_square)

        # otherwise, use Stockfish to find a good move
        try:
            self.board.turn = self.color
            self.board.clear_stack()
            result = self.engine.play(self.board, chess.engine.Limit(time=0.5))
            return result.move
        except chess.engine.EngineTerminatedError:
            print('Stockfish Engine died')
        except chess.engine.EngineError:
            print(f'Stockfish Engine bad state at "{self.board.fen()}"')

        return None  # If no good move, return None to pass

    def handle_move_result(self, requested_move: Optional[chess.Move], taken_move: Optional[chess.Move],
                           captured_opponent_piece: bool, capture_square: Optional[Square]):
        # update board with the move that was actually taken
        if taken_move is not None:
            self.board.push(taken_move)

    def handle_game_end(self, winner_color: Optional[Color], win_reason: Optional[WinReason],
                        game_history: GameHistory):
        try:
            self.engine.quit()
        except chess.engine.EngineTerminatedError:
            pass
