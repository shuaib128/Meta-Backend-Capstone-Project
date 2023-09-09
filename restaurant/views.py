# from django.http import HttpResponse
from django.shortcuts import render
from .forms import BookingForm
from .models import Menu
from django.core import serializers
from .models import Booking
from datetime import datetime
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse



# Create your views here.
def home(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def reservations(request):
    date = request.GET.get('date',datetime.today().date())
    bookings = Booking.objects.all()
    booking_json = serializers.serialize('json', bookings)
    return render(request, 'bookings.html',{"bookings":booking_json})

def book(request):
    form = BookingForm()
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            form.save()
    context = {'form':form}
    return render(request, 'book.html', context)

# Add your code here to create new views

def menu(request):
    menu_data = Menu.objects.all()
    main_data = {"menu" : menu_data}
    return render(request, 'menu.html', {"menu": main_data})

def display_menu_item(request, pk=None):
    if pk: 
        menu_item = Menu.objects.get(pk=pk) 
    else: 
        menu_item = "" 
    return render(request, 'menu_item.html', {"menu_item": menu_item}) 

@csrf_exempt
def bookings(request):
    # If the request method is POST, we attempt to create a new booking
    if request.method == 'POST':
        # Parse the incoming request data as JSON
        data = json.load(request)
        
        # Check if a booking already exists with the provided date and slot
        exist = Booking.objects.filter(reservation_date=data['reservation_date']).filter(
            reservation_slot=data['reservation_slot']).exists()
        
        # If no booking exists for the given date and slot, create a new booking
        if exist==False:
            booking = Booking(
                first_name=data['first_name'],
                reservation_date=data['reservation_date'],
                reservation_slot=data['reservation_slot'],
            )
            booking.save()
        else:
            # If a booking already exists for the given date and slot, return an error
            return HttpResponse("{'error':1}", content_type='application/json')
    
    # If the request method is not POST, or even after handling POST,
    # get the bookings for the provided date or the current date if none is provided
    date = request.GET.get('date',datetime.today().date())
    
    # Retrieve all bookings for the given date
    bookings = Booking.objects.all().filter(reservation_date=date)
    
    # Serialize the bookings as JSON
    booking_json = serializers.serialize('json', bookings)

    # Return the serialized bookings as the response
    return HttpResponse(booking_json, content_type='application/json')
