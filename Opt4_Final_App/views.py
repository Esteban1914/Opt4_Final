from django.shortcuts import render,redirect
from django.http import HttpResponse,HttpResponseBadRequest,JsonResponse
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate,login,logout
from .models import Manager
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json


manager=Manager()

MODE={
    0:"Manual",
    1:"PID Entrada Controlada",
    2:"PID Salida Controlada",
}

def redirect_process(request):
    return redirect('process')

def process(request):
    if not request.user.is_authenticated:
        return redirect("login_post")
        
    context={'active':manager.get_active(),"set_point":manager.get_set_point(),'mode':manager.get_mode(),"modeStr":MODE.get(manager.get_mode())}
    return render(request,"Process.html",context) 

def config(request):
    if not request.user.is_authenticated:
        return redirect("login_post")
    try:
        context={}
        active=manager.get_active()
        mode=manager.get_mode()
        set_point=manager.get_set_point()
        context.update({'active':active,'mode':mode,"set_point":set_point,"modeStr":MODE.get(mode)})
        if request.method=="POST":
            if "SetConfg" in request.POST:
                form=request.POST.dict()
                form_mode=int(form.get("group"))
                form_set_point=float(form.get("SetPoint"))
                
                if form_mode or form_mode == 0: 
                    if form_mode != mode:
                        manager.set_mode(form_mode)
                        context.update({"modeStr":MODE.get(manager.get_mode())})
                    if form_set_point != set_point:
                        manager.set_setpoint(form_set_point)
                        context.update({"set_point":manager.get_set_point()})
                    if active:
                        return redirect('process')
                    return redirect('config')
        return render(request,"Config.html",context)
    except Exception as e:
        messages.error(request,"Error:{}".format(e))
        return redirect('process') 

def login_post(request):
    if request.method=="POST":
        if "Inicar_Sesion" in request.POST:
            formlogin=AuthenticationForm(request,data=request.POST)
            if formlogin.is_valid():
                nombre=formlogin.cleaned_data.get("username")
                contra=formlogin.cleaned_data.get("password")
                
                usuario=authenticate(username=nombre,password=contra)
                if usuario is not None:
                    login(request,usuario)
                    messages.success(request ,"{} Conectado".format(nombre))    
                    return redirect('process')
            
        elif "CerrarSesion" in request.POST:
            user=request.user.username
            logout(request)
            messages.success(request,"{} desconectado".format(request.user))    
    if request.user.is_authenticated:
        return redirect("process")
    
    return render(request,"Login.html")

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
                    error=manager.get_error()
                    return JsonResponse({"level":level,"cistern":cistern,"valve":valve,"bomb":bomb,"error":error})
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

