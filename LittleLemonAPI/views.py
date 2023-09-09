from rest_framework import generics
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, JsonResponse
from .models import MenuItem, Cart, Order, OrderItem, Category
from .serializers import (MenuItemSerializer, ManagerListSerializer, CartSerializer, 
                          OrderSerializer, CartAddSerializer, CartRemoveSerializer,
                            SingleOrderSerializer, OrderPutSerializer, CategorySerializer)
from .paginations import MenuItemListPagination
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.models import User, Group
from .permissions import IsManager, IsDeliveryCrew
import math
from datetime import date

# Define a class-based view to represent the list of MenuItems.
class MenuItemListView(generics.ListCreateAPIView):

    # Throttle classes determine the rate limits for the API view.
    # - AnonRateThrottle: Rate limiting for anonymous (unauthenticated) users.
    # - UserRateThrottle: Rate limiting for authenticated users.
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    # Define the queryset from which the list of MenuItems will be derived.
    queryset = MenuItem.objects.all()

    # Specify the serializer that will be used to convert the MenuItems into a format suitable for the API response.
    serializer_class = MenuItemSerializer

    # Specify the fields on which users can search. Users can search by title and by the title of the related category.
    search_fields = ['title', 'category__title']

    # Define the fields on which users can order the results. They can order by price and category.
    ordering_fields = ['price', 'category']

    # Set the pagination class that will be used for paginating the results.
    pagination_class = MenuItemListPagination

    # Override the get_permissions method to define custom permissions.
    def get_permissions(self):
        # Start with an empty list of permissions.
        permission_classes = []

        # If the HTTP request method is anything other than a GET (e.g., POST, PUT, DELETE), 
        # then require the user to be authenticated and also be an admin.
        if self.request.method != 'GET':
            permission_classes = [IsAuthenticated, IsAdminUser]

        # Instantiate and return the list of permission classes.
        return [permission() for permission in permission_classes]

class CategoryView(generics.ListCreateAPIView):
    # Rate limits based on user type.
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    # Serializer to convert Category objects for the API.
    serializer_class = CategorySerializer
    
    # Main dataset for Category.
    queryset = Category.objects.all()
    
    # Only admin users have permission to access this view.
    permission_classes = [IsAdminUser]


class MenuItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    # Rate limits based on user type.
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    # Main dataset for MenuItem.
    queryset = MenuItem.objects.all()
    
    # Serializer to convert MenuItem objects for the API.
    serializer_class = MenuItemSerializer
    
    # Define custom permissions based on request methods.
    def get_permissions(self):
        if self.request.method == 'PATCH':
            # Managers or Admins can update via PATCH.
            permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
        elif self.request.method == "DELETE":
            # Only Admins can delete.
            permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            # For other methods, authentication is enough.
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    # Override the PATCH method to toggle the 'featured' attribute.
    def patch(self, request, *args, **kwargs):
        menuitem = MenuItem.objects.get(pk=self.kwargs['pk'])
        menuitem.featured = not menuitem.featured
        menuitem.save()
        return JsonResponse(
            status=200, 
            data={
                'message':'Featured status of {} changed to {}'.format(
                    str(menuitem.title), 
                    str(menuitem.featured)
                )
            }
        )


class ManagersListView(generics.ListCreateAPIView):
    # Rate limits based on user type.
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    # Get all users in the 'Managers' group.
    queryset = User.objects.filter(groups__name='Managers')
    
    # Serializer to convert user objects for the API.
    serializer_class = ManagerListSerializer
    
    # Only authenticated managers or admins can access this view.
    permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
    
    # Handle POST requests: adding users to the 'Managers' group.
    def post(self, request, *args, **kwargs):
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
            managers = Group.objects.get(name='Managers')
            managers.user_set.add(user)

            return JsonResponse(status=201, data={'message':'User added to Managers group'}) 


class ManagersRemoveView(generics.DestroyAPIView):
    # Rate limits based on user type.
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    # Serializer to convert user objects for the API.
    serializer_class = ManagerListSerializer
    
    # Only authenticated managers or admins can access this view.
    permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
    
    # Get all users in the 'Managers' group.
    queryset = User.objects.filter(groups__name='Managers')
    
    # Handle DELETE requests: remove users from the 'Managers' group.
    def delete(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        user = get_object_or_404(User, pk=pk)
        managers = Group.objects.get(name='Managers')
        managers.user_set.remove(user)
        return JsonResponse(status=200, data={'message':'User removed Managers group'})


class DeliveryCrewListView(generics.ListCreateAPIView):
    # Rate limits based on user type.
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    # Get all users in the 'Delivery crew' group.
    queryset = User.objects.filter(groups__name='Delivery crew')
    
    # Serializer to convert user objects for the API.
    serializer_class = ManagerListSerializer  # Assuming you're reusing this serializer; might need renaming for clarity.
    
    # Only authenticated managers or admins can access this view.
    permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
    
    # Handle POST requests: add users to the 'Delivery crew' group.
    def post(self, request, *args, **kwargs):
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
            crew = Group.objects.get(name='Delivery crew')
            crew.user_set.add(user)
            return JsonResponse(status=201, data={'message':'User added to Delivery Crew group'})


class DeliveryCrewRemoveView(generics.DestroyAPIView):
    # Rate limits based on user type.
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    # Serializer to convert user objects for the API.
    serializer_class = ManagerListSerializer  # Note: You're reusing the ManagerListSerializer. Consider renaming for clarity.
    
    # Only authenticated managers or admins can access this view.
    permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
    
    # Get all users in the 'Delivery crew' group.
    queryset = User.objects.filter(groups__name='Delivery crew')
    
    # Handle DELETE requests: remove users from the 'Delivery crew' group.
    def delete(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        user = get_object_or_404(User, pk=pk)
        crew = Group.objects.get(name='Delivery crew')
        crew.user_set.remove(user)
        return JsonResponse(status=201, data={'message':'User removed from the Delivery crew group'})


class CartOperationsView(generics.ListCreateAPIView):
    # Rate limits based on user type.
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    # Serializer to convert cart objects for the API.
    serializer_class = CartSerializer
    
    # Only authenticated users can access this view.
    permission_classes = [IsAuthenticated]

    # Retrieves the authenticated user's cart items.
    def get_queryset(self, *args, **kwargs):
        cart = Cart.objects.filter(user=self.request.user)
        return cart

    # Handle POST requests: add an item to the cart.
    def post(self, request, *arg, **kwargs):
        serialized_item = CartAddSerializer(data=request.data)
        serialized_item.is_valid(raise_exception=True)
        id = request.data['menuitem']
        quantity = request.data['quantity']
        item = get_object_or_404(MenuItem, id=id)
        price = int(quantity) * item.price
        try:
            Cart.objects.create(user=request.user, quantity=quantity, unit_price=item.price, price=price, menuitem_id=id)
        except:
            return JsonResponse(status=409, data={'message':'Item already in cart'})
        return JsonResponse(status=201, data={'message':'Item added to cart!'})

    # Handle DELETE requests: remove one or all items from the cart.
    def delete(self, request, *arg, **kwargs):
        if request.data['menuitem']:
            serialized_item = CartRemoveSerializer(data=request.data)
            serialized_item.is_valid(raise_exception=True)
            menuitem = request.data['menuitem']
            cart = get_object_or_404(Cart, user=request.user, menuitem=menuitem)
            cart.delete()
            return JsonResponse(status=200, data={'message':'Item removed from cart'})
        else:
            Cart.objects.filter(user=request.user).delete()
            return JsonResponse(status=201, data={'message':'All Items removed from cart'})


class OrderOperationsView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = OrderSerializer
        
    def get_queryset(self, *args, **kwargs):
        if self.request.user.groups.filter(name='Managers').exists() or self.request.user.is_superuser == True :
            query = Order.objects.all()
        elif self.request.user.groups.filter(name='Delivery crew').exists():
            query = Order.objects.filter(delivery_crew=self.request.user)
        else:
            query = Order.objects.filter(user=self.request.user)
        return query

    def get_permissions(self):
        
        if self.request.method == 'GET' or 'POST' : 
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
        return[permission() for permission in permission_classes]

    def post(self, request, *args, **kwargs):
        cart = Cart.objects.filter(user=request.user)
        x=cart.values_list()
        if len(x) == 0:
            return HttpResponseBadRequest()
        total = math.fsum([float(x[-1]) for x in x])
        order = Order.objects.create(user=request.user, status=False, total=total, date=date.today())
        for i in cart.values():
            menuitem = get_object_or_404(MenuItem, id=i['menuitem_id'])
            orderitem = OrderItem.objects.create(order=order, menuitem=menuitem, quantity=i['quantity'])
            orderitem.save()
        cart.delete()
        return JsonResponse(status=201, data={'message':'Your order has been placed! Your order number is {}'.format(str(order.id))})

class SingleOrderView(generics.ListCreateAPIView):
    # Apply rate limiting for different types of users.
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    # Use this serializer to convert Order data for the API.
    serializer_class = SingleOrderSerializer
    
    # Determine the permissions needed based on the type of request and user's relation to the order.
    def get_permissions(self):
        order = Order.objects.get(pk=self.kwargs['pk'])
        if self.request.user == order.user and self.request.method == 'GET':
            permission_classes = [IsAuthenticated]
        elif self.request.method in ['PUT', 'DELETE']:
            permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
        else:
            permission_classes = [IsAuthenticated, IsDeliveryCrew | IsManager | IsAdminUser]
        return [permission() for permission in permission_classes] 

    # Return the items associated with the specified order.
    def get_queryset(self):
        return OrderItem.objects.filter(order_id=self.kwargs['pk'])

    # Toggle the order status.
    def patch(self, request, *args, **kwargs):
        order = Order.objects.get(pk=self.kwargs['pk'])
        order.status = not order.status
        order.save()
        return JsonResponse(status=200, data={'message': 'Status of order #{} changed to {}'.format(order.id, order.status)})

    # Update the order with a specified delivery crew member.
    def put(self, request, *args, **kwargs):
        serialized_item = OrderPutSerializer(data=request.data)
        serialized_item.is_valid(raise_exception=True)
        order = get_object_or_404(Order, pk=self.kwargs['pk'])
        crew = get_object_or_404(User, pk=request.data['delivery_crew'])
        order.delivery_crew = crew
        order.save()
        return JsonResponse(status=201, data={'message': '{} was assigned to order #{}'.format(crew.username, order.id)})

    # Delete the specified order.
    def delete(self, request, *args, **kwargs):
        order = Order.objects.get(pk=self.kwargs['pk'])
        order.delete()
        return JsonResponse(status=200, data={'message': 'Order #{} was deleted'.format(order.id)})


