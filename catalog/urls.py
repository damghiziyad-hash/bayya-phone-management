
from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    # Boutique publique pour les clients
    path(
        "boutique/",
        views.ClientProductListView.as_view(),
        name="client_catalog",
    ),
    path(
        "boutique/produit/<int:pk>/",
        views.ClientProductDetailView.as_view(),
        name="client_product_detail",
    ),

    # Gestion des produits pour l'administration
    path("produits/", views.ProductListView.as_view(), name="product_list"),
    path("produits/ajouter/", views.ProductCreateView.as_view(), name="product_create"),
    path("produits/<int:pk>/modifier/", views.ProductUpdateView.as_view(), name="product_update"),
    path("produits/<int:pk>/supprimer/", views.ProductDeleteView.as_view(), name="product_delete"),
    path(
    "produits/<int:pk>/archiver/",
    views.ProductArchiveView.as_view(),
    name="product_archive",
),
]
