import pygame
import chess
import chess.pgn
from engines.classical import ClassicalEngine

# ==========================================
# CONFIG
# ==========================================

ENGINE_ENABLED = True
ENGINE_COLOR = chess.BLACK

WIDTH = 800
HEIGHT = 800
SQ_SIZE = WIDTH // 8

LIGHT = (240, 217, 181)
DARK = (181, 136, 99)
SELECT_COLOR = (246, 246, 105)

PIECE_SCALE = 0.90
PIECE_SIZE = int(SQ_SIZE * PIECE_SCALE)
PIECE_OFFSET = (SQ_SIZE - PIECE_SIZE) // 2

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess")

font = pygame.font.SysFont(None, 40)
engine_pending = False
game = chess.pgn.Game()
node = game
board = chess.Board()
engine = ClassicalEngine()
game.headers["Event"] = "Engine Game"
game.headers["Site"] = "Local"
game.headers["White"] = "Engine" if ENGINE_COLOR == chess.WHITE else "Human"
game.headers["Black"] = "Engine" if ENGINE_COLOR == chess.BLACK else "Human"

game_over = False
result_text = ""

# ==========================================
# PIECES
# ==========================================

piece_images = {}

piece_map = {
    'P': 'wp.png',
    'N': 'wn.png',
    'B': 'wb.png',
    'R': 'wr.png',
    'Q': 'wq.png',
    'K': 'wk.png',
    'p': 'bp.png',
    'n': 'bn.png',
    'b': 'bb.png',
    'r': 'br.png',
    'q': 'bq.png',
    'k': 'bk.png'
}

for piece, filename in piece_map.items():
    img = pygame.image.load(f"assets/{filename}")
    img = pygame.transform.smoothscale(img, (PIECE_SIZE, PIECE_SIZE))
    piece_images[piece] = img

# ==========================================
# DRAG STATE
# ==========================================

dragging = False
drag_piece = None
drag_from = None

mouse_x = 0
mouse_y = 0

# ==========================================
# GAME OVER CHECK
# ==========================================

def check_game_over():
    global game_over, result_text

    if board.is_game_over():

        game_over = True
        outcome = board.outcome()

        if outcome is None:
            result_text = "Draw"
        elif outcome.winner is None:
            result_text = "Draw"
        elif outcome.winner:
            result_text = "White Wins"
        else:
            result_text = "Black Wins"

# ==========================================
# DRAW BOARD
# ==========================================

def draw_board():

    for row in range(8):
        for col in range(8):

            color = LIGHT if (row + col) % 2 == 0 else DARK

            pygame.draw.rect(
                screen,
                color,
                (col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            )

    if dragging and drag_from is not None:

        col = chess.square_file(drag_from)
        row = 7 - chess.square_rank(drag_from)

        pygame.draw.rect(
            screen,
            SELECT_COLOR,
            (col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        )

# ==========================================
# DRAW PIECES
# ==========================================

def draw_pieces():

    for square in chess.SQUARES:

        if dragging and square == drag_from:
            continue

        piece = board.piece_at(square)

        if piece:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)

            screen.blit(
                piece_images[piece.symbol()],
                (col * SQ_SIZE + PIECE_OFFSET,
                 row * SQ_SIZE + PIECE_OFFSET)
            )

    if dragging and drag_piece:

        rect = piece_images[drag_piece.symbol()].get_rect()
        rect.center = (mouse_x, mouse_y)

        screen.blit(piece_images[drag_piece.symbol()], rect)

# ==========================================
# PROMOTION MENU
# ==========================================

def show_promotion_menu():

    choices = [
        ("Q", chess.QUEEN),
        ("R", chess.ROOK),
        ("B", chess.BISHOP),
        ("N", chess.KNIGHT)
    ]

    menu_rect = pygame.Rect(WIDTH//2 - 160, HEIGHT//2 - 50, 320, 100)

    while True:

        pygame.draw.rect(screen, (220, 220, 220), menu_rect)
        pygame.draw.rect(screen, (0, 0, 0), menu_rect, 2)

        for i, (label, _) in enumerate(choices):

            option = pygame.Rect(menu_rect.x + i * 80, menu_rect.y, 80, 100)

            pygame.draw.rect(screen, (200, 200, 200), option, 1)

            text = font.render(label, True, (0, 0, 0))
            screen.blit(text, text.get_rect(center=option.center))

        pygame.display.flip()

        for event in pygame.event.get():

            if event.type == pygame.MOUSEBUTTONDOWN:

                mx, my = event.pos

                for i, (_, piece_type) in enumerate(choices):

                    option = pygame.Rect(menu_rect.x + i * 80, menu_rect.y, 80, 100)

                    if option.collidepoint(mx, my):
                        return piece_type

# ==========================================
# ENGINE
# ==========================================
def save_game_pgn(game, filename="engine_game.pgn"):
    with open(filename, "w", encoding="utf-8") as f:
        exporter = chess.pgn.FileExporter(f)
        game.accept(exporter)

def make_engine_move():
    global node
    if game_over:
        return

    if not ENGINE_ENABLED:
        return

    if board.turn != ENGINE_COLOR:
        return

    move = engine.get_move(board)

    if move in board.legal_moves:
        board.push(move)
        node = node.add_variation(move)
        check_game_over()

# ==========================================
# GAME OVER POPUP
# ==========================================

def show_game_over_popup():

    global result_text

    popup = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 80, 300, 160)

    while True:

        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, (240, 240, 240), popup)
        pygame.draw.rect(screen, (0, 0, 0), popup, 2)

        title = font.render(result_text, True, (0, 0, 0))
        screen.blit(title, title.get_rect(center=(WIDTH//2, HEIGHT//2 - 20)))

        sub = pygame.font.SysFont(None, 28).render(
            "Click anywhere to exit", True, (50, 50, 50)
        )
        screen.blit(sub, sub.get_rect(center=(WIDTH//2, HEIGHT//2 + 30)))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type in (pygame.QUIT, pygame.MOUSEBUTTONDOWN):
                pygame.quit()
                raise SystemExit

# ==========================================
# START ENGINE MOVE (if black)
# ==========================================

if ENGINE_ENABLED and ENGINE_COLOR == chess.WHITE:
    make_engine_move()

# ==========================================
# MAIN LOOP
# ==========================================

running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        # ==========================
        # MOUSE DOWN
        # ==========================

        elif event.type == pygame.MOUSEBUTTONDOWN:

            if game_over:
                continue

            x, y = event.pos

            col = x // SQ_SIZE
            row = y // SQ_SIZE

            square = chess.square(col, 7 - row)
            piece = board.piece_at(square)

            if piece:
                dragging = True
                drag_piece = piece
                drag_from = square
                mouse_x, mouse_y = x, y

        # ==========================
        # MOUSE MOVE
        # ==========================

        elif event.type == pygame.MOUSEMOTION:
            mouse_x, mouse_y = event.pos

        # ==========================
        # MOUSE UP
        # ==========================

        elif event.type == pygame.MOUSEBUTTONUP:

            if dragging and not game_over:

                x, y = event.pos

                col = x // SQ_SIZE
                row = y // SQ_SIZE

                target = chess.square(col, 7 - row)

                piece = board.piece_at(drag_from)

                promotion = None

                if piece and piece.piece_type == chess.PAWN:
                    if chess.square_rank(target) in (0, 7):
                        promotion = show_promotion_menu()

                move = chess.Move(drag_from, target, promotion=promotion)

                if move in board.legal_moves:
                    board.push(move)
                    node = node.add_variation(move)
                    check_game_over()
                    engine_pending = True

            dragging = False
            drag_piece = None
            drag_from = None

    # ==========================
    # RENDER
    # ==========================

    draw_board()
    draw_pieces()

    pygame.display.flip()
    if engine_pending and not dragging and not game_over:
        make_engine_move()
        engine_pending = False
    # engine fallback safety (optional but good)
    if not dragging and not game_over:
        make_engine_move()

    # ==========================
    # GAME OVER
    # ==========================

    if game_over:
        show_game_over_popup()
save_game_pgn(game, f"results/game1.pgn")
pygame.quit()