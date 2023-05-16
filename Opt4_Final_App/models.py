from django.db import models
import threading
import random
import time
from simple_pid import PID
import math

MAX_LEVEL=1
DELAYTIME=1
class Manager():
    def __init__(self):
        self._look=threading.Lock()
        self._level=0
        self._valve=0
        self._bomb=0
        self._active=False
        self._look_loop=False
        self._mode=0
        self._on_off=False
        self.set_valve_pid(1, 0.1, 0.05,1)
        self.set_bomb_pid(1, 0.1, 0.05,1)
        
    def __del__(self):
        self.desactivate()
    
    def loop(self):
        with self._look:
            if self._look_loop == True:
                return
            self._look_loop = True
        while(True):
            with self._look:
                self._level=0 #Read From Level Sensor
                
                if self._mode == 0:
                    if self._level > MAX_LEVEL:
                        self.off_bomb_NL()   
                  
                elif self._mode == 1:
                    self._bomb+=self._bomb_pid(self._level)
                    self._valve+=self._valve_pid(self._level)    
                
                if self._active == False:
                    break
            
            time.sleep(DELAYTIME)
        self._look_loop = False
    
    
    def activate(self):
        if self.get_active()==True:
            self.desactivate()
        with self._look:
            self._active=True
            self._thread=threading.Thread(target=self.loop)
            self._thread.start()
    
    def desactivate(self):
        if self.get_active() == True:
            self.off_bomb()
            self.off_valve()
            with self._look:
                self._active=False
            self._thread.join()
    
    def set_mode(self,mode):
        self.off_bomb()
        self.off_valve()
        try:
            with self._look:    
                mode=int(mode)
                if mode == 0 or mode == 1:
                    self._mode=mode
                    return
        except:
            pass
        self.desactivate()      
    
    def set_valve_pid(self,kp,ki,kd,setpoint,output_limits=None):
        with self._look:
            self._valve_pid=PID(kp,ki,kd,setpoint)
            self._valve_pid.sample_time = DELAYTIME
            if output_limits:
                self._valve_pid.output_limits=output_limits
                
    def set_bomb_pid(self,kp,ki,kd,setpoint,output_limits=None):
        with self._look:
            self._bomb_pid=PID(kp,ki,kd,setpoint)
            self._bomb_pid.sample_time = DELAYTIME
            if output_limits:
                self._bomb_pid.output_limits=output_limits
                
    def off_bomb(self):
        with self._look:
            self._bomb=0
    
    def off_bomb_NL(self):
        self._bomb=0
        
    def off_valve(self):
        with self._look:
            self._valve=0
    
    
    def get_level(self):  
        with self._look: 
            return self._level if self._active else None
    
    def get_valve(self):  
        with self._look:
            
            return self._valve if self._active else None
    
    def get_bomb(self):  
        with self._look:
            return self._bomb if self._active else None
    
    def get_active(self):  
        with self._look:
            return self._active 

    def get_mode(self):
        return self._mode
    