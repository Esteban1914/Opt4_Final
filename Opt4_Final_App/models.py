#from django.db import models
import threading
import time
from simple_pid import PID

MAX_LEVEL=1
MAX_CISTERN=1
MIN_CISTERN=0
DELAYTIME=1
INCDEC=5
MAXMINBOMB=(0,100)
MAXMINVAVLE=(0,30)
class Manager():
    def __init__(self):
        self.__look=threading.Lock()
        self.__level=0
        self.__valve=0
        self.__bomb=0
        self.__cistern=0
        self.__active=False
        self.__look_loop=False
        self.__mode=0
        self.__error=None
        self.__bomb_pid=PID(1, 0.1, 0.05)
        self.__bomb_pid.output_limits=MAXMINBOMB
        self.__bomb_pid.sample_time = DELAYTIME
        self.__valve_pid=PID(1, 0.1, 0.05)
        self.__valve_pid.output_limits=MAXMINVAVLE
        self.__valve_pid.sample_time = DELAYTIME
        self.set_setpoint(0.5)
        
    def __del__(self):
        self.desactivate()
    
    def loop(self):
        
        def _round(data,dec):
            data=round(data,dec)
            pow_10_dec=pow(10,dec)
            data*=pow_10_dec
            data=int(data)
            data/=pow_10_dec
            return data
        def __error_limits():
            with self.__look:
                error=False
                if self.__level > MAX_LEVEL:
                    self.off_bomb()
                    self.__error="Nivel al Máximo , Bomba Detenida"
                    error=True
                if self.__cistern > MAX_CISTERN:
                    self.off_valve()
                    self.__error="Cisterna al Máximo , Válvula Cerrada"
                    error=True
                if self.__cistern < MIN_CISTERN:
                    self.__error="Cisterna al Mínimo; Bomba Detenida"
                    self.off_bomb()
                    error=True
                return error
        with self.__look:
            if self.__look_loop == True:
                return
            self.__look_loop = True
        desactivate=False
        while(True):
            if not __error_limits():
                with self.__look:
                    
                    self.__level=0 #Read From Level Sensor
                    
                    #Modo Manual
                    if self.__mode == 0: 
                        pass
                    #Modo PID Entrada Controlada
                    elif self.__mode == 1:
                        self.__bomb= _round(self.__bomb_pid(self.__level),3)
                           
                    #Modo PID Salida Controlada
                    elif self.__mode == 2:
                        self.__valve=_round(self.__valve_pid(self.__level),3)
                    #Modo PID Control Paralelo
                    elif self.__mode == 3:
                        self.__bomb= _round(self.__bomb_pid(self.__level),3)
                        self.__valve=_round(self.__valve_pid(self.__level),3)
                        pass
                    else:
                        break
                    
                    if self.__active == False:
                        break
                
            time.sleep(DELAYTIME)
            
        
        self.desactivate()
            
        self.__look_loop = False
     
    def activate(self):
        if self.get_active()==True:
            self.desactivate()
        with self.__look:
            self.__active=True
            self.__thread=threading.Thread(target=self.loop)
            self.__thread.start()
    
    def desactivate(self):
        if self.get_active() == True:
            self.off_bomb()
            self.off_valve()
            with self.__look:
                self.__active=False
            self.__thread.join()
    
    def set_mode(self,mode):
        self.off_bomb()
        self.off_valve()
        try:
            with self.__look:    
                mode=int(mode)
                self.__mode=mode
                return
        except:
            pass
        self.desactivate()      
    
    def incdec_bomb(self,incdec):
        with self.__look:
            if incdec:
                self.__bomb+=INCDEC
                if self.__bomb > MAXMINBOMB[1]:
                    self.__bomb=MAXMINBOMB[1]
            else:
                self.__bomb-=INCDEC
                if self.__bomb < MAXMINBOMB[0]:
                    self.__bomb=MAXMINBOMB[0]
    
    def incdec_valve(self,incdec):
        with self.__look:
            if incdec:
                self.__valve+=INCDEC
                if self.__valve > MAXMINVAVLE[1]:
                    self.__valve=MAXMINVAVLE[1]
            else:
                self.__valve-=INCDEC
                if self.__valve < MAXMINVAVLE[0]:
                    self.__valve=MAXMINVAVLE[0]
    
    def set_valve(self,value):  
        with self.__look:
            self.__valve=int(value) 
    
    def set_bomb(self,value):  
        with self.__look:
            self.__bomb=int(value) 
     
    def set_setpoint(self,setpoint):
        with self.__look:
            self.__set_point=setpoint
            self.__valve_pid.setpoint=setpoint
            self.__bomb_pid.setpoint=setpoint
                
    def off_bomb(self):
        with self.__look:
            #self.off_bomb_NL()
            self.__bomb=0
        
    def off_valve(self):
        with self.__look:
            self.__valve=0

    def get__data(self):
        with self.__look:
            if self.__active:
                return self.__level,self.__cistern,self.__bomb,self.__valve,self.__error
            return None
    
    def get_set_point(self):
        with self.__look:
            return self.__set_point
    
    def get_level(self):  
        with self.__look: 
            return self.__level if self.__active else None
    
    def get_valve(self):  
        with self.__look:
            
            return self.__valve if self.__active else None
    
    def get_bomb(self):  
        with self.__look:
            return self.__bomb if self.__active else None
    
    def get_cistern(self):  
        with self.__look:
            return self.__cistern if self.__active else None
    
    def get_active(self):  
        with self.__look:
            return self.__active 

    def get_mode(self):
        return self.__mode
    