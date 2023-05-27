#from django.db import models
import threading
import time
import smbus2 as smbus
import time
from simple_pid import PID 
import RPi.GPIO as GPIO
from gpiozero import MCP3008


GPIO.setmode(GPIO.BCM)

"""    =============POT=============   """
pot=MCP3008(channel=0)

"""    =============BOMB=============   """
GPIO.setup(19,GPIO.OUT)
GPIO.output(19,GPIO.HIGH)
GPIO.setup(13,GPIO.OUT)

"""    =============SERVO=============   """
GPIO.setup(12,GPIO.OUT)

"""    =============LCD=============   """
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
# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

"""  =============UltraSonic Sensor =============  """
#set GPIO Pins
GPIO_TRIGGER = 5
GPIO_ECHO = 6
#set GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

def get_ultra_distance():
    # set Trigger to HIGH
    GPIO.output(GPIO_TRIGGER, True)
    #set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)

    StartTime = time.time()
    StopTime = time.time()

    # save StartTime
    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()

    # save time of arrival
    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()

    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2

    return distance

"""  =============Internal=============  """
MAX_LEVEL=100
MAX_CISTERN=100
MIN_CISTERN=0
DELAYTIME=1
INCDEC=1
MAXMINBOMB=(0,100)
MAXMINVAVLE=(0,100)

class Manager():
    def __init__(self):
        self.__look=threading.Lock()
        self.__lcd=Lcd_DJ()
        self.__servo=GPIO.PWM(12,50)
        self.__servo.start(0)
        self.__servo.ChangeDutyCycle(0)
        self.__pwm_bomb=GPIO.PWM(13,50)
        self.__pwm_bomb.start(0)
        self.__pwm_bomb.ChangeDutyCycle(0)
        self.__level=0
        self.__valve=0
        self.__bomb=0
        self.__cistern=0
        self.__active=True
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
            #return False
            with self.__look:
                self.__error=False
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
        while(True):
            if not __error_limits():
                with self.__look:
                    try:
                        self.__level=_round(get_ultra_distance(),4) #Read From Level Sensor
                        #print(self.__level)
                        self.__cistern=_round(pot.value,4)
                        #print(self.__cistern)
                        try:
                            self.__lcd.print_all(self.__active,self.__mode,self.__level,self.__cistern,self.__bomb,self.__valve,self.__set_point)
                        except:
                            print("Error , no lcd connected")
                    except Exception as e :
                        print("Error:",e)
                        break
                    #Modo Manual
                    if self.__mode == 0: 
                        pass
                    #Modo PID Entrada Controlada
                    elif self.__mode == 1:
                        self.set_bomb(_round(self.__bomb_pid(self.__level),3))
                           
                    #Modo PID Salida Controlada
                    elif self.__mode == 2:
                        self.set_valve(_round(self.__valve_pid(self.__level),3))
    
                    else:
                        break
                    
                    #if self.__active == False:
                    #    break
                    
                
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
                self.set_bomb(self.__bomb+INCDEC+4)
                if self.__bomb > MAXMINBOMB[1]:
                    self.set_bomb(MAXMINBOMB[1])
            else:
                self.set_bomb(self.__bomb-INCDEC-4)
                if self.__bomb < MAXMINBOMB[0]:
                    self.set_bomb(MAXMINBOMB[0])
    
    def incdec_valve(self,incdec):
        with self.__look:
            if incdec:

                #self.__valve+=INCDEC
                self.set_valve(self.__valve+INCDEC)
                if self.__valve > MAXMINVAVLE[1]:
                    self.set_valve(MAXMINVAVLE[1])
                    #self.__valve=MAXMINVAVLE[1]
            else:
                #self.__valve-=INCDEC
                self.set_valve(self.__valve-INCDEC)
                if self.__valve < MAXMINVAVLE[0]:
                    self.set_valve(MAXMINVAVLE[0])
                    #self.__valve=MAXMINVAVLE[0]
    
    def set_valve(self,value):  
        self.__valve=int(value) 
        self.__servo.ChangeDutyCycle(self.__valve)
        
    def set_bomb(self,value):  
        self.__bomb=int(value) 
        self.__pwm_bomb.ChangeDutyCycle(self.__bomb)
    
    def set_setpoint(self,setpoint):
        with self.__look:
            self.__set_point=setpoint
            self.__valve_pid.setpoint=setpoint
            self.__bomb_pid.setpoint=setpoint
                
    def off_bomb(self):
        with self.__look:
            self.set_bomb(0)
        
    def off_valve(self):
        with self.__look:
            self.set_valve(0)

    def get_error(self):
        with self.__look:
            return self.__error
    
    def get_set_point(self):
        with self.__look:
            return self.__set_point
    
    def get_level(self):  
        with self.__look: 
            return self.__level 
    
    def get_valve(self):  
        with self.__look:
            
            return self.__valve
    
    def get_bomb(self):  
        with self.__look:
            return self.__bomb
    
    def get_cistern(self):  
        with self.__look:
            return self.__cistern
    
    def get_active(self):  
        with self.__look:
            return self.__active 

    def get_mode(self):
        return self.__mode


class Lcd_DJ():
    def __init__(self):
        # Open I2C interface
        # bus = smbus.SMBus(0)  # Rev 1 Pi uses 0
        self.bus = smbus.SMBus(1)    # Rev 2 Pi uses 1
        try:

            self.lcd_string("        Hello", LCD_LINE_1)
            self.lcd_string("       People_", LCD_LINE_2)
            self.lcd_string("         Opt", LCD_LINE_3)
            self.lcd_string("         PDH", LCD_LINE_4)
            time.sleep(2)
        except:
            print("Error , no lcd connected")
    
    def lcd_init(self):
        # Initialise display
        self.lcd_byte(0x33, LCD_CMD)     # 110011 Initialise
        self.lcd_byte(0x32, LCD_CMD)     # 110010 Initialise
        self.lcd_byte(0x06, LCD_CMD)     # 000110 Cursor move direction
        self.lcd_byte(0x0C, LCD_CMD)     # 001100 Display On,Cursor Off, Blink Off
        self.lcd_byte(0x28, LCD_CMD)     # 101000 Data length, number of lines, font size
        self.lcd_byte(0x01, LCD_CMD)     # 000001 Clear display
        time.sleep(E_DELAY)

    def lcd_byte(self,bits, mode):
        # Send byte to data pins
        # bits = the data
        # mode = 1 for data
        #        0 for command

        bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
        bits_low = mode | ((bits << 4) & 0xF0) | LCD_BACKLIGHT

        # High bits
        self.bus.write_byte(I2C_ADDR, bits_high)
        self.lcd_toggle_enable(bits_high)

        # Low bits
        self.bus.write_byte(I2C_ADDR, bits_low)
        self.lcd_toggle_enable(bits_low)

    def lcd_toggle_enable(self,bits):
        # Toggle enable
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
        #s=s[:9]+"B:{}".format(bomb)
        self.lcd_string(s,LCD_LINE_3)

        s="{}                    ".format(
            "SP:{}".format(setpoint),
        )
        s=s[:9]+"V:{}".format(valve)
        self.lcd_string(s,LCD_LINE_4)

    def lcd_string(self,message, line):
        # Send string to display
        message = message.ljust(LCD_WIDTH, " ")

        self.lcd_byte(line, LCD_CMD)

        for i in range(LCD_WIDTH):
            self.lcd_byte(ord(message[i]), LCD_CHR)

