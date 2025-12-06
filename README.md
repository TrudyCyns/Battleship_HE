# Homomorphic Battleship (2D, Two-Player)

This project implements a two-player, 10x10 version of the classic Battleship game where the core "hit/miss" check is performed using Paillier Homomorphic Encryption (HE).

The primary goal is to demonstrate how two parties (Alice and Bob) can determine if a guessed coordinate hits a ship without revealing the defender's full board or the attacker's precise guess location to a third-party Network.

## Homomorphic Encryption Principle

The game relies on the additive homomorphic properties of the Paillier cryptosystem.

In a standard battleship game, the server knows the ship locations and the guess. In this version, the Network uses the following homomorphic operation to perform the check:

1. **Defender's Board**: Each cell value is individually encrypted using the Attacker's Public Key.
2. **Server Computation (Hit Check)**: The Server computes the difference between the encrypted cell value and an encrypted '1'.
$$E_{Result} = \big(E_{Pub_A}(B_{cell}) - 1\big) \times \text{Random Blinder}$$

- If **Hit** ($B_{cell}=1$): $E_{Pub_A}(1) - 1 = E_{Pub_A}(0)$, the result remains $E_{Pub_A}(0)$ after blinding.
- If **Miss** ($B_{cell}=0$): $E_{Pub_A}(0) - 1 = E_{Pub_A}(-1)$. The result becomes a large, random number $E_{Pub_A}(\text{Noise})$.

3. **Attacker Decryption**: The Attacker decrypts $E_{Result}$ using their Private Key ($D_{Priv_A}$).

- If the decrypted value is **0**, it's a **HIT**.
- If the decrypted value is **Non-Zero**, it's a **MISS** (or a re-hit).

This setup allows the Attacker to verify the outcome without the Defender (or the Network) ever seeing the clear value of the cell.

## Setup and Installation

This project requires `Python 3.x`, `numpy` for board management, the `phe` library for Paillier encryption, and uv for setup.

### Prerequisites

You must have `uv` installed.

#### 1. Create Virtual Environment and Install

Use `uv` to set up and install dependencies:

``` bash
# 1. Create a virtual environment
uv venv

# 2. Activate the environment (Linux/macOS)
source .venv/bin/activate
# Or for Windows PowerShell: .venv\Scripts\Activate.ps1

# 3. Install dependencies
uv add numpy phe
```

### Running the Game

Execute the main script from your terminal:

```bash
uv sync

uv run main.py
```

#### Gameplay Instructions

1. The game will initialize keys and boards for Alice and Bob, showing the debug placement of the ships (contiguous, non-touching, horizontal or vertical).
2. Players take turns attacking.
3. When prompted, enter coordinates as Row, Column (e.g., 3,5).
4. The system will output the result of the homomorphic check (either 0 for a Hit or Random Noise for a Miss).
5. The game ends when one player runs out of ship segments.

#### Board and Placement Rules

- **Board Size**: 10x10 grid (0-9 for both rows and columns).
- **Ships**: The game uses 5 ships with sizes: 5, 4, 3, 2, 2.
- **Placement**: Ships are placed randomly and are guaranteed to be contiguous (forming a straight line) and non-adjacent (they cannot touch horizontally, vertically, or diagonally).
