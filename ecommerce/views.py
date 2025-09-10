import json
import requests
from django.contrib.auth import login
from django.shortcuts import redirect, render,get_object_or_404
from .models import Cart, Product, CartProduct,Currency,Wishlist, Order,OrderProduct,UserProfile, Address,Coupon, Category
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import OrderForm,AddressForm,UserProfileForm, UserForm
from django.db.models import Q
from blog.models import Blog_Post
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.views.decorators.csrf import csrf_exempt

CASHFREE_API_KEY = 'TEST_API_KEY'
CASHFREE_API_SECRET = 'TEST_API_SECRET'
CASHFREE_API_URL = 'https://sandbox.cashfree.com/pg/orders'

def get_cart_context(request):
    cart = get_cart(request)
    cart_products = cart.cartproduct_set.all()
    cart_items = cart.count_unique_items()
    total = cart.get_total_price()
    return {
        'cart': cart,
        'cart_products': cart_products,
        'cart_items': cart_items,
        'total': total,
    }

# Create your views here.
@require_POST
def apply_coupon(request):
    coupon_code = request.POST.get('coupon_code', '').strip()
    cart = get_cart(request)  # Initialize cart here

    total = cart.get_total_price()

    print(f"Coupon code: {coupon_code}, Total before applying coupon: {total}")  # Debugging

    try:
        coupon = Coupon.objects.get(code=coupon_code)
        if coupon.is_valid():
            print("Coupon is valid")  # Debugging
            new_total = coupon.apply_coupon(total)  # Use apply_coupon method
            
            # Convert the total to float before returning as JSON
            new_total_float = float(new_total)
            request.session['total'] = new_total_float  # Update total in session

            print(f"Total after applying coupon: {new_total_float}")  # Debugging

            return JsonResponse({'success': True, 'new_total': new_total_float})
        else:
            print("Coupon is invalid")  # Debugging
            return JsonResponse({'success': False})
    except Coupon.DoesNotExist:
        print("Coupon does not exist")  # Debugging
        return JsonResponse({'success': False})
    except Exception as e:
        print(f"Error applying coupon: {str(e)}")  # Debugging
        return JsonResponse({'error': 'Internal Server Error'}, status=500)

    
def change_currency(request):
    if request.method == 'POST' and request.is_ajax():
        currency_code = request.POST.get('currency')

        # Fetch the Currency object based on the currency code
        currency = get_object_or_404(Currency, code=currency_code)

        # Update session with selected currency and conversion rate
        request.session['currency'] = currency.code
        request.session['currency_name'] = currency.name
        request.session['currency_conversion_rate'] = str(currency.conversion_rate)
        request.session['currency_symbol'] = str(currency.symbol)

        # Return JSON response indicating success
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request'})
    
def get_cart(request):
    # Ensure the session key is created if not present
    if not request.session.session_key:
        request.session.save()  # Force save session to create a session key

    if request.user.is_authenticated:
        # For authenticated users
        cart, created = Cart.objects.get_or_create(user=request.user)
        print(f"Authenticated user cart: {cart}, Created: {created}")
    else:
        # For non-authenticated users
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_id=session_key)
        print(f"Session-based cart: {cart}, Created: {created}, Session Key: {session_key}")

    print(f"Cart items: {cart.cartproduct_set.all()}")
    return cart

def update_cart(request):
    if request.method == 'POST':
        try:
            product_id = request.POST.get('product_id')
            action = request.POST.get('action')
            quantity = int(request.POST.get('quantity', 1))

            print(f'Received data - Product ID: {product_id}, Action: {action}, Quantity: {quantity}')  # Debugging

            if not product_id or not action:
                print('Missing product_id or action')  # Debugging
                return JsonResponse({'error': 'Missing product_id or action'}, status=400)

            product = get_object_or_404(Product, id=product_id)
            cart = get_cart(request)

            if action == 'add':
                cart_product, created = CartProduct.objects.get_or_create(cart=cart, product=product)
                if not created:
                    cart_product.quantity += quantity
                else:
                    cart_product.quantity = quantity
                cart_product.save()
            elif action == 'remove':
                cart_product = CartProduct.objects.filter(cart=cart, product=product).first()
                if cart_product:
                    if cart_product.quantity > 1:
                        cart_product.quantity -= 1
                        cart_product.save()
                    else:
                        cart_product.delete()
            elif action == 'update':
                if quantity <= 0:
                    return JsonResponse({'error': 'Quantity must be greater than 0'}, status=400)
                cart_product, created = CartProduct.objects.get_or_create(cart=cart, product=product)
                cart_product.quantity = quantity
                cart_product.save()
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)

            cart_products = CartProduct.objects.filter(cart=cart)
            subtotal = sum(cp.quantity * float(cp.product.price) for cp in cart_products)
            print(f"Calculated subtotal: {subtotal}")  # Debugging

            cart_data = {
                'total_items': cart_products.count(),
                'cart_subtotal': float(subtotal),  # Ensure this is sent as a float
                'products': [{
                    'id': cp.product.id,
                    'name': cp.product.name,
                    'price': float(cp.product.price),  # Ensure this is a float
                    'image_url': cp.product.image.url,
                    'quantity': cp.quantity  # Include the quantity
                } for cp in cart_products]
            }

            print(f"Cart data to be returned: {cart_data}")  # Debugging
            return JsonResponse(cart_data)

        except Exception as e:
            print(f"Error occurred: {e}")  # Debugging
            return JsonResponse({'error': f'An error occurred: {e}'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


def index(request):
    # Fetch products and initialize cart
    products = Product.objects.all()
    bloglist = Blog_Post.objects.all().order_by('-Timestamp')

    selected_currency = request.session.get('currency', 'USD')
    all_currencies = Currency.objects.all()

    # Adjust product prices based on selected currency
    for product in products:
        product.price = product.get_price(selected_currency)
    
    cart_context = get_cart_context(request)
    cart_products = cart_context['cart_products']

    for cart_product in cart_products:
        cart_product.product.price = cart_product.product.get_price(selected_currency)

    # Calculate currency_total
    currency_total = sum(cart_product.product.price * cart_product.quantity for cart_product in cart_products)
    currency_total = round(currency_total, 2)

    context = {
        'currency_total':currency_total,
        'products': products,
        'selected_currency': selected_currency,
        'currencies': all_currencies,
        'bloglist':bloglist,
    }
    context.update(cart_context)
    return render(request, 'index-2.html', context)


def product_details(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    currencies = Currency.objects.all()  # Get all available currencies
    selected_currency = request.session.get('currency', 'USD')  # Default to USD if not set in session

    product_price = product.get_price(selected_currency)

    # Top rated products (using price as a proxy for rating)
    top_rated_products = Product.objects.order_by('-price')[:3]

    # Related products (random products, excluding the current one)
    related_products = Product.objects.exclude(id=product_id).order_by('?')[:3]

    product_data = {
        'id': product.id,
        'name': product.name,
        'price': product_price,
        'description': product.description,
        'image_url': product.image.url,
        # 'categories': [category.name for category in product.categories.all()],  # Example: Assuming you have categories
    }
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(product_data)
    else:
        cart_context = get_cart_context(request)
        context = {
            'product': product,
            'product_data': product_data,
            'currencies': currencies,
            'selected_currency': selected_currency,
            'product_price': product_price,
            'top_rated_products': top_rated_products,
            'related_products': related_products,
        }
        context.update(cart_context)
        return render(request, 'product-details.html', context)
    

@require_POST
def toggle_wishlist(request):
    print("Request body:", request.body)  # Debugging

    try:
        data = json.loads(request.body)
        print("Parsed JSON data:", data)  # Debug: check parsed data
        
        product_id = data.get('product_id')
        print("Product ID:", product_id)  # Debug: check product ID

        product = get_object_or_404(Product, id=product_id)
        print("Product found:", product)  # Debug: check if product is found

        if request.user.is_authenticated:
            # For authenticated users
            wishlist, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        else:
            # For non-authenticated users
            session_key = request.session.session_key
            if not session_key:
                request.session.save()  # Force save session to create a session key
                session_key = request.session.session_key
            
            wishlist, created = Wishlist.objects.get_or_create(session_id=session_key, product=product)
        
        print("Wishlist entry:", wishlist)  # Debug: check the wishlist entry
        print("Created:", created)  # Debug: check if the entry was newly created

        if not created:
            wishlist.delete()
            added = False
        else:
            added = True

        return JsonResponse({'added': added})
    except json.JSONDecodeError:
        print("JSON Decode Error")  # Debug: handle JSON decode error
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print("Exception:", str(e))  # Debug: catch any other exceptions
        return JsonResponse({'error': 'An error occurred'}, status=500)
    
# @login_required
def wishlist_view(request):
    if request.user.is_authenticated:
        # For authenticated users, filter wishlist by user
        wishlist_items = Wishlist.objects.filter(user=request.user)
    else:
        # For non-authenticated users, filter wishlist by session key
        session_key = request.session.session_key
        if not session_key:
            request.session.save()  # Ensure the session key is created
            session_key = request.session.session_key
        
        wishlist_items = Wishlist.objects.filter(session_id=session_key)
    
    cart_context = get_cart_context(request)
    context = {
        'wishlist_items': wishlist_items
    }
    context.update(cart_context)
    return render(request, 'wishlist.html', context)

   
@login_required
def checkout(request):
    user = request.user
    
    # Initialize forms with None
    order_form = OrderForm()
    address_form = AddressForm(user=user)
    shipping_address = None

    print("Existing addresses queryset:")
    for address in address_form.fields['existing_address'].queryset:
        print(address.id, address)
        
    if request.method == 'POST':
        order_form = OrderForm(request.POST)
        address_form = AddressForm(user, request.POST)

        if 'existing_address' in request.POST:
            address_id = request.POST['existing_address']
            if address_id:
                shipping_address = get_object_or_404(Address, id=address_id, user=user)
                address_form = AddressForm(instance=shipping_address, user=user, data=request.POST)
        else:
            shipping_address = None
        
        if address_form.is_valid() and order_form.is_valid():
            if not shipping_address:
                shipping_address = address_form.save(commit=False)
                shipping_address.user = user
                shipping_address.save()

            order = order_form.save(commit=False)
            order.user = user
            order.shipping_address = shipping_address
            order.total_price = get_cart(request).get_total_price() # Get total from cart
            order.payment_status = 'unpaid' # Set to unpaid initially
            order.status = 'pending'
            order.save()

            for cart_product in get_cart(request).cartproduct_set.all():
                OrderProduct.objects.create(
                    order=order,
                    product=cart_product.product,
                    quantity=cart_product.quantity
                )

            # Do not clear cart here, it will be cleared after successful payment

            return redirect('order_confirmation', order_id=order.id)
    else:
        order_form = OrderForm()
        address_form = AddressForm(user=user)

    cart_context = get_cart_context(request)
    context = {
        'order_form': order_form,
        'address_form': address_form,
    }
    context.update(cart_context)
    return render(request, 'checkout.html', context)


@login_required
def user_profile(request):
    orders = Order.objects.filter(user=request.user)

    if request.user.is_superuser:
        return redirect('admin:index')

    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    addresses = Address.objects.filter(user=request.user)
    address_form = AddressForm(user=request.user)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=user_profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if current_password and new_password and confirm_password:
                if request.user.check_password(current_password):
                    if new_password == confirm_password:
                        request.user.set_password(new_password)
                        request.user.save()
                        login(request, request.user)  # Re-login the user to update the session
                        return redirect('user_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
    
    cart_context = get_cart_context(request)
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'addresses': addresses,
        'orders': orders,
        'address_form': address_form
    }
    context.update(cart_context)
    return render(request, 'user_profile.html', context)

@login_required
def add_address(request):
    if request.method == 'POST':
        form = AddressForm(request.user, request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            return redirect('user_profile')
    return redirect('user_profile')

@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.user, request.POST, instance=address)
        if form.is_valid():
            form.save()
            return redirect('user_profile')
    else:
        form = AddressForm(request.user, instance=address)
    cart_context = get_cart_context(request)
    context = {
        'form': form
    }
    context.update(cart_context)
    return render(request, 'edit_address.html', context)

@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
    return redirect('user_profile')

@login_required
def set_default_address(request, address_id):
    Address.objects.filter(user=request.user, default=True).update(default=False)
    Address.objects.filter(id=address_id, user=request.user).update(default=True)
    return redirect('user_profile')


def cart(request):
    products = Product.objects.all()

    cart_context = get_cart_context(request)
    context = {
        'products':products,
    }
    context.update(cart_context)
    return render(request, 'cart.html', context)

@login_required
def get_address_details(request):
    address_id = request.GET.get('address_id')
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    address_data = {
        'first_name': address.first_name,
        'last_name': address.last_name,
        'email': address.email,
        'address_line_1': address.address_line_1,
        'country': address.country.code,  # Ensure this is the country code
        'state': address.state,
        'city': address.city,
        'zipcode': address.zipcode,
        'phone': address.phone,
    }

    return JsonResponse(address_data)


def search(request):
  products = Product.objects.all()  # Fetch all products from the database
  searchlist = Product.objects.all().order_by('-price')
  query = request.GET.get('q')

  if query:
    searchlist = searchlist.filter(
      Q(name__icontains = query) |
      Q(description__icontains = query)   
    ).distinct()

  cart_context = get_cart_context(request)
  context = {   
    'searchlist' : searchlist,
    'query':query,
    'products': products,
  }
  context.update(cart_context)
  return render(request,'search_result.html',context)


def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_products = OrderProduct.objects.filter(order=order)
    cart_context = get_cart_context(request)
    context = {
        'order': order,
        'order_products': order_products
    }
    context.update(cart_context)
    return render(request, 'invoice/general-invoice.html', context)

@login_required
def past_orders(request):
    orders = Order.objects.filter(user=request.user)
    cart_context = get_cart_context(request)
    context = {
        'orders': orders
    }
    context.update(cart_context)
    return render(request, 'past_orders.html', context)

@login_required
def order_tracking(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    cart_context = get_cart_context(request)
    context = {
        'order': order
    }
    context.update(cart_context)
    return render(request, 'order_tracking.html', context)

@login_required
def invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_products = OrderProduct.objects.filter(order=order)
    cart_context = get_cart_context(request)
    context = {
        'order': order,
        'order_products': order_products
    }
    context.update(cart_context)
    return render(request, 'invoice/general_invoice.html', context)

@login_required
def initiate_cashfree_payment(request):
    if request.method == 'POST':
        # Create an order in your database
        user = request.user
        cart = Cart.objects.get(user=user)
        total = cart.get_total_price()

        order_form = OrderForm(request.POST)
        address_form = AddressForm(user, request.POST)

        if address_form.is_valid() and order_form.is_valid():
            shipping_address = address_form.save(commit=False)
            shipping_address.user = user
            shipping_address.save()

            order = order_form.save(commit=False)
            order.user = user
            order.shipping_address = shipping_address
            order.total_price = total
            order.payment_status = 'unpaid'
            order.status = 'pending'
            order.save()

            for cart_product in cart.cartproduct_set.all():
                OrderProduct.objects.create(
                    order=order,
                    product=cart_product.product,
                    quantity=cart_product.quantity
                )

            # Create an order with Cashfree
            headers = {
                "Content-Type": "application/json",
                "x-api-version": "2022-01-01",
                "x-client-id": CASHFREE_API_KEY,
                "x-client-secret": CASHFREE_API_SECRET
            }

            payload = {
                "order_id": str(order.id),
                "order_amount": str(order.total_price),
                "order_currency": "INR",
                "customer_details": {
                    "customer_id": str(user.id),
                    "customer_name": user.get_full_name(),
                    "customer_email": user.email,
                    "customer_phone": user.userprofile.phone_number
                },
                "order_meta": {
                    "return_url": request.build_absolute_uri(f'/cashfree-callback/?order_id={order.id}')
                }
            }

            response = requests.post(CASHFREE_API_URL, headers=headers, json=payload)
            cashfree_order = response.json()

            return JsonResponse({'payment_session_id': cashfree_order['payment_session_id']})

    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def cashfree_callback(request):
    if request.method == 'POST':
        order_id = request.GET.get('order_id')
        order = get_object_or_404(Order, id=order_id)

        # Verify the payment with Cashfree
        # This step is important to prevent fraud
        # You should implement the verification logic here based on Cashfree's documentation

        order.payment_status = 'paid'
        order.save()

        # Clear the cart
        cart = Cart.objects.get(user=order.user)
        cart.products.clear()

        return redirect('order_confirmation', order_id=order.id)

    return JsonResponse({'error': 'Invalid request'}, status=400)


from django.contrib.auth import login
import requests


import logging


def phone_login(request):
    CLIENT_ID = "13173857965042182049"  # Replace with your actual CLIENT_ID
    REDIRECT_URL = request.build_absolute_uri('/phone-callback/')  # Adjust path as needed
    AUTH_URL = f"https://www.phone.email/auth/log-in?client_id={CLIENT_ID}&redirect_url={REDIRECT_URL}"

    cart_context = get_cart_context(request)
    context = {
        'auth_url': AUTH_URL
    }
    context.update(cart_context)
    response =  render(request, 'phone_login.html', context)
    response['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'
    return response
from django.contrib.auth.models import User
from .models import UserProfile  # Import your UserProfile model
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)
@csrf_exempt
def phone_callback(request):
    user_json_url = request.GET.get('user_json_url', None)
    if not user_json_url:
        return JsonResponse({'error': 'User JSON URL is missing'}, status=400)

    try:
        response = requests.get(user_json_url)
        response.raise_for_status()
        response_data = response.json()

        country_code = response_data.get('user_country_code', '')
        phone_number = response_data.get('user_phone_number', '')
        first_name = response_data.get('user_first_name', '')
        last_name = response_data.get('user_last_name', '')

        if not phone_number:
            return JsonResponse({'error': 'Phone number is missing in response'}, status=400)

        complete_phone_number = f"{country_code}{phone_number}"

        # Check if the user exists
        user = User.objects.filter(username=complete_phone_number).first()
        if user is None:
            # Create user if not exists
            user = User.objects.create_user(username=complete_phone_number, password='defaultpassword')
            user.backend = 'ecommerce.auth_backends.CustomBackend'  # Set the backend attribute

        # Set user details
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        # Update or create the user profile
        user_profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'phone_number': complete_phone_number,
                'name': f"{first_name} {last_name}".strip()
            }
        )
        if not created:
            user_profile.phone_number = complete_phone_number
            user_profile.name = f"{first_name} {last_name}".strip()
            user_profile.save()

        # Log the user in
        login(request, user)

        cart_context = get_cart_context(request)
        context = {}
        context.update(cart_context)
        return redirect('/')


    except requests.RequestException as e:
        logger.error(f'Request error: {str(e)}')
        return JsonResponse({'error': 'Failed to fetch user details'}, status=500)
    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}')
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)
    
from django.contrib.auth import authenticate

# def authenticate_phone(phone_number):
#     try:
#         user = authenticate(username=phone_number, backend='ecommerce.auth_backends.CustomBackend')
#         return user
#     except User.DoesNotExist:
#         return None

def authenticate_phone(phone_number):
    backend = 'ecommerce.auth_backends.CustomBackend'
    user = authenticate(username=phone_number, backend=backend)
    print(f"Using backend: {backend}")
    return user

def refund_and_cancellation_policy(request):
    cart_context = get_cart_context(request)
    context = {}
    context.update(cart_context)
    return render(request, 'refund_and_cancellation_policy.html', context)

def shipping_and_delivery_policy(request):
    cart_context = get_cart_context(request)
    context = {}
    context.update(cart_context)
    return render(request, 'shipping_and_delivery_policy.html', context)

def terms_and_conditions(request):
    cart_context = get_cart_context(request)
    context = {}
    context.update(cart_context)
    return render(request, 'terms_and_conditions.html', context)

def privacy_policy(request):
    cart_context = get_cart_context(request)
    context = {}
    context.update(cart_context)
    return render(request, 'privacy_policy.html', context)

def shop(request):
    products = Product.objects.all()
    categories = ['Men', 'Women', 'Kids', 'Accessories']

    # Extract unique tags, sizes, and colors from product titles
    all_tags = sorted(list(set(tag for product in products for tag in product.name.split() if not tag.isdigit())))
    all_sizes = sorted(list(set(size for product in products for size in product.name.split() if size.upper() in ['S', 'M', 'L', 'XL', 'XXL'])))
    all_colors = sorted(list(set(color for product in products for color in product.name.split() if not color.isdigit() and not color.upper() in ['S', 'M', 'L', 'XL', 'XXL'])))


    # Filtering
    category = request.GET.get('category')
    if category:
        products = products.filter(name__icontains=category)

    min_price = request.GET.get('min_price')
    if min_price:
        products = products.filter(price__gte=min_price)

    max_price = request.GET.get('max_price')
    if max_price:
        products = products.filter(price__lte=max_price)

    tag = request.GET.get('tag')
    if tag:
        products = products.filter(name__icontains=tag)

    size = request.GET.get('size')
    if size:
        products = products.filter(name__icontains=size)

    color = request.GET.get('color')
    if color:
        products = products.filter(name__icontains=color)
    
    # Sorting
    sort_by = request.GET.get('sort_by')
    if sort_by == 'popularity':
        products = products.order_by('-id')  # Assuming popularity is related to views or sales
    elif sort_by == 'new_arrivals':
        products = products.order_by('-created_at')
    elif sort_by == 'price_low_to_high':
        products = products.order_by('price')
    elif sort_by == 'price_high_to_low':
        products = products.order_by('-price')
    elif sort_by == 'price':
        products = products.order_by('price')
    elif sort_by == '-price':
        products = products.order_by('-price')

    # Pagination
    paginator = Paginator(products, 12)  # Show 12 products per page
    page_number = request.GET.get('page')
    try:
        products = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        products = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        products = paginator.page(paginator.num_pages)

    cart_context = get_cart_context(request)
    context = {
        'products': products,
        'categories': categories,
        'all_tags': all_tags,
        'all_sizes': all_sizes,
        'all_colors': all_colors,
    }
    context.update(cart_context)
    return render(request, 'shop.html', context)
