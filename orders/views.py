from django.shortcuts import render,redirect
from django.http import HttpResponse,JsonResponse
# Create your views here.
from cart.models import cartitem
from .forms import OrderForm
from .models import Order,Payment,OrderProduct
import datetime
import json
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


def peyments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_order=False, order_number=body['orderID'])
    peyment = Payment(
        user=request.user,
        peyment_id=body['transID'],
        peyment_method = body['peyment_method'],
        amount_paid = order.order_total,
        status = body['status'],

    )
    peyment.save()
    order.peyment = peyment
    order.is_order=True
    order.save()
#crate orderprouct and set variation
    cart_item=cartitem.objects.filter(user=request.user)
    for item in cart_item:
        orderproduct = OrderProduct()
        orderproduct.order_id=order.id
        orderproduct.peyment = peyment
        orderproduct.user_id= request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.is_ordered = True
        orderproduct.save()

        cart_item = cartitem.objects.get(id= item.id)
        product_variation = cart_item.variations.all()
        orderproduct =OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variation.set(product_variation)
        orderproduct.save()

        #reduce Quantity
        product = Product.objects.get(id= item.product_id)
        product.stock -=item.quantity
        product.save()

    #cleare cartitem
    cartitem.objects.filter(user=request.user).delete()
    #send email
    mail_subject = 'Thank you for your shopping'
    message = render_to_string('orders/order_recieved_email.html',{
        'user':request.user,
        'order':order,
    })
    to_email =request.user.email
    send_email = EmailMessage(mail_subject,message,to=[to_email])
    send_email.send()
    #send order number and transid by JSON
    data ={
        'order_number':order.order_number,
        'transID':peyment.peyment_id,
    }

    return JsonResponse(data)


def place_order(request,total=0,quantity=0,):
    current_user = request.user

    cart_items = cartitem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    tax =0
    grand_total = 0
    for cart_item in cart_items:
        total +=(cart_item.product.price * cart_item.quantity)
        quantity +=cart_item.quantity
    tax = (2 * total)/100
    grand_total = total + tax
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            data= Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total= grand_total
            data.tax=tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            yr=int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            created_date = d.strftime("%y%m%d")
            order_number = created_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_order=False, order_number=order_number)
            context = {
                'order':order,
                'cart_items': cart_items,
                'tax': tax,
                'total':total,
                'grand_total':grand_total,
            }
            # return redirect('checkout')
            return render(request,'orders/peyments.html',context)
    else:
        return redirect('checkout')
def order_complete(request):
    order_number = request.GET.get('order_number')
    transID= request.GET.get('peyment_id')
    try:
        order = Order.objects.get(order_number=order_number,is_order=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal= 0
        for i in ordered_products:
            subtotal +=i.product_price * i.quantity

        peyment = Payment.objects.get(peyment_id=transID)

        context = {
            'order':order,
            'ordered_products':ordered_products,
            'order_number':order.order_number,
            'transID':peyment.peyment_id,
            'peyment':peyment,
            'subtotal':subtotal,
        }

        return render(request,'orders/order_complete.html',context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
