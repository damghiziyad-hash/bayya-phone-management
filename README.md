# Bayya Phone — Stock & CRM System

Application de gestion interne (Django, PostgreSQL, Bootstrap 5). **Lot 1 : fondations** — utilisateurs/rôles, catégories, produits, mouvements de stock, journal d'audit. Ventes, factures PDF, CRM, tableau de bord et interface bilingue complète arrivent dans les lots suivants.

## Installation sur Ubuntu (projet existant)

```bash
cd ~/Desktop/bayya-phone-management && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # puis éditer .env (jamais commité)
```

### PostgreSQL (une seule fois)
```bash
sudo -u postgres psql
```
```sql
CREATE USER bayya_user WITH PASSWORD 'votre-mot-de-passe' CREATEDB;
CREATE DATABASE bayya_phone OWNER bayya_user;
\q
```
`CREATEDB` permet à pytest de créer sa base temporaire `test_bayya_phone`. Vos autres bases ne sont pas touchées.

### Modèle utilisateur personnalisé — ATTENTION
`AUTH_USER_MODEL = "accounts.User"` doit être en place **avant** la première migration. Si vous avez déjà exécuté `migrate` avec l'utilisateur Django par défaut sur la base `bayya_phone`, il faut repartir d'une base de **développement vide** (ceci supprime son contenu) :
```bash
sudo -u postgres psql -c "DROP DATABASE bayya_phone;"
sudo -u postgres psql -c "CREATE DATABASE bayya_phone OWNER bayya_user;"
```
N'exécutez ceci que si cette base ne contient aucune donnée à garder.

### Migrations, rôles, administrateur
```bash
python manage.py makemigrations accounts core catalog inventory
python manage.py migrate
python manage.py setup_roles          # crée les groupes et permissions (relancer après chaque ajout de permission)
python manage.py createsuperuser      # reçoit automatiquement le rôle propriétaire
python manage.py runserver            # http://127.0.0.1:8000/admin/
```
Committez les fichiers `*/migrations/0001_initial.py` générés.

### Tests
```bash
pytest -v
```
Le test de concurrence (dernière pièce) ne tourne que sur PostgreSQL ; il est ignoré avec SQLite.

## Rôles
| Rôle | Accès (lot 1) |
|---|---|
| Propriétaire | toutes les permissions, administration, journal d'audit |
| Gestionnaire de stock | produits, catégories, mouvements, ajustements, prix d'achat |
| Vendeur/caissier | consultation des produits et catégories |

## Production (à adapter)
`DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS` et `DJANGO_CSRF_TRUSTED_ORIGINS` réels, HTTPS, clé secrète unique, sauvegardes `pg_dump` testées. Détails dans un lot ultérieur.
