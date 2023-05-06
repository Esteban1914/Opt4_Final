from django.shortcuts import render
from django.http import JsonResponse,HttpResponse
from .Class.MySensor import MySensor
import json

my_sensor=MySensor()

def Home(request):
    
    if request.method == "POST":
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest': 
            data = json.load(request)
            if 'BtnActDesact' in data:
                active=my_sensor.get_active()
                if active:
                    my_sensor.desactivate()
                else:    
                    my_sensor.activate()
                return HttpResponse("OK_D" if active == True else "OK_A")    
            elif 'GetData' in data:
                data=my_sensor.get_data()
                if not data:
                    return HttpResponse('NoActive')
                return HttpResponse(data)
            
    return render(request,"Home.html",{'active':my_sensor.get_active()}) 

