"""homeoayurcart URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, reverse
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.contrib.sitemaps import Sitemap

from ecommerce.views import (
    CustomLoginView, phone_login, phone_callback, apply_coupon, index,
    product_details, update_cart, change_currency, toggle_wishlist,
    wishlist_view, cart, order_confirmation, past_orders, order_tracking,
    user_profile, search, get_address_details, checkout
)
from blog.views import post, blog

# Define sitemap for static views
class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'weekly'

    def items(self):
        # List of named URLs for static pages or important views
        return ['home', 'blog', 'checkout', 'cart', 'user_profile']

    def location(self, item):
        return reverse(item)

# Optional: Add a sitemap for blog posts (dynamic content)
class BlogSitemap(Sitemap):
    priority = 0.8
    changefreq = 'daily'

    def items(self):
        from blog.models import Post  # import your blog post model here
        return Post.objects.filter(published=True)

    def lastmod(self, obj):
        return obj.updated_at  # assuming you have updated_at datetime field

sitemaps = {
    'static': StaticViewSitemap,
    # Uncomment if you want to include blog posts in sitemap
    # 'blog': BlogSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='home'),
    path('blog/', blog, name='blog'),
    path('post/<slug>/', post, name='post'),
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
    path('profile/', user_profile, name='user_profile'),
    path('search/', search, name='search'),
    path('get-address-details/', get_address_details, name='get_address_details'),
    path('apply_coupon/', apply_coupon, name='apply_coupon'),
    path('phone-login/', phone_login, name='phone_login'),
    path('phone-callback/', phone_callback, name='phone_callback'),

    # Sitemap URL
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Admin site customization
admin.site.site_header = "Microwhite Admin"
admin.site.site_title = "Microwhite Admin Portal"
admin.site.index_title = "Welcome to Microwhite Admin Portal"
