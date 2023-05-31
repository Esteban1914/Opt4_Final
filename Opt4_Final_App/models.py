
from django.db import models
import threading
import time
import smbus2 as smbus
import time
from simple_pid import PID 
import RPi.GPIO as GPIO
from gpiozero import MCP3008



""" ===== GPIO ===== """
GPIO.setmode(GPIO.BCM)
GPIO_H_BOMB=19
GPIO_BOMB=13
GPIO_SERVO=12
GPIO_TRIGGER = 5
GPIO_ECHO = 6
GPIO.setup(GPIO_H_BOMB,GPIO.OUT)
GPIO.setup(GPIO_BOMB,GPIO.OUT)
GPIO.setup(GPIO_SERVO,GPIO.OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

GPIO.output(GPIO_H_BOMB,GPIO.HIGH)

""" ===== LCD ===== """
I2C_ADDR = 0x27     # I2C device address, if any error, change this address to 0x3f
LCD_WIDTH = 20      # Maximum characters per line
LCD_CHR = 1     # Mode - Sending data
LCD_CMD = 0     # Mode - Sending command
LCD_LINE_1 = 0x80   # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0   # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94   # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4   # LCD RAM address for the 4th line
LCD_BACKLIGHT = 0x08  # On
ENABLE = 0b00000100     # Enable bit
E_PULSE = 0.0005
E_DELAY = 0.0005

""" ===== Internal ===== """
MAX_LEVEL=12
MAX_CISTERN=90#0.07
MIN_CISTERN=30#0.04
""" 
m=(Y2-Y1)/(X2-X1)
m=(100-0)/(0.07-0.04)
m=3333.33
y=mx+n
0=3333.33*0.04+n
n=-133.33
y=3333.33x-133.33
"""
DELAYTIME=1
MAXMINBOMB=(0,100)
MAXMINVALVE=(5,10)
INCDECBOMB=10
INCDECVALVE=1


class Manager():
    
    def __init__(self):
        self.__look=threading.Lock()
        self.__servo=GPIO.PWM(GPIO_SERVO,50)
        self.__servo.start(0)
        self.__servo.ChangeDutyCycle(0)
        self.__pwm_bomb=GPIO.PWM(GPIO_BOMB,50)
        self.__pwm_bomb.start(0)
        self.__pwm_bomb.ChangeDutyCycle(0)
        self.__pot=MCP3008(channel=0)
        self.__lcd=Lcd_DJ()
        self.__level=0
        self.__valve=MAXMINVALVE[0]
        self.__bomb=MAXMINBOMB[0]
        self.__cistern=MIN_CISTERN
        self.__active=False
        self.__look_loop=False
        self.__mode=0
        self.__error=None
        self.__bomb_pid=PID(10, 0.1, 0.05)
        self.__bomb_pid.output_limits=MAXMINBOMB
        self.__bomb_pid.sample_time = DELAYTIME
        self.__valve_pid=PID(-15, -0.25, -0.5)
        self.__valve_pid.output_limits=MAXMINVALVE
        self.__valve_pid.sample_time = DELAYTIME
        self.set_setpoint(5)
        try:
            self.__lcd.print_all(self.__active,self.__mode,self.__level,self.__cistern,self.__bomb,self.__valve,self.__set_point)
        except:
            pass
        self.activate()
    
    def __del__(self):
        self.desactivate()
        self.__servo.stop()
        self.__pwm_bomb.stop()
        GPIO.cleanup()
        
    def loop(self):     
        
        def _round(data,dec):
            data=round(data,dec)
            pow_10_dec=pow(10,dec)
            data*=pow_10_dec
            data=int(data)
            data/=pow_10_dec
            return data
        
        def __error_limits():
            self.__error=""
            error=False
            if self.__level > MAX_LEVEL:
                #self.off_bomb()
                #self.__error+="Nivel al Máximo , Bomba Detenida;"
                self.__error+="Nivel al Máximo;"
                #error=True
            if self.__cistern > MAX_CISTERN:
                #self.off_valve()
                #self.__error+="Cisterna al Máximo , Válvula Cerrada;"
                self.__error+="Cisterna al Máximo;"
                #error=True
            if self.__cistern < MIN_CISTERN:
                #self.__error+="Cisterna al Mínimo; Bomba Detenida;"
                self.__error+="Cisterna al Mínimo;"
                #self.off_bomb()
                #error=True
            if self.__error == "":
                self.__error=None
            else:
                print(self.__error)
            return error
        
        def get_ultra_distance():
            GPIO.output(GPIO_TRIGGER, True)
            time.sleep(0.00001)
            GPIO.output(GPIO_TRIGGER, False)

            StartTime = time.time()
            StopTime = time.time()

            while GPIO.input(GPIO_ECHO) == 0:
                StartTime = time.time()

            while GPIO.input(GPIO_ECHO) == 1:
                StopTime = time.time()
                
            TimeElapsed = StopTime - StartTime
            distance = (TimeElapsed * 34300) / 2
            return distance
            
        with self.__look:
            if self.__look_loop == True:
                return
            self.__look_loop = True
            
        while(True):
            with self.__look:
                self.__level=_round(17.25-get_ultra_distance(),4) #Read From Level Sensor
                self.__cistern=_round(self.__pot.value*3333.33-133.33,4)
                try:
                    self.__lcd.print_all(self.__active,self.__mode,self.__level,self.__cistern,self.__bomb,self.__valve,self.__set_point)
                except:
                    print("Error , no lcd connected")
                if not __error_limits():
                    #Modo Manual
                    if self.__mode == 0: 
                        pass
                    #Modo PID Entrada Controlada
                    elif self.__mode == 1:
                        self.set_bomb(_round(self.__bomb_pid(self.__level),3))
                            
                    #Modo PID Salida Controlada
                    elif self.__mode == 2:
                        self.set_valve(_round(self.__valve_pid(self.__level),2))
                    else:
                        self.__mode=0
                
            if self.get_active() == False:
                break
                
            time.sleep(DELAYTIME)
            
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
        
    def incdec_bomb(self,incdec):
        with self.__look:
            if incdec:
                self.set_bomb(self.__bomb+INCDECBOMB)
            else:
                self.set_bomb(self.__bomb-INCDECBOMB)
                
    def incdec_valve(self,incdec):
        with self.__look:
            if incdec:
                self.set_valve(self.__valve+INCDECVALVE)
  
            else:
                self.set_valve(self.__valve-INCDECVALVE)
                
                    
    def set_mode(self,mode):
        self.off_bomb()
        self.off_valve()
        with self.__look:    
            mode=int(mode)
            self.__mode=mode
    
    def set_valve(self,value):  
        self.__valve=int(value) 
        if self.__valve > MAXMINVALVE[1]:
            self.__valve=MAXMINVALVE[1]
        if self.__valve < MAXMINVALVE[0]:
            self.__valve=MAXMINVALVE[0]
        self.__servo.ChangeDutyCycle(self.__valve)
        

    def set_bomb(self,value):  
        self.__bomb=int(value) 
        if self.__bomb > MAXMINBOMB[1]:
            self.__bomb=MAXMINBOMB[1]
        if self.__bomb < MAXMINBOMB[0]:
            self.__bomb=MAXMINBOMB[0]
        self.__pwm_bomb.ChangeDutyCycle(self.__bomb)
    
    def set_setpoint(self,setpoint):
        with self.__look:
            self.__set_point=setpoint
            self.__valve_pid.setpoint=setpoint
            self.__bomb_pid.setpoint=setpoint
                
    def off_bomb(self):
        self.set_bomb(0)
        
    def off_valve(self):
        self.set_valve(5)
        time.sleep(3)
        self.set_valve(0)

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
        with self.__look:
            return self.__mode

    def get_error(self):
        with self.__look:
            return self.__error

class Lcd_DJ():
    
    def __init__(self):
        #if Instance.objects.first().values()["instance"]==True:
        #    return
        self.bus = smbus.SMBus(1)
        try:
            self.lcd_init()
            self.lcd_string("        Hello", LCD_LINE_1)
            self.lcd_string("       People_", LCD_LINE_2)
            self.lcd_string("         Opt", LCD_LINE_3)
            self.lcd_string("         PDH", LCD_LINE_4)
            time.sleep(3)
        except:
            print("Error , no lcd connected")
            
    def __del__(self):
        try:
            self.lcd_init()
            self.lcd_string("          BYE", LCD_LINE_1)
            self.lcd_string("       People_", LCD_LINE_2)
            self.lcd_string("         Opt", LCD_LINE_3)
            self.lcd_string("         PDH", LCD_LINE_4)
            #time.sleep(3)
        except:
            print("Error , no lcd connected")

    def lcd_init(self):
        #Initialise display
        self.lcd_byte(0x33, LCD_CMD)     # 110011 Initialise
        self.lcd_byte(0x32, LCD_CMD)     # 110010 Initialise
        self.lcd_byte(0x06, LCD_CMD)     # 000110 Cursor move direction
        self.lcd_byte(0x0C, LCD_CMD)     # 001100 Display On,Cursor Off, Blink Off
        self.lcd_byte(0x28, LCD_CMD)     # 101000 Data length, number of lines, font size
        self.lcd_byte(0x01, LCD_CMD)     # 000001 Clear display
        time.sleep(E_DELAY)

    def lcd_byte(self,bits, mode):
        #Send byte to data pins
        #bits = the data
        #mode = 1 for data
        #       0 for command

        bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
        bits_low = mode | ((bits << 4) & 0xF0) | LCD_BACKLIGHT

        #High bits
        self.bus.write_byte(I2C_ADDR, bits_high)
        self.lcd_toggle_enable(bits_high)

        #Low bits
        self.bus.write_byte(I2C_ADDR, bits_low)
        self.lcd_toggle_enable(bits_low)

    def lcd_toggle_enable(self,bits):
        #Toggle enable
        time.sleep(E_DELAY)
        self.bus.write_byte(I2C_ADDR, (bits | ENABLE))
        time.sleep(E_PULSE)
        self.bus.write_byte(I2C_ADDR, (bits & ~ENABLE))
        time.sleep(E_DELAY)

    def print_all(self,active,mode,level,cistern,bomb,valve,setpoint):
        s="EAS_HDCA {}".format(
            
            "L:{}".format(level),
        )
        self.lcd_string(s,LCD_LINE_1)

        s="{}      {}".format(
            "A:{}".format("Y" if active else "N"),
            "C:{}".format(cistern),
        )
        self.lcd_string(s,LCD_LINE_2)

        s="{}      {}".format(
            "M:{}".format(mode),
            "B:{}".format(bomb),   
        )
        s=s[:9]+"B:{}".format(bomb)
        self.lcd_string(s,LCD_LINE_3)

        s="{}                    ".format(
            "SP:{}".format(setpoint),
        )
        s=s[:9]+"V:{}".format(valve)
        self.lcd_string(s,LCD_LINE_4)

    def lcd_string(self,message, line):
        #Send string to display
        message = message.ljust(LCD_WIDTH, " ")

        self.lcd_byte(line, LCD_CMD)

        for i in range(LCD_WIDTH):
            self.lcd_byte(ord(message[i]), LCD_CHR)

