import numpy as np

U = np.uint64

SBOX = np.array([0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD,
                 0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2], dtype=np.uint64)
ROUNDS = 4
CONSTS = [0x9E37, 0x7F4B, 0x85EB, 0xC2B3, 0x27D5]
MASK = U(0xFFFF)


def sub_nibbles(x):
    """Apply the S-box to each of the four 4-bit nibbles of a 16-bit block."""
    out = np.zeros_like(x)
    for i in range(4):
        s = U(4 * i)
        out |= SBOX[((x >> s) & U(0xF)).astype(np.intp)] << s
    return out


def permute_bits(x):
    """Move bit i to position 4*i mod 15 (bit 15 stays), as in PRESENT."""
    out = np.zeros_like(x)
    for i in range(16):
        j = 15 if i == 15 else (4 * i) % 15
        out |= ((x >> U(i)) & U(1)) << U(j)
    return out


def round_key(key, r):
    """A deliberately simple key schedule: 16 bits mixed out of the key."""
    k = np.asarray(key, dtype=np.uint64)
    return ((k * U(CONSTS[r])) ^ (k >> U(r + 1)) ^ (k << U(r + 5))) & MASK


def encrypt(p, key):
    """Toy 16-bit SPN: key whitening, then 4 rounds of S-box, permutation,
    round-key XOR. `p` and `key` may be ints or NumPy arrays (they broadcast)."""
    x = np.atleast_1d(np.asarray(p, dtype=np.uint64) ^ round_key(key, 0))
    for r in range(1, ROUNDS + 1):
        x = permute_bits(sub_nibbles(x)) ^ round_key(key, r)
    return x


def matching_keys(n, pairs):
    """All n-bit keys consistent with every (plaintext, ciphertext) pair.
    The first pair is tested on every key, later pairs only on survivors."""
    cand = np.arange(2 ** n, dtype=np.uint64)
    for p, c in pairs:
        cand = cand[encrypt(p, cand) == U(c)]
    return cand.astype(np.int64)