from django.urls import path

from .views import StockInView, StockMovementListView

app_name = "inventory"

urlpatterns = [
    path("entree/", StockInView.as_view(), name="stock_in"),
    path("historique/", StockMovementListView.as_view(), name="movement_list"),
]
