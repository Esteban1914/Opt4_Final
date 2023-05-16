from django.shortcuts import render,redirect
from django.http import HttpResponse,HttpResponseBadRequest,JsonResponse
from .models import Manager
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json

manager=Manager()

def redirect_process(request):
    return redirect('process')
def process(request):
    mode=manager.get_mode()
    context={}
    context.update({'active':manager.get_active(),'mode':manager.get_mode()})
    if mode==0:
        print("A")
        return render(request,"Manual.html",context)     
    return render(request,"Process.html",context) 
def config(request):
    try:
        context={}
        context.update({'active':manager.get_active(),'mode':manager.get_mode()})
        if request.method=="POST":
            if "SetMode" in request.POST:
                form=request.POST.dict()
                mode=int(form.get("group"))
                if mode: 
                    manager.set_mode(mode)
                    messages.success(request,"Modo {} asignado".format(mode))
                    return redirect(config)
        return render(request,"Config.html",context)
    except Exception as e:
        messages.error("Error:{}".format(e))
        return redirect('process') 
@csrf_exempt
def base_post(request):
    active=manager.get_active()
    if request.method == "POST":
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest': 
            data = json.load(request)
            if 'BtnActDesact' in data:
                if active:
                    manager.desactivate()
                else:    
                    manager.activate()
                return HttpResponse("OK_D" if active == True else "OK_A")    
            elif 'GetData' in data:
                if active == False:
                    return JsonResponse({'NoActive':True})
                level=manager.get_level()
                valve=manager.get_valve()
                bomb=manager.get_bomb()
                return JsonResponse({"level":level,"valve":valve,"bomb":bomb})
                return HttpResponse(level)      
    return HttpResponseBadRequest()
    #return render(request,"Home.html",{'active':active}) 

