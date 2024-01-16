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
        productname=product.name

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

        return redirect('index')

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

    orderdelivered = Buyproduct.objects.filter(user=request.user,orderstatus='DELIVERED')
    context = {'obj': orderdelivered}

    return render(request, "userprofile.html", context)


def orderInvoice(request):
    orderdelivered = Buyproduct.objects.filter(user=request.user,orderstatus='DELIVERED')
    print(orderdelivered)
    # Fetch data to include in the PDF

    # Create a PDF buffer in memory
    buffer = io.BytesIO()

    # Use ReportLab to generate the PDF content:
    p = canvas.Canvas(buffer)
    # ... Add PDF elements (text, images, etc.) using ReportLab's API
    # p.drawString(100, 100, f"custermer name :{user}")
    p.drawString(0,800,'Date')
    p.drawString(0,700,'Product name :')
    p.drawString(0,600,'quantity')
    p.drawString(0,500,'total price')
    p.drawString(0,400,'address')

    p.drawString(0,400,'purchase time')

    p.showPage()
    p.save()

    # Retrieve the generated PDF as bytes
    pdf_file = buffer.getvalue()

    # Create a new model instance and save the PDF:
    my_model = Savepdf.objects.create(name='example1')
    my_model.file.save('generated_pdf.pdf', ContentFile(pdf_file))
    return redirect('index')
    # Return the PDF as a response (optional, for immediate download)
    return FileResponse(buffer, as_attachment=True, filename='generated_pdf.pdf')

