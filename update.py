import docx
import os
from collections import defaultdict
from datetime import datetime
import random

DOCX_FILE = "CCR_SG&AD.docx"
README_FILE = "README.md"
PROCESSED_FILE = "processed_dates.txt"

KEYWORDS = ["Astuces", "Windev", "Correctifs", "Bugs", "Test", "Evolution"]

def load_notes():
    doc = docx.Document(DOCX_FILE)
    notes = {}
    current_date = None
    buffer = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        try:
            date = datetime.strptime(text, "%d/%m/%Y").date()
            if current_date and buffer:
                notes[current_date] = buffer
                buffer = []
            current_date = date
        except ValueError:
            if current_date:
                buffer.append(text)

    if current_date and buffer:
        notes[current_date] = buffer

    return dict(sorted(notes.items(), key=lambda x: x[0]))


def load_processed_dates():
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())


def save_processed_dates(processed):
    with open(PROCESSED_FILE, "w") as f:
        for d in sorted(processed):
            f.write(d + "\n")


def group_notes(notes):
    grouped = defaultdict(lambda: defaultdict(list))
    for date, items in notes.items():
        month_label = date.strftime("%B %Y")
        for note in items:
            found = False
            for kw in KEYWORDS:
                if note.lower().startswith(kw.lower()):
                    grouped[month_label][kw].append(f"{date.strftime('%d/%m/%Y')} - {note}")
                    found = True
                    break
            if not found:
                words = note.split()
                if words and words[0].startswith("#"):
                    tag = words[0][1:]
                    grouped[month_label][tag].append(f"{date.strftime('%d/%m/%Y')} - {note}")
                else:
                    grouped[month_label]["Divers"].append(f"{date.strftime('%d/%m/%Y')} - {note}")
    return grouped


def update_readme(grouped):
    lines = ["# Journal des notes\n"]
    for month, categories in grouped.items():
        lines.append(f"\n## Mois de {month}\n")
        for cat, items in categories.items():
            lines.append(f"### {cat}")
            for note in items:
                lines.append(f"- {note}")
            lines.append("")
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    if random.random() < 0.33:  # ~1 jour sur 3
        print("⏭️ Aujourd'hui on ne met pas à jour.")
        return

    all_notes = load_notes()
    processed = load_processed_dates()

    remaining = [d for d in all_notes if d.strftime("%d/%m/%Y") not in processed]
    if not remaining:
        print("✅ Toutes les notes ont déjà été traitées.")
        return

    to_process = remaining[:3]  # prendre 3 dates chronologiques
    new_entries = {d: all_notes[d] for d in to_process}

    grouped_existing = group_notes({
        datetime.strptime(date, "%d/%m/%Y").date(): all_notes[datetime.strptime(date, "%d/%m/%Y").date()]
        for date in processed
        if datetime.strptime(date, "%d/%m/%Y").date() in all_notes
    })

    grouped_new = group_notes(new_entries)

    for month, cats in grouped_new.items():
        for cat, items in cats.items():
            grouped_existing[month][cat].extend(items)

    update_readme(grouped_existing)

    for d in to_process:
        processed.add(d.strftime("%d/%m/%Y"))
    save_processed_dates(processed)

    print(f"✨ Ajouté {len(to_process)} nouvelles dates dans le README.md")


if __name__ == "__main__":
    main()
