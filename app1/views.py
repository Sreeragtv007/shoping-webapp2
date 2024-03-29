from django.shortcuts import redirect, render, get_object_or_404
from .models import *
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import FileResponse
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
import datetime
from pathlib import Path
from reportlab.lib.units import inch
import os
from django.conf import settings
from django.http import HttpResponse, Http404
from pathlib import Path
import razorpay
from django.http import HttpResponseBadRequest
import io


# Import xhtml2pdf if using HTML templates

# Import xhtml2pdf if using HTML templates


# Create your views here.


# category list


def index(request):

    category = Category.objects.all()

    context = {'category': category}

    posts = Product.objects.all()  # fetching all post objects from database
    p = Paginator(posts, 6)  # creating a paginator object
    # getting the desired page number from url
    page_number = request.GET.get('page')
    try:
        page_obj = p.get_page(page_number)  # returns the desired page object
    except PageNotAnInteger:
        # if page_number is not an integer then assign the first page
        page_obj = p.page(1)
    except EmptyPage:
        # if page is empty then return last page
        page_obj = p.page(p.num_pages)

    context = {'page_obj': page_obj, 'category': category}
    # sending the page object to index.html
    return render(request, 'index.html', context)


# searching by product name
def search_product(request):

    qu = None
    pr = None
    if 'qu' in request.GET:
        qu = request.GET.get('qu')
        pr = Product.objects.filter(name__icontains=qu)
        context = {'pr': pr}
        return render(request, 'product.html', context)
    else:

        return render(request, 'index.html')


def register(request):
    if request.POST:
        uname = request.POST.get('username')
        pass1 = request.POST.get('pass1')
        pass2 = request.POST.get('pass2')
        if User.objects.filter(username=uname).exists():
            messages.info(request, "user name taken")
            return redirect('register')

        elif pass1 == pass2:
            user = User.objects.create_user(username=uname, password=pass1)
            return redirect('login')
        else:
            messages.info(request, "password does not match")
            return redirect('register')

    return render(request, 'register.html')


def login_user(request):
    if request.POST:
        uname = request.POST.get('username')
        pass1 = request.POST.get('pass1')
        user = authenticate(username=uname, password=pass1)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.info(request, "user name or password is incorrect")
            return redirect('login')

    return render(request, 'login.html')


def logout_user(request):
    logout(request)
    return render(request, 'login.html')


def productDetails(request, pk):
    data = Product.objects.get(id=pk)
    obj = data.review_set.all()

    if request.POST:
        result = request.POST.get("review")

        review = Review.objects.create(
            review_body=result, user=request.user, product=data)
        return redirect('productdetails', pk=data.id)

    context = {'data': data, 'obj': obj}

    return render(request, 'productdetails.html', context)


@login_required(login_url='login')
def cart(request, pk):
    obj = Product.objects.get(id=pk)
    cart = Cart.objects.filter(user=request.user)
    for i in cart:
        if i.product.id == obj.id:
            messages.info(request, "product already added")
            return redirect('productdetails', pk=obj.id)

    cart = Cart.objects.create(user=request.user, product=obj)
    messages.info(request, "product added to cart")

    return redirect('productdetails', pk=obj.id)


def cartdeatil(request):

    cart = Cart.objects.filter(user=request.user)
    totalprice = 0
    for i in cart:
        totalprice = i.product.price+totalprice

    if len(cart) == 0:
        messages.info(request, 'cart is empty')
        return redirect('index')
    else:
        context = {'cart': cart, 'total': totalprice}

    return render(request, 'cart.html', context)


def removeCart(request, pk):

    cart = Cart.objects.get(id=pk)
    cart.delete()
    messages.info(request, "product removed from cart")

    return redirect('cartdetail')


def reviewDelet(request, pk):

    review = Review.objects.get(id=pk)
    if review.user.id == request.user.id:
        review.delete()
        return redirect('productdetails', pk=review.product.id)
    else:
        return redirect('productdetails', pk=review.product.id)


@login_required(login_url='login')
def buyProduct(request, pk):

    product = Product.objects.get(id=pk)
    if request.POST:
        address = request.POST.get('address')
        pincode = request.POST.get('pincode')
        qty = request.POST.get('qty')
        productname = product.name
      
    
        buyproduct = Buyproduct.objects.create(
            user=request.user, product=product, qty=qty, address=address, pincode=pincode)
        messages.info(request, "you purchase request is sucessfully created")

        # send_mail(
        #     f"your order sucess fully created {productname}",
        #     'sucsess',
        #     "digitalmediaupdates007@gmail.com",
        #     ["sreeragtv007@gmail.com"],
        #     fail_silently=False,
        # )
        # print('working')
        # print(type(totalprice))
        total=int(qty)*product.price*100
        

        return redirect('index1',pk=total)

    context = {'product': product}

    return render(request, 'buyproduct.html', context)


def buyProductfromcart(request):

    cartproduct = Cart.objects.filter(user=request.user)
    context = {'cartproduct': cartproduct}

    if request.POST:
        address = request.POST.get('address')
        pincode = request.POST.get('pincode')
        qty = request.POST.get('qty')

        for i in cartproduct:
            buyproduct = Buyproduct.objects.create(
                user=request.user, product=i.product, qty=qty, address=address, pincode=pincode)
        return redirect('index')
    return render(request, 'buyproductfromcart.html', context)


def userOrder(request):
    buyedproduct = Buyproduct.objects.filter(
        user=request.user).exclude(orderstatus='DELIVERED')

    if buyedproduct:
        context = {'buyedproduct': buyedproduct}
        return render(request, 'userorder.html', context)
    messages.info(request, 'you have no orders')
    return render(request, 'userorder.html')


def cancelOrder(request, pk):
    cancelorder = Buyproduct.objects.filter(id=pk)
    context = {'cancelorder': cancelorder}

    if request.method == 'POST':

        cancelorder.delete()
        messages.info(request, "you order has been sucessfully canceled")
        if cancelOrder:
            return redirect('userorder')
        return redirect('index')

    return render(request, 'cancelorder.html', context)


def userProfile(request):

    orderdelivered = Buyproduct.objects.filter(
        user=request.user, orderstatus='DELIVERED')
    invoice = Buyproduct.objects.filter(
        user=request.user, orderstatus='DELIVERED').filter(invoice_created=False)
    context = {'obj': orderdelivered}
    if invoice:
        for i in invoice:
            time = datetime.datetime.today()
            file_path = os.path.join(settings.MEDIA_ROOT, i.product.image.path)

            # Create a PDF buffer in memory
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer)
            p.drawString(30, 800, f'Date{time}')
            p.drawString(100, 750, f'Product name :{i.product.name}')
            p.drawImage(file_path, 400, 700, 100, 100)
            p.drawString(100, 700, f'quantity  :{i.qty}')
            p.drawString(100, 650, f'total price  :{i.totalprice}')
            p.drawString(100, 600, f'address :{i.address}{i.pincode}')
            p.drawString(100, 550, f'purchase time  :{i.purchased_time}')

            p.showPage()
            p.save()

        # Retrieve the generated PDF as bytes
            pdf_file = buffer.getvalue()

            # Create a new model instance and save the PDF:
            # my_model = Savepdf.objects.create(name='example1')

            i.file.save(f'generated_pdf{i.id}.pdf', ContentFile(pdf_file))
            i.invoice_created = True
            i.save()

            return render(request, "userprofile.html", context)
    return render(request, "userprofile.html", context)


def downloadInvoice(request, pk):
    obj = Buyproduct.objects.get(product_id=pk)
    file_path = os.path.join(settings.MEDIA_ROOT, obj.file.path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(
                fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + \
                os.path.basename(file_path)
            return response
    raise Http404


razorpay_client = razorpay.Client(
    auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))



def homepage(request,pk):
    currency = 'INR'
    amount = pk  # Rs. 200
 
    # Create a Razorpay Order
    razorpay_order = razorpay_client.order.create(dict(amount=amount,
                                                       currency=currency,
                                                       payment_capture='0'))
 
    # order id of newly created order.
    razorpay_order_id = razorpay_order['id']
    callback_url = 'paymenthandler/'
 
    # we need to pass these details to frontend.
    context = {}
    context['razorpay_order_id'] = razorpay_order_id
    context['razorpay_merchant_key'] = settings.RAZOR_KEY_ID
    context['razorpay_amount'] = amount
    context['currency'] = currency
    context['callback_url'] = callback_url
 
    return render(request, 'index1.html', context=context)
 
 
# we need to csrf_exempt this url as
# POST request will be made by Razorpay
# and it won't have the csrf token.

def paymenthandler(request):
 
    # only accept POST request.
    if request.method == "POST":
        try:
           
            # get the required parameters from post request.
            payment_id = request.POST.get('razorpay_payment_id', '')
            razorpay_order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')
            amount=request.post.get('razorpay_amount','')
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
 
            # verify the payment signature.
            result = razorpay_client.utility.verify_payment_signature(
                params_dict)
            if result is not None:
                
                amount = amount  # Rs. 200
                try:
 
                    # capture the payemt
                    razorpay_client.payment.capture(payment_id, amount)
 
                    # render success page on successful caputre of payment
                    return render(request, 'paymentsuccess.html')
                except:
 
                    # if there is an error while capturing payment.
                    return render(request, 'paymentfail.html')
            else:
 
                # if signature verification fails.
                return render(request, 'paymentfail.html')
        except:
 
            # if we don't find the required parameters in POST data
            return HttpResponseBadRequest()
    else:
       # if other than POST request is made.
        return HttpResponseBadRequest()