import threading
import random
import time
class MySensor():
    def __init__(self):
        self._look=threading.Lock()
        self._data=0
        self._active=False
        self._look_read_data=False
        
    def __del__(self):
        print("__del__")
        self.desactivate()
    
    def activate(self):
        if self.get_active()==True:
            self.desactivate()
        with self._look:
            self._active=True
            self._thread=threading.Thread(target=self.loop)
            self._thread.start()
    
    def desactivate(self):
        if self.get_active() == True:
            with self._look:
                self._active=False
            self._thread.join()
        
    def loop(self):
        with self._look:
            if self._look_read_data == True:
                return
            self._look_read_data = True
        
        while(True):
            with self._look:    
                self._data=random.randint(0,100)
                if self._active == False:
                    break
            
            time.sleep(1)
            
            
            
        self._look_read_data = False
    
    def get_data(self):  
        with self._look:
            return self._data if self._active else None
    
    def get_active(self):  
        with self._look:
            return self._active             
    
        