from arduino import Arduino
import time
import cherrypy
import threading
import sys
from cherrypy.lib.static import serve_file

STATICPATH = '/root/Home-Automation-Python/static'
serialMutex = threading.Lock()
config = {'/': {'tools.staticdir.on': True, 'tools.staticdir.dir':STATICPATH}}
cherrypy.config.update({'server.socket_host': '0.0.0.0','server.socket_port': 8080})

#Switches with amp meters (eg, lightswitches, fans, powerpoints)
class powerSwitch:
    def __init__(self, pinNumber, description="", analogPin=-1, threshold=0.02):
        serialMutex.acquire()
        self.pinNumber = pinNumber
        self.description = description
        self.analogPin = analogPin
        self.state = False
        self.cachedState = -1  #set the cached state to -1, unlike state, cachedstate is the analog reading
        self.threshold = threshold
        board.output([pinNumber])
        board.analogWrite(self.pinNumber,0)
        board.setLow(pinNumber)
        if (analogPin == -1):
            self.analogPin = pinNumber-22
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
        if (self.isOn()):
            self.cachedState = -1
            self.toggle()
    def on(self):
        if (not self.isOn()):
            self.cachedState = -1
            self.toggle()
    def isOn(self):
            serialMutex.acquire()
            print str(self.analogPin) + " - " + str(float(board.analogRead(self.analogPin)) )
            if (float(board.analogRead(self.analogPin)) > self.threshold):
                 serialMutex.release()
                 return True
            else:
                 serialMutex.release()
                 return False
    def cachedRead(self):
        if self.cachedState != -1:
             return self.cachedState
        else:
             self.cachedState = self.isOn()
    def updateCache(self):
        self.cachedState = self.isOn()


#doors that have an unlock switch
class door:
    def __init__(self, unlockSwitchPin, latchPin):
        self.unlockSwitchPin = unlockSwitchPin
        self.latchPin = latchPin
        serialMutex.acquire()
        board.output([latchPin])
        board.setLow(self.latchPin)
        board.analogWrite(self.latchPin,0)
        self.lastState = board.getState(unlockSwitchPin)
        serialMutex.release()
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
                time.sleep(0.2)
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
    def on(self, switchId, NOCACHE=False):
        switches[int(switchId)].on()
        return "On"
    def off(self, switchId, NOCACHE=False):
        switches[int(switchId)].off()
        return "Off"
    def unlock(self, timer=20, NOCACHE=False):
        t = threading.Thread(target=frontDoor.doorUnlock, args=(timer,))
        t.start()
        return "Unlocked"
    def status(self, NOCACHE=False):
        y = 0
        page = "{\"description\": {"
        for switch in switches:
            if y != 0:
                page = page + ",\n"
            page = page + "\"" + str(y) + "\"" + " : \"" + switch.description + "\""
            y = y + 1
        page = page + "},\"state\": {"
        y = 0
        for switch in switches:
            if y != 0:
                page = page + ",\n"
            if switch.cachedRead():
                page = page + "\"" + str(y) + "\"" + " : 1"
            else:
                page = page + "\"" + str(y) + "\"" + " : 0"
            y = y + 1
        page = page + "}}"
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

class updateSwitchCache(threading.Thread):
    def run(self):
        self.breakLoop = 0
        while self.breakLoop == 0:
           time.sleep(0.3)
           print "Updating switch cache"
           for switch in switches:
               switch.updateCache()

def exit():
    cherrypy.engine.exit()
    frontDoor.breakLoop = 1
    t0.breakLoop = 1
    sys.exit("Killed by user")


board = Arduino('/dev/ttyUSB0')
#switches = [
#powerSwitch(22,"Front Light"),
#powerSwitch(23,"Kitchen Light"),
#powerSwitch(24,"Dinning Room Light"),
#powerSwitch(25,"Lounge Room 1 Light"),
#powerSwitch(26,"Lounge Room 2 Light"),
#powerSwitch(27,"Bedroom 1 Light"),
#powerSwitch(28,"Bedroom 1 Fan"),
#powerSwitch(29,"Bedroom 2 Light"),
#powerSwitch(30,"Bedroom 2 Fan"),
#powerSwitch(31,"Bedroom 3 Light"),
#powerSwitch(32,"Bedroom 3 Fan"),
#powerSwitch(33,"Hallway"),
#powerSwitch(34,"Outside 1 Light"),
#powerSwitch(35,"Outside 2 Light"),
#]

switches = [
powerSwitch(22,"Front Light"),
powerSwitch(23,"Kitchen Light"),
powerSwitch(24,"Dinning Room Light"),
powerSwitch(26,"Lounge Room 1 Light"),
powerSwitch(25,"Lounge Room 2 Light"),
powerSwitch(27,"Lounge Room Fan"),
powerSwitch(28,"Bedroom 1 Light"),
powerSwitch(32,"Bedroom 1 Fan"),
powerSwitch(29,"Bedroom 2 Light"),
powerSwitch(31,"Bedroom 2 Fan"),
powerSwitch(30,"Bedroom 3 Light")
]


frontDoor = door(43,45)

t = webServer()
t.start()
t = checkDoor()
t.start()
t0 = updateSwitchCache()
t0.start()

while(1):
        command = raw_input("> ")
        if command == "exit":
                exit()

