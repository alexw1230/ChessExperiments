import chess
import random
import time
MATE = 1000000000
class ClassicalEngine:

    def __init__(self, depth=4):

        self.depth = depth

        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 0
        }
        self.zobrist_table = {}
        self.init_zobrist()
        self.tt = {}
        self.history = {}
        self.nodes = 0
        self.qnodes = 0
        self.pv_move = None
        self.killer_moves = {}  # depth -> [move1, move2]
        self.pst = {
    chess.PAWN: [
         0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
         5,  5, 10, 25, 25, 10,  5,  5,
         0,  0,  0, 20, 20,  0,  0,  0,
         5, -5,-10,  0,  0,-10, -5,  5,
         5, 10, 10,-20,-20, 10, 10,  5,
         0,  0,  0,  0,  0,  0,  0,  0,
    ],

    chess.KNIGHT: [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50,
    ],

    chess.BISHOP: [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20,
    ],

    chess.ROOK: [
         0,  0,  0,  5,  5,  0,  0,  0,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
         5, 10, 10, 10, 10, 10, 10,  5,
         0,  0,  0,  0,  0,  0,  0,  0,
    ],

    chess.QUEEN: [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
         -5,  0,  5,  5,  5,  5,  0, -5,
          0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20,
    ],

    chess.KING: [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
         20, 20,  0,  0,  0,  0, 20, 20,
         20, 30, 10,  0,  0, 10, 30, 20,
    ]
}
    def init_zobrist(self):

        pieces = [
            chess.PAWN, chess.KNIGHT, chess.BISHOP,
            chess.ROOK, chess.QUEEN, chess.KING
        ]

        self.zobrist_table = {}

        for square in chess.SQUARES:
            for piece in pieces:
                self.zobrist_table[(piece, chess.WHITE, square)] = random.getrandbits(64)
                self.zobrist_table[(piece, chess.BLACK, square)] = random.getrandbits(64)

        self.zobrist_black_to_move = random.getrandbits(64)
    def compute_hash(self, board):
        h = 0

        for square in chess.SQUARES:

            piece = board.piece_at(square)

            if piece:

                h ^= self.zobrist_table[(piece.piece_type, piece.color, square)]

        if board.turn == chess.BLACK:
            h ^= self.zobrist_black_to_move

        return h
    def pst_value(self, piece_type, square, color):

        value = self.pst[piece_type]

        # flip board for black
        if color == chess.WHITE:
            return value[square]
        else:
            return value[chess.square_mirror(square)]
    def see_score(self, board, move):
        if not board.is_capture(move):
            return 0

        from_piece = board.piece_at(move.from_square)
        to_piece = board.piece_at(move.to_square)

        if not from_piece or not to_piece:
            return 0

        return self.piece_values[to_piece.piece_type] - self.piece_values[from_piece.piece_type]
    def is_quiet(self, board):

        # If any capture exists, it's not quiet
        for move in board.legal_moves:
            if board.is_capture(move):
                return False

        return True
    def quiescence(self, board, alpha, beta, depth):
        self.qnodes += 1

        # -------------------------------------------------
        # HARD STOP (FIX 3: depth cap for quiescence)
        # -------------------------------------------------
        if depth >= 6:
            return self.evaluate(board)

        stand_pat = self.evaluate(board)
        DELTA_MARGIN = 200
        # -------------------------------------------------
        # MAX NODE (WHITE)
        # -------------------------------------------------
        if board.turn == chess.WHITE:

            if stand_pat >= beta:
                return beta

            alpha = max(alpha, stand_pat)

            # only consider "good enough" captures (delta pruning light)
            moves = [
            m for m in board.legal_moves
            if board.is_capture(m)
            and self.see_score(board, m) >= -50   # threshold tunable
            ]

            # MVV-LVA style ordering (simple but effective)
            moves.sort(
                key=lambda m: self.see_score(board, m),
                reverse=True
            )

            for move in moves:
                captured = board.piece_at(move.to_square)

                captured_value = (
                    self.piece_values[captured.piece_type]
                    if captured else 0
                )

                if stand_pat + captured_value + DELTA_MARGIN < alpha:
                    continue
                board.push(move)
                score = self.quiescence(board, alpha, beta, depth + 1)
                board.pop()

                if score > alpha:
                    alpha = score

                if alpha >= beta:
                    break

            return alpha

        # -------------------------------------------------
        # MIN NODE (BLACK)
        # -------------------------------------------------
        else:

            if stand_pat <= alpha:
                return alpha

            beta = min(beta, stand_pat)

            moves = [
                m for m in board.legal_moves
                if board.is_capture(m)
                and self.see_score(board, m) >= 0
            ]

            moves.sort(
                key=lambda m: self.see_score(board, m),
                reverse=True
            )

            for move in moves:
                captured = board.piece_at(move.to_square)

                captured_value = (
                    self.piece_values[captured.piece_type]
                    if captured else 0
                )

                if stand_pat - captured_value - DELTA_MARGIN > beta:
                    continue
                board.push(move)
                score = self.quiescence(board, alpha, beta, depth + 1)
                board.pop()

                if score < beta:
                    beta = score

                if beta <= alpha:
                    break

            return beta
    def order_moves(self, board, moves, depth):

        def score_move(move):
            if self.pv_move is not None and move == self.pv_move:
                return 100000000
            score = 0
            move_key = move.uci()

            # --------------------------------------------------
            # 1. TRANSPOSITION TABLE BEST MOVE (VERY IMPORTANT)
            # --------------------------------------------------
            # if depth >= 3:
            #     key = self.compute_hash(board)
            #     if key in self.tt:
            #         # optional: you can later store best move separately
            #         pass

            # --------------------------------------------------
            # 2. KILLER MOVES (depth-specific tactical moves)
            # --------------------------------------------------
            if depth in self.killer_moves:
                if move in self.killer_moves[depth]:
                    score += 100000

            # --------------------------------------------------
            # 3. HISTORY HEURISTIC (global learned success)
            # --------------------------------------------------
            if move_key in self.history:
                score += self.history[move_key]

            # --------------------------------------------------
            # 4. CAPTURES (MVV-LVA style)
            # --------------------------------------------------
            if board.is_capture(move):
                if self.see_score(board, move) < 0:
                    score -= 10000   # blunder capture
                else:
                    score += 500

            # # --------------------------------------------------
            # # 5. CHECKS
            # # --------------------------------------------------
            # board.push(move)
            # if board.is_check():
            #     score += 5000
            # board.pop()

            # --------------------------------------------------
            # 6. CENTER CONTROL
            # --------------------------------------------------
            if move.to_square in [27, 28, 35, 36]:
                score += 50

            return score

        return sorted(moves, key=score_move, reverse=True)
    def search(self, board, depth, is_maximizing):

        alpha = -float("inf")
        beta = float("inf")

        best_move = None
        best_value = -float("inf") if is_maximizing else float("inf")

        key = self.compute_hash(board)

        # -------------------------------------------------
        # TT MOVE (SAFE EXTRACTION)
        # -------------------------------------------------
        tt_move = None
        if key in self.tt:
            entry = self.tt[key]
            if len(entry) == 3:
                tt_move = entry[2]

        # -------------------------------------------------
        # MOVE ORDERING
        # -------------------------------------------------
        legal_moves = self.order_moves(board, list(board.legal_moves), depth)

        # boost TT move to front (if valid)
        if tt_move in legal_moves:
            legal_moves.remove(tt_move)
            legal_moves.insert(0, tt_move)

        # -------------------------------------------------
        # SEARCH LOOP
        # -------------------------------------------------
        for move in legal_moves:

            board.push(move)

            value = self.alphabeta(
                board,
                depth - 1,
                alpha,
                beta,
                not is_maximizing
            )

            board.pop()

            if is_maximizing:
                if value > best_value:
                    best_value = value
                    best_move = move
            else:
                if value < best_value:
                    best_value = value
                    best_move = move

        return best_move, best_value

    def evaluate(self, board: chess.Board) -> int:

        # ==========================================
        # TERMINAL STATES
        # ==========================================

        if board.is_checkmate():
            if board.turn == chess.WHITE:
                return -MATE - self.depth
            else:
                return MATE + self.depth

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

        for piece_type, base_value in self.piece_values.items():

            for square in board.pieces(piece_type, chess.WHITE):
                score += base_value
                score += self.pst_value(piece_type, square, chess.WHITE)

            for square in board.pieces(piece_type, chess.BLACK):
                score -= base_value
                score -= self.pst_value(piece_type, square, chess.BLACK)

        return score
    
    def alphabeta(self, board, depth, alpha, beta, is_maximizing):
        self.nodes += 1
        if depth >= 3:
            key = self.compute_hash(board)

        # -----------------------------------
        # TRANSPOSITION TABLE LOOKUP (simple)
        # -----------------------------------
            if depth >= 3 and key in self.tt:
                stored_depth, stored_value = self.tt[key]
                if stored_depth >= depth:
                    return stored_value

        # -----------------------------------
        # TERMINAL / LEAF CONDITIONS
        # -----------------------------------
        if board.is_checkmate():
            return -MATE + (1000 - depth) if board.turn == chess.WHITE else MATE - (1000 - depth)

        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        if depth == 0:
            return self.quiescence(board, alpha, beta, depth=0)

        # -----------------------------------
        # MOVE ORDERING
        # -----------------------------------
        legal_moves = self.order_moves(board, list(board.legal_moves), depth)

        # ======================================================
        # MAX NODE
        # ======================================================
        if is_maximizing:

            max_eval = -MATE

            for move in legal_moves:

                board.push(move)
                eval_score = self.alphabeta(
                    board,
                    depth - 1,
                    alpha,
                    beta,
                    False
                )
                board.pop()

                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)

                # -------------------------
                # CUTOFF
                # -------------------------
                if beta <= alpha:

                    move_key = move.uci()

                    # HISTORY HEURISTIC
                    if move_key not in self.history:
                        self.history[move_key] = 0
                    self.history[move_key] += depth * depth

                    # KILLER MOVES
                    depth_key = depth

                    if depth_key not in self.killer_moves:
                        self.killer_moves[depth_key] = []

                    if move not in self.killer_moves[depth_key]:
                        self.killer_moves[depth_key].insert(0, move)

                    self.killer_moves[depth_key] = self.killer_moves[depth_key][:2]

                    break
            if depth >= 3:
                self.tt[key] = (depth, max_eval, legal_moves[0] if legal_moves else None)
            return max_eval

        # ======================================================
        # MIN NODE
        # ======================================================
        else:

            min_eval = MATE

            for move in legal_moves:

                board.push(move)
                eval_score = self.alphabeta(
                    board,
                    depth - 1,
                    alpha,
                    beta,
                    True
                )
                board.pop()

                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)

                # -------------------------
                # CUTOFF
                # -------------------------
                if beta <= alpha:

                    move_key = move.uci()

                    # HISTORY HEURISTIC
                    if move_key not in self.history:
                        self.history[move_key] = 0
                    self.history[move_key] += depth * depth

                    # KILLER MOVES
                    depth_key = depth

                    if depth_key not in self.killer_moves:
                        self.killer_moves[depth_key] = []

                    if move not in self.killer_moves[depth_key]:
                        self.killer_moves[depth_key].insert(0, move)

                    self.killer_moves[depth_key] = self.killer_moves[depth_key][:2]

                    break

            if depth >= 3:
                self.tt[key] = (depth, min_eval, legal_moves[0] if legal_moves else None)
            return min_eval

    def get_move(self, board):

        start = time.time()
        self.nodes = 0
        self.qnodes = 0
        legal_moves = list(board.legal_moves)

        if not legal_moves:
            print("[ENGINE] No legal moves!")
            return None

        if len(legal_moves) == 1:
            return legal_moves[0]

        is_maximizing = (board.turn == chess.WHITE)

        # reset PV move for this position
        self.pv_move = None

        best_move = legal_moves[0]
        best_value = 0

        print(f"[ENGINE ROOT] evaluating {len(legal_moves)} moves")

        for current_depth in range(1, self.depth + 1):

            move, value = self.search(
                board,
                current_depth,
                is_maximizing
            )

            if move is not None:
                best_move = move
                best_value = value

                # use previous iteration's best move
                # for move ordering in the next iteration
                self.pv_move = move

            print(
                f"[ITERATION {current_depth}] "
                f"{best_move} -> {best_value}"
            )

        elapsed = time.time() - start

        print(f"[ENGINE CHOSEN] {best_move} with value {best_value}")
        print(f"[NODES SEARCHED] {self.nodes} in {elapsed:.4f} seconds")
        print(f"[Q NODES] {self.qnodes}")

        return best_move