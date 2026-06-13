import chess

class ClassicalEngine:

    def __init__(self, depth=5):

        self.depth = depth

        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 0
        }
    def order_moves(self, board, moves):

        def score_move(move):

            score = 0

            # ----------------------------------
            # CAPTURES (MVV-LVA style)
            # ----------------------------------
            if board.is_capture(move):

                captured_piece = board.piece_at(move.to_square)
                attacker_piece = board.piece_at(move.from_square)

                if captured_piece:
                    score += self.piece_values[captured_piece.piece_type]

                if attacker_piece:
                    score -= self.piece_values[attacker_piece.piece_type]

                score += 1000  # capture bonus

            # ----------------------------------
            # CHECKS
            # ----------------------------------
            board.push(move)
            if board.is_check():
                score += 500
            board.pop()

            # ----------------------------------
            # CENTER CONTROL
            # ----------------------------------
            center_squares = [27, 28, 35, 36]  # d4, e4, d5, e5

            if move.to_square in center_squares:
                score += 50

            return score

        return sorted(moves, key=score_move, reverse=True)
    # ==========================================
    # EVALUATION FUNCTION
    # ==========================================
    def evaluate(self, board: chess.Board) -> int:

        # ==========================================
        # TERMINAL STATES
        # ==========================================

        if board.is_checkmate():
            # side to move is checkmated
            if board.turn == chess.WHITE:
                return -float("inf")  # white is losing
            else:
                return float("inf")   # black is losing

        if board.is_stalemate():
            return 0

        if board.is_insufficient_material():
            return 0

        if board.can_claim_threefold_repetition():
            return 0

        if board.can_claim_fifty_moves():
            return 0

        # ==========================================
        # MATERIAL EVALUATION
        # ==========================================

        score = 0

        for piece_type, value in self.piece_values.items():
            score += len(board.pieces(piece_type, chess.WHITE)) * value
            score -= len(board.pieces(piece_type, chess.BLACK)) * value

        return score

    # ==========================================
    # MINIMAX
    # ==========================================
    def alphabeta(self, board, depth, alpha, beta, is_maximizing):

        if depth == 0 or board.is_game_over():
            return self.evaluate(board)

        legal_moves = list(board.legal_moves)

        if is_maximizing:

            max_eval = -float("inf")

            for move in legal_moves:

                board.push(move)
                eval_score = self.alphabeta(board, depth - 1, alpha, beta, False)
                board.pop()

                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)

                # PRUNE
                if beta <= alpha:
                    break

            return max_eval

        else:

            min_eval = float("inf")

            for move in legal_moves:

                board.push(move)
                eval_score = self.alphabeta(board, depth - 1, alpha, beta, True)
                board.pop()

                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)

                # PRUNE
                if beta <= alpha:
                    break

            return min_eval

    # ==========================================
    # GET BEST MOVE
    # ==========================================
    def get_move(self, board: chess.Board):

        print(f"[ENGINE EVAL ROOT] {self.evaluate(board)}")

        legal_moves = list(board.legal_moves)

        if not legal_moves:
            return None

        best_move = None

        is_maximizing = (board.turn == chess.WHITE)

        best_value = -float("inf") if is_maximizing else float("inf")

        alpha = -float("inf")
        beta = float("inf")

        for move in legal_moves:

            board.push(move)

            value = self.alphabeta(
                board,
                self.depth - 1,
                alpha,
                beta,
                not is_maximizing
            )

            board.pop()

            print(f"Move {move} -> {value}")

            if is_maximizing:

                if value > best_value:
                    best_value = value
                    best_move = move

                alpha = max(alpha, value)

            else:

                if value < best_value:
                    best_value = value
                    best_move = move

                beta = min(beta, value)

        print(f"[ENGINE CHOSEN] {best_move} with value {best_value}")

        return best_move