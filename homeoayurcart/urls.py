from django.contrib import admin
from django.urls import path, include, reverse
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.contrib.sitemaps import Sitemap

from ecommerce.views import (
    CustomLoginView, phone_login, phone_callback, apply_coupon, index,
    product_details, update_cart, change_currency, toggle_wishlist,
    wishlist_view, cart, order_confirmation, past_orders, order_tracking, invoice,
    user_profile, search, get_address_details, checkout, add_address,
    initiate_cashfree_payment, cashfree_callback,
    privacy_policy, terms_and_conditions, shipping_and_delivery_policy, refund_and_cancellation_policy
)

from blog.views import post, blog, about, contact # 👈 contact import add karo
from ecommerce.views import shop  # 👈 contact import add karo



# Define sitemap for static views
class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'weekly'

    def items(self):
        return ['home', 'blog', 'checkout', 'cart', 'user_profile', 'about', 'contact']

    def location(self, item):
        return reverse(item)


sitemaps = {
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='home'),
    path('blog/', blog, name='blog'),
    path('post/<slug>/', post, name='post'),

    # 👇 Static Pages
    path("about/", about, name="about"),
    path("contact/", contact, name="contact"),
    path("privacy-policy/", privacy_policy, name="privacy_policy"),
    path("terms-and-conditions/", terms_and_conditions, name="terms_and_conditions"),
    path("shipping-and-delivery-policy/", shipping_and_delivery_policy, name="shipping_and_delivery_policy"),
    path("refund-and-cancellation-policy/", refund_and_cancellation_policy, name="refund_and_cancellation_policy"),


    # Ecommerce
    path('checkout/', checkout, name='checkout'),
    path('product_details/<int:product_id>/', product_details, name='product_details'),
    path('cart/', cart, name='cart'),
    path('update-cart/', update_cart, name='update_cart'),
    path('change-currency/', change_currency, name='change_currency'),
    path('toggle-wishlist/', toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/', wishlist_view, name='wishlist'),
    path('accounts/', include('allauth.urls')),
    path('accounts/login/', CustomLoginView.as_view(), name='account_login'),
    path('order-confirmation/<int:order_id>/', order_confirmation, name='order_confirmation'),
    path('past-orders/', past_orders, name='past_orders'),
    path('order-tracking/<int:order_id>/', order_tracking, name='order_tracking'),
    path('invoice/<int:order_id>/', invoice, name='invoice'),
    path('profile/', user_profile, name='user_profile'),
    path('search/', search, name='search'),
    path('get-address-details/', get_address_details, name='get_address_details'),
    path('add-address/', add_address, name='add_address'),
    path('apply_coupon/', apply_coupon, name='apply_coupon'),
    path('phone-login/', phone_login, name='phone_login'),
    path('phone-callback/', phone_callback, name='phone_callback'),
    path('initiate-cashfree-payment/', initiate_cashfree_payment, name='initiate_cashfree_payment'),
    path('cashfree-callback/', cashfree_callback, name='cashfree_callback'),
    path('shop/', shop, name='shop'),

    # Sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Admin site customization
admin.site.site_header = "Microwhite Admin"
admin.site.site_title = "Microwhite Admin Portal"
admin.site.index_title = "Welcome to Microwhite Admin Portal"
