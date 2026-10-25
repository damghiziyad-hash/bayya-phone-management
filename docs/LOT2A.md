# Lot 2a — Interface : connexion, layout, langues, tableau de bord

## Fichiers créés (aucun fichier existant n'est écrasé)
`web/` (apps.py, services.py, views.py, urls.py) · `templates/` (base_root, base, 403, registration/login, partials/*, web/dashboard) ·
`static/css/app.css` · `static/vendor/bootstrap/LISEZMOI.txt` · `locale/ar/LC_MESSAGES/django.po` · `tests/web/*` ·
`scripts/apply_lot2a_settings.py` · ce fichier.

## Fichiers modifiés (par le script, avec sauvegarde `.lot2a.bak`)
- `config/settings.py` : `web` dans INSTALLED_APPS ; LOGIN_URL / LOGIN_REDIRECT_URL / LOGOUT_REDIRECT_URL ; STATICFILES_DIRS ; STORE_CURRENCY (défaut MAD, hypothèse).
- `config/urls.py` : la racine `/` passe par `web.urls` (redirection vers le tableau de bord).
- `.gitignore` : `*.mo`.
Aucun modèle modifié, aucune migration créée.

## Bootstrap 5.3.3 en local
```bash
cd static/vendor/bootstrap
B=https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist
curl -fL -o bootstrap.min.css        $B/css/bootstrap.min.css
curl -fL -o bootstrap.rtl.min.css    $B/css/bootstrap.rtl.min.css
curl -fL -o bootstrap.bundle.min.js  $B/js/bootstrap.bundle.min.js
head -c 120 bootstrap.min.css        # doit contenir "Bootstrap  v5.3.3"
cd ../../..
```

## Limites connues
- Pas de limitation des tentatives de connexion (lot sécurité avant la production).
- Traductions arabes à faire relire. Menu : seul le tableau de bord existe (Produits, Stock, Alertes : lots 2b/2c).
- Devise MAD provisoire, non encore configurable depuis l'interface.
