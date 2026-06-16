from itertools import permutations
import random
from dataclasses import dataclass

DIGITS = "0123456789"

@dataclass(frozen=True)
class Clue:
    guess: str
    bulls: int
    cows: int

    def text(self):
        b, c = self.bulls, self.cows
        texts = {
            (0, 0): "Nessuna cifra è presente",
            (1, 0): "Una cifra è corretta ed è al posto giusto",
            (0, 1): "Una cifra è corretta ma nel posto sbagliato",
            (2, 0): "Due cifre sono corrette ed entrambe al posto giusto",
            (0, 2): "Due cifre sono corrette ma nel posto sbagliato",
            (1, 1): "Una cifra è corretta al posto giusto e una nel posto sbagliato",
            (3, 0): "Tre cifre sono corrette ed al posto giusto",
            (0, 3): "Tre cifre sono corrette ma nel posto sbagliato",
            (2, 1): "Due cifre sono corrette al posto giusto e una nel posto sbagliato",
            (1, 2): "Una cifra è corretta al posto giusto e due nel posto sbagliato",
            (4, 0): "Quattro cifre sono corrette ed al posto giusto",
            (0, 4): "Quattro cifre sono corrette ma nel posto sbagliato",
            (2, 2): "Due cifre sono corrette al posto giusto e due nel posto sbagliato",
        }
        return texts.get((b, c), f"{b} cifre corrette al posto giusto e {c} nel posto sbagliato")

    def line(self):
        return f"{self.guess} → {self.text()}"


def evaluate(secret, guess):
    bulls = sum(a == b for a, b in zip(secret, guess))
    cows = sum(ch in secret for ch in guess) - bulls
    return bulls, cows


def all_codes(length):
    return ["".join(p) for p in permutations(DIGITS, length)]


def solutions_for(clues, candidates):
    out = []
    for code in candidates:
        if all(evaluate(code, c.guess) == (c.bulls, c.cows) for c in clues):
            out.append(code)
    return out


def every_clue_useful(clues, candidates):
    for i in range(len(clues)):
        reduced = clues[:i] + clues[i + 1:]
        if len(solutions_for(reduced, candidates)) == 1:
            return False
    return True


def zero_connected(zero_guess, clues):
    joined = "".join(c.guess for c in clues[1:])
    return all(d in joined for d in zero_guess)


def progression(clues, candidates):
    active = candidates[:]
    counts = []
    for clue in clues:
        active = [c for c in active if evaluate(c, clue.guess) == (clue.bulls, clue.cows)]
        counts.append(len(active))
    return counts


def score(clues, candidates):
    pairs = [(c.bulls, c.cows) for c in clues]
    counts = progression(clues, candidates)
    s = len(set(pairs)) * 4
    if pairs[0] == (0, 0):
        s += 10
    good = {(1,0),(0,1),(2,0),(0,2),(1,1),(3,0),(0,3),(2,1),(1,2)}
    s += sum(3 for p in pairs if p in good)
    if len(counts) >= 3 and counts[2] <= 2:
        s -= 20
    if len(counts) >= 4 and counts[3] == 1:
        s -= 8
    for a, b in zip(counts, counts[1:]):
        if b < a:
            s += 2
    return s


def generate(length=3, clue_count=5, max_attempts=200000):
    candidates = all_codes(length)
    best = None
    best_score = -10**9
    for _ in range(max_attempts):
        secret = random.choice(candidates)
        absent = [d for d in DIGITS if d not in secret]
        zero_guess = "".join(random.sample(absent, length))
        clues = [Clue(zero_guess, 0, 0)]
        used = {zero_guess, secret}

        tries = 0
        while len(clues) < clue_count and tries < 2000:
            tries += 1
            g = random.choice(candidates)
            if g in used:
                continue
            used.add(g)
            b, c = evaluate(secret, g)
            if (b, c) in [(0, 0), (length, 0)]:
                continue
            clues.append(Clue(g, b, c))

        if len(clues) != clue_count:
            continue
        if not zero_connected(zero_guess, clues):
            continue
        if solutions_for(clues, candidates) != [secret]:
            continue
        if not every_clue_useful(clues, candidates):
            continue

        sc = score(clues, candidates)
        if sc > best_score:
            best = (secret, clues)
            best_score = sc
        if sc >= 28:
            return secret, clues

    if best:
        return best
    raise RuntimeError("Nessun quiz trovato. Riprova o aumenta max_attempts.")


def print_quiz(length=3, clue_count=5):
    secret, clues = generate(length, clue_count)
    candidates = all_codes(length)
    counts = progression(clues, candidates)

    print("\n=== QUIZ ===\n")
    for c in clues:
        print(c.line())
    print("\nSOLUZIONE:", secret)
    print("Progressione soluzioni:", " → ".join(map(str, counts)))
    print("Soluzioni finali:", solutions_for(clues, candidates))


if __name__ == "__main__":
    print("104Quiz Generator")
    print("1 = 3 cifre / 2 = 4 cifre / 3 = 5 cifre")
    scelta = input("Scegli: ").strip()
    length = {"1": 3, "2": 4, "3": 5}.get(scelta, 3)
    clue_count = 5 if length < 5 else 6
    print_quiz(length, clue_count)
