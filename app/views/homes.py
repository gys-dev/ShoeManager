from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from app.models import Shoe, Size, Stock, User, Cart, CartDetail
from app.utils import getShoeWithMax, serialize, parseOne, parseMany, serializeMany
from django.contrib.auth import logout as AuthLogout


def index(request):
    shoes = Shoe.objects.all()
    dealOfWeek = getShoeWithMax(shoes)

    context = {
        "menu_active": 0,
        "deal_of_week": dealOfWeek
    }


    return render(request, 'app/index.html', context)

def detail(request, product_id):
    session = request.session
    shoe = Shoe.objects.get(pk=product_id)

    context = {
        "menu_active": 0,
        "shoe": shoe
    }
    if session.get('user', False):
        user = session.get('user', None)
        context['user'] = parseOne(user)
    return render(request, 'app/single-product.html', context)

def category(request):
    session = request.session

    sizes = Size.objects.all()

    selectedSize = request.GET.get('size_id', '')
    shoes = []
    dealOfWeek = getShoeWithMax(Shoe.objects.all())

    if selectedSize:
        def shoe(x):
            return x.shoe

        stocks = Stock.objects.filter(size=selectedSize)
        shoes = map(shoe, stocks)
    else:
        shoes = Shoe.objects.all()



    context = {
        "menu_active": 0,
        "sizes": sizes,
        "shoes": shoes,
        "deal_of_week": dealOfWeek,

    }
    if session.get('user', False):
        user = session.get('user', None)
        context['user'] = parseOne(user)

    return render(request, 'app/category.html', context)

def category_add(request, shoe_id):
    session = request.session
    targetShoe = Shoe.objects.get(pk=shoe_id)
    rawShoes = session.get('cart', [])

    shoes = []

    if rawShoes:
        shoes = parseMany(rawShoes)

    shoes.append(targetShoe)
    session['cart'] = serializeMany(shoes)
    return redirect('/')

def card_update(request):
    if request.method == 'POST':
        session = request.session
        itemArray = request.POST.getlist('shop_id')
        amountArray = request.POST.getlist('shop_number')

        listSSShoes = []

        if (len(itemArray) > 0):
            del session['cart']

            for i, shoeId in enumerate(itemArray):
                shoe = Shoe.objects.get(pk=int(shoeId))
                j = 1
                while j <= int(amountArray[i]):
                    listSSShoes.append(shoe)
                    j = j + 1
            session['cart'] = serializeMany(listSSShoes)

        return redirect('/cart/')

    else:
        return redirect('/cart/')

def cart(request):
    session = request.session
    context = {
        "menu_active": 1
    }
    if session.get('user', False):
        user = session.get('user', None)
        context['user'] = parseOne(user)

        rawShoes = session.get('cart', [])
        listCartShoe = []

        if rawShoes:
            listCartShoe = parseMany(rawShoes)
        dict = {}

        for shoe in listCartShoe:
            if shoe in dict:
                dict[shoe] = dict[shoe] + 1
            else:
                dict[shoe] = 1

        total = 0
        for key, value in dict.items():
            total = total + key.price * value
        context['shoe_detail'] = list(dict.keys())
        context['shoe_order'] = dict
        context['total'] = total


        return render(request, 'app/cart.html', context)
    else:
        return redirect('/login/')

def checkout(request):
    session = request.session
    if not session.get('user', False):
        return redirect('/login/')

    rawUser = session.get('user', None)
    user = parseOne(rawUser)
    cart = Cart.objects.create(user_create=user, da_duyet=False)

    listShoe = []
    rawShoes = session.get('cart', [])
    if len(rawShoes):
        listShoe = parseMany(rawShoes)
    else:
        return redirect('/cart/')
    dictDistince = {}
    for shoe in listShoe:
        if shoe in dictDistince:
            dictDistince[shoe] = dictDistince[shoe] + 1
        else:
            dictDistince[shoe] = 1

    if len(dictDistince.keys()) > 0:
        for shoe in dictDistince.keys():
            CartDetail.objects.create(cart=cart, shoe=shoe, amount=dictDistince[shoe])

    del session['cart']
    return redirect('/cart/')

def history(request):
    session = request.session
    context = {
        "menu_active": 2
    }
    if session.get('user', False):
        rawUser = session.get('user', None)
        context['user'] = parseOne(rawUser)
        user = parseOne(rawUser)
        carts = Cart.objects.filter(user_create=user)
        context['carts'] = carts

        cartTotal = {}
        for cart in carts:
            cartDetail = CartDetail.objects.filter(cart=cart)
            total = 0
            for item in cartDetail:
                total = item.amount * item.shoe.price
            cartTotal[cart] = total

        if len(list(cartTotal.keys())) > 0:
            context['cart_total'] = cartTotal.items()
        return render(request, 'app/history.html', context)
    else:
        return redirect('/login/')
def login(request):
   session = request.session
   if request.method == 'GET':

       if session.get('user', False):
            return redirect('/')
       else:
            context = {
                "menu_active": 3
            }
            return render(request, 'app/login.html', context)
   else:
       username = request.POST.get('username', '')
       password = request.POST.get('password', '')
       context = {
           "menu_active": 3
       }
       user = authenticate(username=username, password=password)

       if user:
           session['user'] = serialize(user)
           return redirect('/cart/')
       else:
           context['error'] = "Login Failed"
           return render(request, 'app/login.html', context)

def logout(request):
    try:
        AuthLogout(request)
        del request.session['user']
    except KeyError:
        pass
    return redirect('/')



def register(request):
    session = request.session
    context = {
        "menu_active": 4
    }

    if request.method == 'GET':
        if session.get('user', False):
            return redirect('/')
        else:
            context = {
                "menu_active": 4
            }
            return render(request, 'app/user_register.html', context)
    else:
        try:
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
            repassword = request.POST.get('repassword', '')
            firstname = request.POST.get('firstname', '')
            lastname = request.POST.get('lastname', '')

            if password == repassword:
                if User.objects.filter(username=username).filter():
                    context['error'] = "Username already taken"
                    return render(request, 'app/user_register.html', context)
                else:
                    User.objects.create_user(username, firstname, lastname, password)

                    return redirect("/login")
            else:
                context['error'] = "Password not match"
                return render(request, 'app/user_register.html', context)
        except User.DoesNotExist:
            return redirect("/")


