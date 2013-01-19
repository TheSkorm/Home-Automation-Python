from arduino import Arduino
import time
import cherrypy
import threading
import sys
from cherrypy.lib.static import serve_file 

STATICPATH = 'C:\\Users\\Michael\\Documents\\Home-Automation-Python\static'
THRESHOLD = 3
CACHETIME = 0.5 #amount of time in seconds to cache analogs
serialMutex = threading.Lock()
config = {'/': {'tools.staticdir.on': True, 'tools.staticdir.dir':STATICPATH}}
cherrypy.config.update({'server.socket_host': '0.0.0.0','server.socket_port': 8080})

#Switches with amp meters (eg, lightswitches, fans, powerpoints)
class powerSwitch:
    def __init__(self, pinNumber, description="", analogPin=-1):
        serialMutex.acquire()
        self.pinNumber = pinNumber
        self.description = description
        self.analogPin = analogPin
        self.state = False
        board.output([pinNumber])
        board.analogWrite(self.pinNumber,0)
        board.setLow(pinNumber)
        #time.sleep(0.1)
        if (analogPin == -1):
            self.analogPin = pinNumber-22
            
        if (int(board.analogRead(self.analogPin)) <= THRESHOLD):
            self.isOnCache = False
        else:
            self.isOnCache = True
        self.isOnCacheTimeout = time.time() + CACHETIME
        serialMutex.release()
    def toggle(self):
        serialMutex.acquire()
        if (self.state == True):
            self.state = False
            board.setLow(self.pinNumber)
            #board.analogWrite(self.pinNumber,255) #need to analogWrite for some reason with this lib on PWM ports
        else:
            self.state = True
            board.setHigh(self.pinNumber)
            #board.analogWrite(self.pinNumber,0)
        serialMutex.release()
    def off(self):
        if (self.isOn(checkCache=False)):
            self.toggle()
    def on(self):
        if (not self.isOn(checkCache=False)):
            self.toggle()
    def isOn(self, checkCache=True):
        if (time.time() < self.isOnCacheTimeout) and checkCache: #use cache if it's fresh and we are allowed
            print "cache hit"
            return self.isOnCache
        elif(serialMutex.acquire(False)): #check if we can refresh the cache without blocking
            if (int(board.analogRead(self.analogPin)) <= THRESHOLD):
                 self.isOnCache = False
            else:
                 self.isOnCache = True
            serialMutex.release()
            self.isOnCacheTimeout = time.time() + CACHETIME
            return self.isOnCache
        elif(checkCache==False):         #if we can't check without blocking and we need fresh data, block
            serialMutex.acquire()
            if (int(board.analogRead(self.analogPin)) <= THRESHOLD):
                 self.isOnCache = False
            else:
                 self.isOnCache = True
            serialMutex.release()
            self.isOnCacheTimeout = time.time() + CACHETIME
            return self.isOnCache            
        else:                              #else just send the cached data.
            print "Blocked request, sending cache"
            return self.isOnCache


#doors that have an unlock switch
class door:
    def __init__(self, unlockSwitchPin, latchPin):
        self.unlockSwitchPin = unlockSwitchPin
        self.latchPin = latchPin
        board.output([latchPin])
        board.setLow(self.latchPin)
        board.analogWrite(self.latchPin,0)
        self.lastState = board.getState(unlockSwitchPin)
        self.debounceCheck = False
        self.breakLoop = 0
    def checkSwitch(self, loop=False):
        while True:
            serialMutex.acquire()
            currentState = board.getState(self.unlockSwitchPin)
            serialMutex.release()
            if currentState != self.lastState:
                if self.debounceCheck == True:
                    self.doorUnlock()
                    self.lastState = currentState
                    self.debounceCheck = False
                else:
                    self.debounceCheck = True
            else:
                time.sleep(0.1)
            if self.breakLoop == 1:
                self.breakLoop = 0
                break
            if loop==False:
                break
    def doorUnlock(self,timeout=3):
        serialMutex.acquire()
        board.setHigh(self.latchPin)
        board.analogWrite(self.latchPin,255)
        serialMutex.release()
        time.sleep(float(timeout))
        serialMutex.acquire()
        board.setLow(self.latchPin)
        board.analogWrite(self.latchPin,0)
        serialMutex.release()

class webMappings(object):
    def index(self):
        return serve_file(STATICPATH + "/index.html") 
    def on(self, switchId):
        switches[int(switchId)].on()
        return "On"
    def off(self, switchId):
        switches[int(switchId)].off()
        return "Off"
    def unlock(self, timer=20):
        t = threading.Thread(target=frontDoor.doorUnlock, args=(timer,))
        t.start()
        return "Unlocked"
    def status(self):
        y = 0
        page = ""
        for switch in switches:
            print "Checking - " + str(y) + " - " + switch.description
            if switch.isOn():
                page = page + str(y) + " - " + switch.description + " - On\n"
            else:
                page = page + str(y) + " - " + switch.description + " - Off\n"
            y = y + 1
        return page
    on.exposed = True
    off.exposed = True
    unlock.exposed = True
    status.exposed = True
    index.exposed = True

class webServer(threading.Thread):
    def run(self):
        cherrypy.quickstart(webMappings(),'/',config=config)
        
class checkDoor(threading.Thread):
    def run(self):
        frontDoor.checkSwitch(loop=True)



def exit():
    cherrypy.engine.exit()
    frontDoor.breakLoop = 1
    sys.exit("Killed by user")
	

board = Arduino('COM3')

switches = [
powerSwitch(22,"Front Light"),
powerSwitch(23,"Kitchen Light"),
powerSwitch(24,"Dinning Room Light"),
powerSwitch(25,"Lounge Room 1 Light"),
powerSwitch(26,"Lounge Room 2 Light"),
powerSwitch(27,"Bedroom 1 Light"),
powerSwitch(28,"Bedroom 1 Fan"),
powerSwitch(29,"Bedroom 2 Light"),
powerSwitch(30,"Bedroom 2 Fan"),
powerSwitch(31,"Bedroom 3 Light"),
powerSwitch(32,"Bedroom 3 Fan"),
powerSwitch(33,"Hallway"),
powerSwitch(34,"Outside 1 Light"),
powerSwitch(35,"Outside 2 Light"),
]

frontDoor = door(47,46)

t = webServer()
t.start()
t = checkDoor()
t.start()

while(1):
	command = raw_input("> ")
	if command == "exit":
		exit()
