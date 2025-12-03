import random
import sys
from phe import paillier
import numpy as np

BOARD_SIZE = 10
BOARD_DIM = BOARD_SIZE * BOARD_SIZE
SHIP_SIZES = [5, 4, 3, 2, 2]


def initialize_board():
    """Initializes an empty 10x10 board (100 zeros)."""
    # The board is flattened into a 1D array for easier indexing and encryption.
    return np.zeros(BOARD_DIM, dtype=int)

def coord_to_index(x, y):
    """Converts (x, y) coordinates (Row, Col) to a flat index (0-99)."""
    if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
        return x * BOARD_SIZE + y
    raise ValueError("Coordinate out of bounds (0-9).")

def index_to_coord(i):
    """Converts a flat index (0-99) back to (x, y) coordinates (Row, Col)."""
    if 0 <= i < BOARD_DIM:
        x = i // BOARD_SIZE
        y = i % BOARD_SIZE
        return x, y
    raise ValueError("Index out of bounds (0-99).")

def check_neighbors(board, x, y):
    """
    Checks if any neighboring cell (including diagonals) of (x, y)
    already contains a ship segment. Returns True if a ship is found nearby.
    """
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            # Skip the center cell itself
            if dx == 0 and dy == 0:
                continue
            
            nx, ny = x + dx, y + dy
            # Check boundary conditions
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                if board[coord_to_index(nx, ny)] == 1:
                    return True # Found an adjacent ship
    return False

def can_place_ship(board, x, y, size, orientation):
    """
    Checks if a ship of a given size can be placed at (x, y) without
    going out of bounds, overlapping, OR touching any existing ships.
    orientation: 0 for horizontal, 1 for vertical.
    """
    if orientation == 0:  # Horizontal
        if y + size > BOARD_SIZE:
            return False
        for dy in range(size):
            cx, cy = x, y + dy
            # 1. Check for overlap (ship must be placed on water)
            if board[coord_to_index(cx, cy)] == 1:
                return False
            # 2. Check for adjacent ships (no touching rule)
            if check_neighbors(board, cx, cy):
                return False
    
    elif orientation == 1:  # Vertical
        if x + size > BOARD_SIZE:
            return False
        for dx in range(size):
            cx, cy = x + dx, y
            # 1. Check for overlap
            if board[coord_to_index(cx, cy)] == 1:
                return False
            # 2. Check for adjacent ships
            if check_neighbors(board, cx, cy):
                return False
                
    return True

def place_ships(board, ship_sizes):
    """
    Places contiguous ships randomly (horizontal or vertical) on the board.
    Includes boundary, overlap, and 'no touching' checks.
    """
    for size in ship_sizes:
        placed = False
        attempts = 0
        while not placed and attempts < 2000: # Increased limit for successful placement
            attempts += 1
            
            # 1. Randomly select starting point (x, y) and orientation
            x = random.randint(0, BOARD_SIZE - 1)
            y = random.randint(0, BOARD_SIZE - 1)
            orientation = random.randint(0, 1) # 0: Horizontal, 1: Vertical
            
            if can_place_ship(board, x, y, size, orientation):
                # Placement is valid, mark the ship segments
                if orientation == 0: # Horizontal
                    for dy in range(size):
                        board[coord_to_index(x, y + dy)] = 1
                elif orientation == 1: # Vertical
                    for dx in range(size):
                        board[coord_to_index(x + dx, y)] = 1
                
                placed = True

        if not placed:
            print(f"Warning: Failed to place ship of size {size} after many attempts. Board might be too full.")
            # If placement fails, the board state is returned as-is (possibly incomplete).
            
    return board

def display_board(board):
    """Prints the 10x10 board for debug purposes."""
    print("   0 1 2 3 4 5 6 7 8 9")
    print("  --------------------")
    for i in range(BOARD_SIZE):
        row = board[i * BOARD_SIZE : (i + 1) * BOARD_SIZE]
        # Use a dot for 0 (water) and 'S' for 1 (ship) for cleaner display
        row_str = " ".join(['S' if x == 1 else '.' for x in row])
        print(f"{i}| {row_str}")

# --- MAIN GAME LOOP ---

def main():
    print("=============================================")
    print("   HOMOMORPHIC BATTLESHIP (2-Player 10x10)   ")
    print("=============================================\n")

    # --- PART 1: SETUP ---
    # 1. Key Generation
    print("1. Key Generation and Exchange...")
    # Alice's keys
    pub_A, priv_A = paillier.generate_paillier_keypair()
    # Bob's keys
    pub_B, priv_B = paillier.generate_paillier_keypair()
    
    # 2. Board Setup
    print("2. Board Setup (Contiguous Ships Placed)...")
    board_A = place_ships(initialize_board(), SHIP_SIZES)
    board_B = place_ships(initialize_board(), SHIP_SIZES)
    
    print("   [Debug] Alice's Ships (S = Ship, . = Water):")
    display_board(board_A)
    print("\n   [Debug] Bob's Ships (S = Ship, . = Water):")
    display_board(board_B)

    # 3. Encryption and Exchange
    # Defender encrypts their board using the ATTACKER'S public key.
    
    # E_B(Board_A): Alice's board is encrypted with Bob's public key
    encrypted_board_A = [pub_B.encrypt(int(x)) for x in board_A]
    # E_A(Board_B): Bob's board is encrypted with Alice's public key
    encrypted_board_B = [pub_A.encrypt(int(x)) for x in board_B]
    
    print("\n3. Encrypted boards exchanged. Game Start!\n")

    # --- PART 2: THE GAME LOOP ---
    attempts = 0
    ships_A_left = sum(SHIP_SIZES)
    ships_B_left = sum(SHIP_SIZES)

    while ships_A_left > 0 and ships_B_left > 0:
        attempts += 1
        print(f"\n--- Turn {attempts} ---")
        
        # --- SUB-TURN 1: ALICE ATTACKS BOB ---
        print("\n[ATTACKER: Alice] - [DEFENDER: Bob]")
        ships_B_left = take_turn(
            attacker_name="Alice", 
            defender_name="Bob", 
            attacker_priv_key=priv_A, 
            encrypted_board=encrypted_board_B, 
            ships_left=ships_B_left
        )

        # --- SUB-TURN 2: BOB ATTACKS ALICE ---
        if ships_A_left > 0:
            print("\n[ATTACKER: Bob] - [DEFENDER: Alice]")
            ships_A_left = take_turn(
                attacker_name="Bob", 
                defender_name="Alice", 
                attacker_priv_key=priv_B, 
                encrypted_board=encrypted_board_A, 
                ships_left=ships_A_left
            )

    # --- PART 3: GAME OVER ---
    if ships_A_left == 0 and ships_B_left == 0:
        print("\n*** DRAW! Both players sank all ships! ***")
    elif ships_B_left == 0:
        print(f"\n*** GAME OVER! Alice wins in {attempts} turns! ***")
    else: # ships_A_left == 0
        print(f"\n*** GAME OVER! Bob wins in {attempts} turns! ***")

def take_turn(attacker_name, defender_name, attacker_priv_key, encrypted_board, ships_left):
    """Handles one attack turn (Attacker guesses, Network computes, Attacker decrypts)."""
    
    # 1. Attacker's Move
    while True:
        try:
            guess_input = input(f"   [{attacker_name}] Enter guess (x,y) [Row,Col]: ")
            x, y = map(int, guess_input.replace(' ', '').split(','))
            guess_index = coord_to_index(x, y)
            break
        except ValueError:
            print("   ! Invalid input. Please enter coordinates like '3,5' (Row, Column 0-9).")
        except Exception:
            print("   ! Invalid input format.")

    # 2. Network's Job (Homomorphic Check)
    # The network gets the encrypted cell E(B[i_guess]) from the defender's board.
    encrypted_cell = encrypted_board[guess_index]
    
    # Homomorphic Subtraction: E(cell value) - E(1)
    # E(1) - E(1) = E(0) if HIT
    # E(0) - E(1) = E(-1) if MISS
    # The library allows E(a) - b, which is E(a) + E(-b)
    encrypted_difference = encrypted_cell - 1
    
    # Blinding
    # If the difference is E(0) (HIT), the result is E(0 * factor) = E(0).
    # If the difference is E(-1) (MISS), the result is E(-1 * factor) = E(Noise).
    blinding_factor = random.randint(1, 9999)
    encrypted_result = encrypted_difference * blinding_factor
    
    # 3. Attacker's Verification
    # The attacker decrypts the result using their private key.
    decrypted_val = attacker_priv_key.decrypt(encrypted_result)

    # 4. Announce Result
    if decrypted_val == 0:
        ships_left -= 1
        print(f"   [Homomorphic Check Result] Decrypted value is 0.")
        print(f"   *** BOOM! {attacker_name} hit {defender_name} at ({x},{y})! ***")
        print(f"   {defender_name} has {ships_left} ship segments remaining.")
        
        # Mark the cell as hit on the encrypted board to prevent re-hitting.
        # We replace the ciphertext with E(99) (a non-zero/non-one value) using the
        # attacker's public key (which was used to encrypt the board initially).
        encrypted_board[guess_index] = attacker_priv_key.public_key.encrypt(99) 
        
    else:
        print(f"   [Homomorphic Check Result] Decrypted value is {decrypted_val}.")
        print("   --- MISS ---")
    
    return ships_left

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGame exited.")
        sys.exit()
    except ValueError as e:
        print(f"\nError: {e}. Please ensure inputs are correct and within bounds.")
        sys.exit()