from django.urls import path
from . import views

urlpatterns = [
    # ...other url patterns...
    path('initiate-cashfree-payment/', views.initiate_cashfree_payment, name='initiate_cashfree_payment'),
    path('cashfree-callback/', views.cashfree_callback, name='cashfree_callback'),
]
