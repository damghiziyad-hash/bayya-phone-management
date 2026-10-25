from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("produits/", views.ProductListView.as_view(), name="product_list"),
    path("produits/ajouter/", views.ProductCreateView.as_view(), name="product_create"),
    path("produits/<int:pk>/modifier/", views.ProductUpdateView.as_view(), name="product_update"),
]
