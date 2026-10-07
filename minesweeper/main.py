"""
Name: main.py
Function: Start Minesweeper, draw the board, and handle player and computer turns.
Inputs: Number of mines, game mode, keyboard and mouse events
Outputs: Pygame window, win and loss status
External sources: pygame documentation for reference, VScode Copilot
Authors: Mo Osby, Drew Franke, Vrishank Kulkarni, Alex Lanter
Date Created: 09/12/2026
Date Last Edited: 09/20/2026
"""
import pygame
from board import Board
from controller import GameController
from solver import choose_move

pygame.init()
screen = pygame.display.set_mode((650, 700))
pygame.display.set_caption("Minesweeper")
font = pygame.font.Font("assets/ThaleahFat.ttf", 32)
small_font = pygame.font.Font("assets/ThaleahFat.ttf", 24)
clock = pygame.time.Clock()
mode_names = {"human_vs_ai": "Human vs. computer", "ai_only": "Computer solves alone"}
mode_buttons = {
    "human_vs_ai": pygame.Rect(100, 435, 450, 50),
    "ai_only": pygame.Rect(100, 500, 450, 50),
}


def draw_input_screen(user_input, error, selected_mode):
    #display the input screen for the number of mines
    #original function written with help from assitive inline suggestions (VScode Copilot)
    screen.fill("white")
    #title text
    title_text = font.render("Minesweeper", True, "black")
    screen.blit(title_text, (650 // 2 - title_text.get_width() // 2, 200))
    #instructions text
    instructions_text = small_font.render("Select number of mines (10-20):", True, "black")
    screen.blit(instructions_text, (650 // 2 - instructions_text.get_width() // 2, 270))

    #input box
    input_box = pygame.Rect(275, 320, 100, 40)
    pygame.draw.rect(screen, "lightgray", input_box)
    pygame.draw.rect(screen, "black", input_box, 2)
    typed = font.render(user_input, True, "black")
    screen.blit(typed, (input_box.x + 10, input_box.y + 5))
    #hint text
    hint = small_font.render("Backspace to edit. Enter to start.", True, "gray")
    screen.blit(hint, (650 // 2 - hint.get_width() // 2, 380))

    for mode, button in mode_buttons.items():
        color = "lightblue" if mode == selected_mode else "lightgray"
        pygame.draw.rect(screen, color, button)
        label = mode_names[mode] + (" [H]" if mode == "human_vs_ai" else " [C]")
        text = small_font.render(label, True, "black")
        screen.blit(text, (650 // 2 - text.get_width() // 2, button.y + 13))
    #error handling
    if error:
        error_text = small_font.render(error, True, "red")
        screen.blit(error_text, (650 // 2 - error_text.get_width() // 2, 580))
    pygame.display.flip()


user_input = ""
error = ""
selected_mode = "human_vs_ai"
at_start = True
running = True
ai_delay_ms = 500

while running:
    while at_start and running:
        #display input screen
        draw_input_screen(user_input, error, selected_mode)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if not at_start:
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for mode, button in mode_buttons.items():
                    if button.collidepoint(event.pos):
                        selected_mode = mode
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h:
                    selected_mode = "human_vs_ai"
                elif event.key == pygame.K_c:
                    selected_mode = "ai_only"
                elif event.key == pygame.K_RETURN:
                    if user_input.isascii() and user_input.isdigit() and 10 <= int(user_input) <= 20:
                        num_mines = int(user_input)
                        at_start = False
                        error = ""
                        continue
                    error = "Please enter a number between 10 and 20."
                    user_input = ""
                elif event.key == pygame.K_BACKSPACE:
                    user_input = user_input[:-1]
                    error = ""
                elif event.unicode in "0123456789" and event.unicode and len(user_input) < 2:
                    user_input += event.unicode
                    error = ""
        clock.tick(60)

    if not running:
        break
    controller = GameController(num_mines=num_mines, mode=selected_mode)
    board = Board(controller)
    next_ai_move_at = pygame.time.get_ticks() + ai_delay_ms
    rejected_moves = set()
    solver_message = ""

    while running and not at_start:
        #main game loop
        # loop through events and keep game running unless user exits out of window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if at_start:
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    at_start = True
                    continue
                if event.key == pygame.K_r:
                    controller.new_game()
                    rejected_moves.clear()
                    solver_message = ""
                    next_ai_move_at = pygame.time.get_ticks() + ai_delay_ms
            if event.type == pygame.MOUSEBUTTONDOWN:
                result = "no_change"
                # handle left click actions
                if event.button == 1:
                    #left click to reveal cell
                    result = board.handle_click(*event.pos)
                # handle right click actions
                elif event.button == 3:
                    #right click to place flag
                    result = board.place_flag(*event.pos)
                if result != "no_change":
                    rejected_moves.clear()
                    solver_message = ""
                    next_ai_move_at = pygame.time.get_ticks() + ai_delay_ms

        if not running or at_start:
            break

        # Take one computer action when due, then return to events and drawing.
        now = pygame.time.get_ticks()
        if (controller.active_player == "computer" and not controller.game.game_over
                and not solver_message and now >= next_ai_move_at):
            next_ai_move_at = now + ai_delay_ms
            try:
                move = choose_move(controller.game.get_visible_board(), num_mines,
                                   rejected_moves=rejected_moves)
                if move is None:
                    solver_message = "No move available. Press R to restart."
                elif move in rejected_moves:
                    solver_message = "Computer could not make a move. Press R to restart."
                else:
                    result = controller.submit_action("computer", *move)
                    # Ignore clicks received during computer work; keep Quit and keys.
                    pygame.event.clear(pygame.MOUSEBUTTONDOWN)
                    if result == "no_change":
                        rejected_moves.add(move)
                    else:
                        rejected_moves.clear()
            except ValueError:
                solver_message = "Could not choose a move. Press R to restart."

        screen.fill("white")
        board.draw(screen)
        game = controller.game
        # Change the status text for playing/lose/win
        if game.game_over:
            if controller.mode == "ai_only":
                status_text = "Computer solved the board!" if game.won else "Computer lost!"
            else:
                status_text = "Human wins!" if controller.winner == "human" else "Computer wins!"
        elif solver_message:
            status_text = "Computer paused"
        else:
            status_text = "Human's turn" if controller.active_player == "human" else "Computer's turn"

        text = font.render(status_text, True, "black")
        #text placement
        screen.blit(text, (650 // 2 - text.get_width() // 2, 540))
        counts = f"Mines: {num_mines}   Flags left: {num_mines - len(game.flags)}   Moves: {controller.move_count}"
        text = small_font.render(counts, True, "black")
        screen.blit(text, (650 // 2 - text.get_width() // 2, 580))
        text = small_font.render(solver_message or mode_names[controller.mode], True, "black")
        screen.blit(text, (650 // 2 - text.get_width() // 2, 615))
        text = small_font.render("R: new game   Esc: mode selection", True, "black")
        screen.blit(text, (650 // 2 - text.get_width() // 2, 650))
        pygame.display.flip()
        clock.tick(60)

pygame.quit()
