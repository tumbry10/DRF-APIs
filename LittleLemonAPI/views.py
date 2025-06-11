from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import Group, User
from django.shortcuts import get_object_or_404
from . models import MenuItem, Cart, Order, OrderItem
from . serializers import MenuItemSerializer, CartSerializer, OrderSerializer, UserSerializer, GroupSerializer
from . permissions import IsManager, IsDeliveryCrew
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.core.paginator import Paginator, EmptyPage

@api_view(['GET', 'POST'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def menu_items(request):
    if request.method == 'GET':
        items = MenuItem.objects.all()
        
        # Filtering
        category_name = request.query_params.get('category')
        to_price = request.query_params.get('to_price')
        featured = request.query_params.get('featured')
        search = request.query_params.get('search')
        
        if category_name:
            items = items.filter(category__title=category_name)
        if to_price:
            items = items.filter(price__lte=to_price)
        if featured:
            items = items.filter(featured=featured.lower() == 'true')
        if search:
            items = items.filter(title__icontains=search)
        
        # Sorting
        sort_by = request.query_params.get('sort_by')
        if sort_by:
            items = items.order_by(sort_by)
        
        # Pagination
        perpage = request.query_params.get('perpage', default=10)
        page = request.query_params.get('page', default=1)
        paginator = Paginator(items, per_page=perpage)
        
        try:
            items = paginator.page(number=page)
        except EmptyPage:
            items = []
        
        serializer = MenuItemSerializer(items, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        if not request.user.groups.filter(name='Manager').exists():
            return Response({"message": "Only Managers can add menu items"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = MenuItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def single_menu_item(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    
    if request.method == 'GET':
        serializer = MenuItemSerializer(item)
        return Response(serializer.data)
    
    if not request.user.groups.filter(name='Manager').exists():
        return Response({"message": "Only Managers can modify menu items"}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method in ['PUT', 'PATCH']:
        serializer = MenuItemSerializer(item, data=request.data, partial=request.method == 'PATCH')
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsManager])
@throttle_classes([UserRateThrottle])
def managers(request):
    manager_group = Group.objects.get(name='Manager')
    
    if request.method == 'GET':
        managers = User.objects.filter(groups=manager_group)
        serializer = UserSerializer(managers, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        username = request.data.get('username')
        if not username:
            return Response({"message": "Username is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = get_object_or_404(User, username=username)
        user.groups.add(manager_group)
        return Response({"message": f"User {username} added to Managers group"}, status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsManager])
@throttle_classes([UserRateThrottle])
def manager(request, pk):
    manager_group = Group.objects.get(name='Manager')
    user = get_object_or_404(User, pk=pk)
    
    if manager_group not in user.groups.all():
        return Response({"message": "User is not a Manager"}, status=status.HTTP_404_NOT_FOUND)
    
    user.groups.remove(manager_group)
    return Response({"message": f"User {user.username} removed from Managers group"}, status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsManager])
@throttle_classes([UserRateThrottle])
def delivery_crew(request):
    crew_group = Group.objects.get(name='Delivery crew')
    
    if request.method == 'GET':
        crew = User.objects.filter(groups=crew_group)
        serializer = UserSerializer(crew, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        username = request.data.get('username')
        if not username:
            return Response({"message": "Username is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = get_object_or_404(User, username=username)
        user.groups.add(crew_group)
        return Response({"message": f"User {username} added to Delivery Crew group"}, status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsManager])
@throttle_classes([UserRateThrottle])
def crew_member(request, pk):
    crew_group = Group.objects.get(name='Delivery crew')
    user = get_object_or_404(User, pk=pk)
    
    if crew_group not in user.groups.all():
        return Response({"message": "User is not in Delivery Crew"}, status=status.HTTP_404_NOT_FOUND)
    
    user.groups.remove(crew_group)
    return Response({"message": f"User {user.username} removed from Delivery Crew group"}, status=status.HTTP_200_OK)

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def cart(request):
    if request.method == 'GET':
        cart_items = Cart.objects.filter(user=request.user)
        serializer = CartSerializer(cart_items, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CartSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        Cart.objects.filter(user=request.user).delete()
        return Response({"message": "Cart cleared"}, status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def orders(request):
    if request.method == 'GET':
        if request.user.groups.filter(name='Manager').exists():
            orders = Order.objects.all()
        elif request.user.groups.filter(name='Delivery crew').exists():
            orders = Order.objects.filter(delivery_crew=request.user)
        else:
            orders = Order.objects.filter(user=request.user)
        
        # Filtering
        status_filter = request.query_params.get('status')
        date = request.query_params.get('date')
        
        if status_filter is not None:
            orders = orders.filter(status=status_filter.lower() == 'true')
        if date:
            orders = orders.filter(date=date)
        
        # Pagination
        perpage = request.query_params.get('perpage', default=10)
        page = request.query_params.get('page', default=1)
        paginator = Paginator(orders, per_page=perpage)
        
        try:
            orders = paginator.page(number=page)
        except EmptyPage:
            orders = []
        
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response({"message": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
        
        total = sum(item.price for item in cart_items)
        order = Order.objects.create(
            user=request.user,
            total=total,
            status=False
        )
        
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                menuitem=item.menuitem,
                quantity=item.quantity,
                unit_price=item.unit_price,
                price=item.price
            )
        
        cart_items.delete()
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def order(request, pk):
    if request.user.groups.filter(name='Manager').exists():
        order = get_object_or_404(Order, pk=pk)
    elif request.user.groups.filter(name='Delivery crew').exists():
        order = get_object_or_404(Order, pk=pk, delivery_crew=request.user)
    else:
        order = get_object_or_404(Order, pk=pk, user=request.user)
    
    if request.method == 'GET':
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        if request.user.groups.filter(name='Delivery crew').exists():
            # Delivery crew can only update status
            if 'status' in request.data and len(request.data) == 1:
                serializer = OrderSerializer(order, data={'status': request.data['status']}, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(
                {"message": "Delivery crew can only update order status"},
                status=status.HTTP_403_FORBIDDEN
            )
        elif request.user.groups.filter(name='Manager').exists():
            # Managers can update delivery crew and status
            serializer = OrderSerializer(order, data=request.data, partial=request.method == 'PATCH')
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {"message": "Only managers and delivery crew can update orders"},
                status=status.HTTP_403_FORBIDDEN
            )
    
    elif request.method == 'DELETE':
        if not request.user.groups.filter(name='Manager').exists():
            return Response(
                {"message": "Only managers can delete orders"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        order.delete()
        return Response({"message": "Order deleted"}, status=status.HTTP_200_OK)