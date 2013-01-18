from arduino import Arduino
import time

THRESHOLD = 3

#Switches with amp meters (eg, lightswitches, fans, powerpoints)
class powerSwitch:
    def __init__(self, pinNumber, description="", analogPin=-1):
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
    def toggle(self):
        if (self.state == True):
            self.state = False
            board.setLow(self.pinNumber)
            board.analogWrite(self.pinNumber,0) #need to analogWrite for some reason with this lib on PWM ports
        else:
            self.state = True
            board.setHigh(self.pinNumber)
            board.analogWrite(self.pinNumber,255)
    def off(self):
        if (int(board.analogRead(self.analogPin)) >= THRESHOLD):
            self.toggle()
    def on(self):
        if (int(board.analogRead(self.analogPin)) <= THRESHOLD):
            self.toggle()
    def isOn(self):
        if (int(board.analogRead(self.analogPin)) >= THRESHOLD):
            return False
        else:
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
            currentState = board.getState(self.unlockSwitchPin)
            if currentState != self.lastState:
                if self.debounceCheck == True:
                    self.unlock()
                    self.lastState = currentState
                    self.debounceCheck = False
                else:
                    self.debounceCheck = True
            else:
                time.sleep(0.1)
            if loop==False:
                break
    def unlock(self,timeout=3):
        board.setHigh(self.latchPin)
        board.analogWrite(self.latchPin,255)
        time.sleep(timeout)
        board.setLow(self.latchPin)
        board.analogWrite(self.latchPin,0)


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

front_door = door(47,46)
