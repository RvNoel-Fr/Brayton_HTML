#!/usr/bin/env python3
"""Validation minimale des fichiers HTML du depot : parse, equilibre des balises, liens locaux."""
import sys
from html.parser import HTMLParser
from pathlib import Path

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}
EXTERNAL = ("http://", "https://", "mailto:", "#", "data:")


class Checker(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)
        for name, value in attrs:
            if name in ("href", "src") and value and not value.startswith(EXTERNAL):
                target = value.split("#")[0]
                if target and not (self.path.parent / target).exists():
                    self.errors.append(f"{self.path.name}: lien local introuvable: {value}")

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"{self.path.name}: balise fermante orpheline </{tag}>")
        elif self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append(
                f"{self.path.name}: </{tag}> inattendu, balise ouverte: <{self.stack[-1]}>")


def main():
    root = Path(__file__).resolve().parents[2]
    files = sorted(p for p in root.rglob("*.html") if ".git" not in p.parts)
    if not files:
        print("ERREUR aucun fichier HTML trouve")
        return 1
    ok = True
    for f in files:
        text = f.read_text(encoding="utf-8")
        checker = Checker(f)
        try:
            checker.feed(text)
            checker.close()
        except Exception as exc:
            print(f"ERREUR {f.name}: exception du parseur: {exc}")
            ok = False
            continue
        if not text.lstrip().lower().startswith("<!doctype html"):
            checker.errors.append(f"{f.name}: doctype <!DOCTYPE html> manquant")
        if checker.stack:
            checker.errors.append(
                f"{f.name}: balises non fermees: {', '.join(checker.stack)}")
        if checker.errors:
            ok = False
            for err in checker.errors:
                print(f"ERREUR {err}")
        else:
            print(f"OK {f.relative_to(root)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
