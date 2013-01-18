from arduino import Arduino
import time
import cherrypy
import threading
THRESHOLD = 3
serialLocked = False
def serialLock():
    global serialLocked
    while(serialLocked == True):
        time.sleep(0.01)
    serialLocked = True
def serialUnlock():
    global serialLocked
    serialLocked = False

#Switches with amp meters (eg, lightswitches, fans, powerpoints)
class powerSwitch:
    def __init__(self, pinNumber, description="", analogPin=-1):
        serialLock()
        self.pinNumber = pinNumber
        self.description = description
        self.analogPin = analogPin
        self.state = False
        board.setLow(pinNumber)
        board.analogWrite(self.pinNumber,0)
        #time.sleep(0.1)
        if (analogPin == -1):
            self.analogPin = pinNumber-22
        board.output([pinNumber])
        serialUnlock()
    def toggle(self):
        serialLock()
        if (self.state == True):
            self.state = False
            board.setLow(self.pinNumber)
            #board.analogWrite(self.pinNumber,255) #need to analogWrite for some reason with this lib on PWM ports
        else:
            self.state = True
            board.setHigh(self.pinNumber)
            #board.analogWrite(self.pinNumber,0)
        serialUnlock()
    def off(self):
        serialLock()
        if (int(board.analogRead(self.analogPin)) >= THRESHOLD):
            serialUnlock()
            self.toggle()
        serialUnlock()
    def on(self):
        serialLock()
        if (int(board.analogRead(self.analogPin)) <= THRESHOLD):
            serialUnlock()
            self.toggle()
        serialUnlock()
    def isOn(self):
        serialLock()
        time.sleep(0.05) #slow down comms to serial // possibly test removing latter
        if (int(board.analogRead(self.analogPin)) <= THRESHOLD):
            serialUnlock()
            return False
        else:
            serialUnlock()
            return True


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
    def checkSwitch(self, loop=False):
        while True:
            serialLock()
            currentState = board.getState(self.unlockSwitchPin)
            serialUnlock()
            if currentState != self.lastState:
                if self.debounceCheck == True:
                    self.doorUnlock()
                    self.lastState = currentState
                    self.debounceCheck = False
                else:
                    self.debounceCheck = True
            else:
                time.sleep(0.1)
            if loop==False:
                break
    def doorUnlock(self,timeout=3):
        serialLock()
        board.setHigh(self.latchPin)
        board.analogWrite(self.latchPin,255)
        serialUnlock()
        time.sleep(timeout)
        serialLock()
        board.setLow(self.latchPin)
        board.analogWrite(self.latchPin,0)
        serialUnLock()

class webMappings(object):
    def index(self):
        return "Hello World!"
    def on(self, switchId):
        switches[int(switchId)].on()
        return "On"
    def off(self, switchId):
        switches[int(switchId)].off()
        return "Off"
    def unlock(self, timer=20):
        frontDoor.doorUnlock(timer)
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
        cherrypy.quickstart(webMappings())
        
class checkDoor(threading.Thread):
    def run(self):
        frontDoor.checkSwitch(loop=True)


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
