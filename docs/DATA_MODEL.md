# Modèle de données — lot 1

```mermaid
erDiagram
    USER ||--o{ STOCK_MOVEMENT : "enregistre"
    USER ||--o{ AUDIT_LOG : "auteur (nullable)"
    CATEGORY ||--o{ PRODUCT : "contient"
    PRODUCT ||--o{ STOCK_MOVEMENT : "historique"
    STOCK_MOVEMENT |o--o| STOCK_MOVEMENT : "reverses (annulation)"

    USER { bigint id PK  string username UK  string role  string preferred_language  string phone }
    CATEGORY { bigint id PK  string name_fr UK  string name_ar  text description  string status  datetime created_at  datetime updated_at }
    PRODUCT { bigint id PK  string sku UK  string barcode "unique si non vide"  string name_fr  string name_ar  bigint category_id FK  string phone_brand  string phone_model  decimal purchase_price  decimal sale_price  int quantity  int low_stock_threshold  string location  string status }
    STOCK_MOVEMENT { bigint id PK  bigint product_id FK  string movement_type  int quantity "gt 0"  int quantity_before  int quantity_after  datetime created_at  bigint created_by_id FK  string reason  string reference  bigint reverses_id FK "unique, nullable" }
    AUDIT_LOG { bigint id PK  bigint user_id FK  string action  string object_type  string object_id  json details  datetime created_at }
```

## Règles
- `Product.quantity` n'est modifié que par `inventory.services.record_movement` (transaction + verrou de ligne `select_for_update`).
- `StockMovement` et `AuditLog` sont en ajout seul. Une correction crée un mouvement inverse relié par `reverses`.
- Suppressions : `PROTECT` sur catégorie, produit et utilisateur de mouvement. On archive (`status=archived`), on ne supprime pas.
- Contraintes SQL : prix >= 0, quantité de mouvement > 0, code-barres unique s'il est renseigné, SKU unique (normalisé en majuscules).
- Rôles : un groupe Django par rôle (`owner`, `stock_manager`, `cashier`), défini dans `accounts/roles.py`.
- Permissions personnalisées : `catalog.view_purchase_price`, `inventory.adjust_stock`.

## Hypothèses à confirmer
Seuil d'alerte par défaut = 5 ; fuseau Africa/Casablanca ; le gestionnaire de stock voit le prix d'achat (pas les marges) ; mouvements limités à entrée, sortie, ajustement ± (vente et retour viendront avec les ventes).
