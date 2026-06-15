import itertools
import random
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


DIGITS = "0123456789"


class Clue:
    def __init__(self, guess: str, bulls: int, cows: int):
        self.guess = guess
        self.bulls = bulls
        self.cows = cows

    def text(self) -> str:
        b, c = self.bulls, self.cows
        if b == 0 and c == 0:
            return "Nessuna cifra è presente"
        if b == 1 and c == 0:
            return "Una cifra è corretta ed è al posto giusto"
        if b == 0 and c == 1:
            return "Una cifra è corretta ma nel posto sbagliato"
        if b == 2 and c == 0:
            return "Due cifre sono corrette ed entrambe al posto giusto"
        if b == 0 and c == 2:
            return "Due cifre sono corrette ma nel posto sbagliato"
        if b == 1 and c == 1:
            return "Una cifra è corretta al posto giusto e una nel posto sbagliato"
        if b == 3 and c == 0:
            return "Tre cifre sono corrette ed al posto giusto"
        if b == 0 and c == 3:
            return "Tre cifre sono corrette ma nel posto sbagliato"
        if b == 2 and c == 1:
            return "Due cifre sono corrette al posto giusto e una nel posto sbagliato"
        if b == 1 and c == 2:
            return "Una cifra è corretta al posto giusto e due nel posto sbagliato"
        return f"{b} cifre corrette al posto giusto e {c} nel posto sbagliato"

    def line(self) -> str:
        return f"{self.guess} → {self.text()}"


def evaluate(secret: str, guess: str) -> tuple[int, int]:
    bulls = sum(s == g for s, g in zip(secret, guess))
    cows = sum(g in secret for g in guess) - bulls
    return bulls, cows


def all_codes(length: int) -> list[str]:
    return ["".join(p) for p in itertools.permutations(DIGITS, length)]


def valid_solutions(clues: list[Clue], length: int) -> list[str]:
    solutions = []
    for code in all_codes(length):
        if all(evaluate(code, clue.guess) == (clue.bulls, clue.cows) for clue in clues):
            solutions.append(code)
    return solutions


def clues_are_all_useful(clues: list[Clue], length: int) -> bool:
    """Ogni indizio deve servire: togliendone uno, le soluzioni diventano più di una."""
    for i in range(len(clues)):
        reduced = clues[:i] + clues[i + 1:]
        if len(valid_solutions(reduced, length)) == 1:
            return False
    return True


def score_clues(clues: list[Clue]) -> int:
    score = 0
    pairs = [(c.bulls, c.cows) for c in clues]

    # Preferiamo varietà: non 5 indizi tutti uguali.
    score += len(set(pairs)) * 3

    # Indizi utili nello stile TikTok/Mastermind.
    for b, c in pairs:
        if (b, c) == (0, 0):
            score += 4
        elif (b, c) in [(1, 0), (0, 1), (0, 2), (2, 0), (1, 1)]:
            score += 3
        elif b + c >= 3:
            score += 1

    # Evita quiz troppo rivelatori.
    if pairs.count((0, 0)) > 2:
        score -= 6
    if any(b == 3 for b, c in pairs):
        score -= 10

    return score


def generate_quiz(length: int = 3, clue_count: int = 5, require_all_useful: bool = True, max_attempts: int = 50000):
    codes = all_codes(length)

    best = None
    best_score = -999999

    for _ in range(max_attempts):
        secret = random.choice(codes)
        guesses = random.sample([c for c in codes if c != secret], clue_count)
        clues = [Clue(g, *evaluate(secret, g)) for g in guesses]

        # Scarta righe inutilizzabili o troppo ovvie.
        if any(c.bulls == length for c in clues):
            continue

        solutions = valid_solutions(clues, length)
        if solutions != [secret]:
            continue

        if require_all_useful and not clues_are_all_useful(clues, length):
            continue

        s = score_clues(clues)
        if s > best_score:
            best = (secret, clues)
            best_score = s

        # Buon risultato: fermiamoci.
        if s >= 18:
            return secret, clues

    if best:
        return best

    raise RuntimeError("Non sono riuscito a generare un quiz valido. Riprova.")


class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("104Quiz Generator")
        self.root.geometry("950x720")
        self.secret = None
        self.clues = []

        self.length_var = tk.IntVar(value=3)
        self.prev_solution_var = tk.StringVar(value="7496")
        self.show_solution_var = tk.BooleanVar(value=True)
        self.require_useful_var = tk.BooleanVar(value=True)

        self.build_ui()
        self.generate()

    def build_ui(self):
        top = ttk.Frame(self.root, padding=12)
        top.pack(fill="x")

        ttk.Label(top, text="Cifre:").pack(side="left")
        ttk.Radiobutton(top, text="3", variable=self.length_var, value=3).pack(side="left", padx=4)
        ttk.Radiobutton(top, text="4", variable=self.length_var, value=4).pack(side="left", padx=4)

        ttk.Label(top, text="Soluzione precedente:").pack(side="left", padx=(20, 4))
        ttk.Entry(top, textvariable=self.prev_solution_var, width=10).pack(side="left")

        ttk.Checkbutton(top, text="Tutti gli indizi devono servire", variable=self.require_useful_var).pack(side="left", padx=20)

        ttk.Button(top, text="🎲 Genera quiz", command=self.generate).pack(side="right", padx=4)
        ttk.Button(top, text="📋 Copia", command=self.copy_quiz).pack(side="right", padx=4)
        ttk.Button(top, text="🖼️ Esporta PNG", command=self.export_png).pack(side="right", padx=4)

        self.text = tk.Text(self.root, font=("Arial", 17), wrap="word", padx=16, pady=16)
        self.text.pack(fill="both", expand=True, padx=12, pady=8)

        bottom = ttk.Frame(self.root, padding=12)
        bottom.pack(fill="x")
        ttk.Label(bottom, text="Suggerimento: genera più volte finché trovi un quiz che ti piace. Il programma mostra solo quiz con una soluzione unica.").pack(anchor="w")

    def generate(self):
        try:
            self.secret, self.clues = generate_quiz(
                length=self.length_var.get(),
                clue_count=5,
                require_all_useful=self.require_useful_var.get(),
            )
        except Exception as e:
            messagebox.showerror("Errore", str(e))
            return
        self.render_text()

    def quiz_text(self, include_solution: bool = True) -> str:
        lines = []
        prev = self.prev_solution_var.get().strip()
        if prev:
            lines.append(f"🔓 SOLUZIONE PRECEDENTE: {prev}")
            lines.append("")
        lines.append("🔒 IL 99% SBAGLIA QUESTO QUIZ")
        lines.append(f"TROVA IL CODICE A {self.length_var.get()} CIFRE")
        lines.append("")
        for clue in self.clues:
            lines.append(clue.line())
        lines.append("")
        lines.append("❓ QUAL È IL CODICE?")
        lines.append("⬜ " * self.length_var.get())
        lines.append("")
        lines.append(f"💬 SCRIVI SOLO LE {self.length_var.get()} CIFRE NEI COMMENTI")
        if include_solution:
            lines.append("")
            lines.append(f"✅ SOLUZIONE: {self.secret}")
            lines.append(f"🔎 Soluzioni trovate dal verificatore: {valid_solutions(self.clues, self.length_var.get())}")
        return "\n".join(lines)

    def render_text(self):
        self.text.delete("1.0", "end")
        self.text.insert("end", self.quiz_text(include_solution=True))

    def copy_quiz(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.quiz_text(include_solution=True))
        messagebox.showinfo("Copiato", "Quiz copiato negli appunti.")

    def export_png(self):
        if not PIL_AVAILABLE:
            messagebox.showerror("Pillow mancante", "Installa Pillow con: pip install pillow")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png")],
            initialfile=f"quiz_{self.secret}.png",
        )
        if not path:
            return

        img = Image.new("RGB", (1080, 1920), (12, 12, 15))
        draw = ImageDraw.Draw(img)

        def font(size, bold=False):
            candidates = [
                "arialbd.ttf" if bold else "arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
            for c in candidates:
                try:
                    return ImageFont.truetype(c, size)
                except Exception:
                    pass
            return ImageFont.load_default()

        f_small = font(34)
        f_title = font(58, True)
        f_sub = font(42, True)
        f_num = font(58, True)
        f_hint = font(31)
        f_bottom = font(48, True)

        y = 55
        prev = self.prev_solution_var.get().strip()
        if prev:
            draw.rounded_rectangle((60, y, 1020, y + 90), radius=28, fill=(28, 28, 34), outline=(255, 204, 64), width=3)
            draw.text((90, y + 24), f"🔓 SOLUZIONE PRECEDENTE: {prev}", font=f_small, fill=(255, 235, 120))
            y += 125

        draw.text((60, y), "IL 99% SBAGLIA", font=f_title, fill=(255, 210, 60))
        y += 70
        draw.text((60, y), f"TROVA IL CODICE A {self.length_var.get()} CIFRE", font=f_sub, fill=(255, 255, 255))
        y += 100

        colors = [(45, 106, 255), (30, 180, 95), (255, 160, 40), (150, 80, 255), (230, 60, 70)]
        for idx, clue in enumerate(self.clues):
            h = 205
            fill = colors[idx % len(colors)]
            draw.rounded_rectangle((60, y, 1020, y + h), radius=30, fill=(25, 25, 31), outline=fill, width=5)
            draw.text((95, y + 35), clue.guess, font=f_num, fill=(255, 255, 255))
            draw.text((320, y + 35), clue.text(), font=f_hint, fill=(240, 240, 240))
            y += h + 28

        y += 20
        draw.rounded_rectangle((60, y, 1020, y + 230), radius=34, fill=(180, 35, 45), outline=(255, 220, 80), width=5)
        draw.text((150, y + 30), "QUAL È IL CODICE?", font=f_bottom, fill=(255, 255, 255))
        boxes = "   ".join(["⬜"] * self.length_var.get())
        draw.text((285, y + 105), boxes, font=f_bottom, fill=(255, 255, 255))
        draw.text((170, y + 170), f"SCRIVI SOLO LE {self.length_var.get()} CIFRE", font=f_small, fill=(255, 255, 255))

        img.save(path)
        messagebox.showinfo("Esportato", f"Immagine salvata:\n{path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()
