from django.urls import path
from . import views

urlpatterns = [
    path('menu-items', views.menu_items),
    path('menu-items/<int:pk>', views.single_menu_item),
    
    path('groups/manager/users', views.managers),
    path('groups/manager/users/<int:pk>', views.manager),
    
    path('groups/delivery-crew/users', views.delivery_crew),
    path('groups/delivery-crew/users/<int:pk>', views.crew_member),
    
    path('cart/menu-items', views.cart),
    
    path('orders', views.orders),
    path('orders/<int:pk>', views.order),
]