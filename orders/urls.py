from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('peyments/', views.peyments, name='peyments'),
    path('order_complete/',views.order_complete,name='order_complete'),
    ]
