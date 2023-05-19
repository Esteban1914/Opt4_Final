from django.shortcuts import render,redirect
from django.http import HttpResponse,HttpResponseBadRequest,JsonResponse
from .models import Manager
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json


manager=Manager()
MODE={
    0:"Manual",
    1:"PID Entrada Controlada",
    2:"PID Salida Controlada",
    3:"PID Control Paralelo",
}

def redirect_process(request):
    return redirect('process')

def process(request):
    mode=manager.get_mode()
    context={}
    context.update({'active':manager.get_active(),"set_point":manager.get_set_point(),'mode':manager.get_mode(),"modeStr":MODE.get(manager.get_mode())})
    return render(request,"Process.html",context) 

def config(request):
    try:
        context={}
        active=manager.get_active()
        context.update({'active':active,'mode':manager.get_mode(),"set_point":manager.get_set_point(),"modeStr":MODE.get(manager.get_mode())})
        if request.method=="POST":
            if "SetMode" in request.POST:
                form=request.POST.dict()
                mode=int(form.get("group"))
                print(mode)
                if mode or mode==0: 
                    manager.set_mode(mode)
                    context.update({"modeStr":MODE.get(manager.get_mode())})
                    #messages.success(request,"Modo {} asignado".format(mode))
                    if active:
                        return redirect('process')
                    return redirect('config')
        return render(request,"Config.html",context)
    except Exception as e:
        messages.error(request,"Error:{}".format(e))
        return redirect('process') 

@csrf_exempt
def base_post(request):
    try:
        active=manager.get_active()
        if request.method == "POST":
            if 'BtnActDesact' in request.POST:
                    if active:
                        manager.desactivate()
                        return redirect('config')
                    else:    
                        manager.activate()
                        return redirect('process')
                    #return HttpResponse("OK_D" if active == True else "OK_A")
            elif request.headers.get('X-Requested-With') == 'XMLHttpRequest': 
                data = json.load(request)
                if 'GetData' in data:
                    if active == False:
                        return JsonResponse({'NoActive':True})
                    level=manager.get_level()
                    valve=manager.get_valve()
                    bomb=manager.get_bomb()
                    cistern=manager.get_cistern()
                    return JsonResponse({"level":level,"cistern":cistern,"valve":valve,"bomb":bomb})
                elif "IncDecBomb" in data:
                    incdec=bool(data.get("IncDecBomb"))
                    manager.incdec_bomb(incdec)
                elif "IncDecValve" in data:
                    incdec=bool(data.get("IncDecValve"))
                    manager.incdec_valve(incdec)
        
    except:
        pass
    return redirect('process')
    #return render(request,"Home.html",{'active':active}) 

