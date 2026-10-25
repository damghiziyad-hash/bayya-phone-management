"""Applique les petites modifications du Lot 2a à config/settings.py et config/urls.py.

- Idempotent : relancé, il constate que tout est déjà fait.
- Tout ou rien : si une ancre est introuvable, AUCUN fichier n'est modifié.
- Sauvegarde avant écriture : fichier.lot2a.bak
- Ne touche jamais à .env.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SETTINGS_EDITS = [
    ("web dans INSTALLED_APPS", '    "inventory",\n]', '    "inventory",\n    "web",\n]', '    "web",'),
    ("URLs de connexion", 'LOGIN_URL = "admin:login"',
     'LOGIN_URL = "web:login"\nLOGIN_REDIRECT_URL = "web:dashboard"\nLOGOUT_REDIRECT_URL = "web:login"',
     "LOGIN_REDIRECT_URL"),
    ("fichiers statiques et devise", 'STATIC_ROOT = BASE_DIR / "staticfiles"',
     'STATIC_ROOT = BASE_DIR / "staticfiles"\nSTATICFILES_DIRS = [BASE_DIR / "static"]\n'
     'STORE_CURRENCY = os.environ.get("STORE_CURRENCY", "MAD")  # hypothèse : MAD, à confirmer',
     "STATICFILES_DIRS"),
]
URLS_EDITS = [
    ("racine vers l'application web",
     '    path("", RedirectView.as_view(pattern_name="admin:index", permanent=False)),',
     '    path("", include("web.urls")),', 'web.urls'),
]


def plan(path, edits):
    text = path.read_text(encoding="utf-8")
    for name, old, new, marker in edits:
        if marker in text:
            print(f"= {path.name} : « {name} » déjà appliqué")
            continue
        if text.count(old) != 1:
            sys.exit(f"ERREUR : ancre introuvable ou ambiguë pour « {name} » dans {path}.\n"
                     f"Rien n'a été modifié. Faites cette modification à la main :\n--- remplacer\n{old}\n--- par\n{new}")
        text = text.replace(old, new)
        print(f"+ {path.name} : « {name} » à appliquer")
    return text


def main():
    targets = {ROOT / "config" / "settings.py": SETTINGS_EDITS, ROOT / "config" / "urls.py": URLS_EDITS}
    results = {p: plan(p, e) for p, e in targets.items()}  # toutes les vérifications avant toute écriture
    for path, new_text in results.items():
        if new_text != path.read_text(encoding="utf-8"):
            path.with_name(path.name + ".lot2a.bak").write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            path.write_text(new_text, encoding="utf-8")
    gitignore = ROOT / ".gitignore"
    if gitignore.exists() and "*.mo" not in gitignore.read_text(encoding="utf-8").splitlines():
        with gitignore.open("a", encoding="utf-8") as f:
            f.write("\n# Traductions compilées (régénérées par compilemessages)\n*.mo\n")
        print("+ .gitignore : *.mo ajouté")
    print("Terminé.")


if __name__ == "__main__":
    main()
