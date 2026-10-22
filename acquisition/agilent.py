# -*- coding: utf-8 -*-
import serial
from time import sleep
import time


#############################################################################
class usb():
    def __init__(self,add,dev):
        self.inst = dev.open_resource(add)
        self.inst.write('OUTP:TRIG ON')
        time.sleep(0.1)
        response = self.inst.query("*OPC?")
        print('OUTP:TRIG ON',response)

        self.inst.write('OUTP:TRIG:SLOP POS')
        time.sleep(0.1)
        response = self.inst.query("*OPC?")
        print('OUTP:TRIG:SLOP POS',response)

    def write(self,text):
        self.inst.write(text)
        time.sleep(0.1)
        response = self.inst.query("*OPC?")
        print(text,response)

    def query(self, command):
        """Envoie une commande et retourne la réponse complète."""
        self.inst.write(command)
        sleep(0.1)
        response = self.inst.read().strip()
        print(f"Query: {command}, Réponse: {response}")
        return response

    def reset(self):
        r""" Reset the device
        """
        self.inst.write('*RST')
        time.sleep(0.1)
        response = self.inst.query("*OPC?")
        print('*RST',response)

    def output(self,text):
        r""" Enable or disable the output of the waveform function generator.

        When status is *on*, the generator output is enabled and a signal is sent,
        while when the status is *off* no signal is going out from the generator.
        To perform these actions,
        the command OUTP, followed by either ON or OFF,
        is sent to the generator.

        :param status: is either *on* or *off*'
        :type status: string

        :return: the status of the generator, that is ON or OFF
        :rtype: string

        """
        if text == 'on':
            self.inst.write('OUTP ON')
            time.sleep(0.1)
            response = self.inst.query("*OPC?")
            print('OUTP ON',response)
        elif text == 'off':
            self.inst.write('OUTP OFF')
            time.sleep(0.1)
            response = self.inst.query("*OPC?")
            print('OUTP OFF',response)
        value = self.inst.write('OUTP?')
        return value
#############################################################################


#############################################################################
class model33250(serial.Serial):
    r""" Class to interact with a waveform generator,
    model 32250A from Agilent, using a RS232.
    """
    
    def __init__(self,port):
        r"""   Import the port of the generator and open it.
        In order to communicate with the generator through RS232,
        the following parameters need to be used:
        
        - Baudrate rate: 9600 (factory setting is 57 600 ?),
        - Parity: None,
        - Data bits: 8 bits,
        - Number of stop bits: 1 bit,
        - Handshake mode:  XonXoff on, RTS/CTS on (factory setting is DTR/DSR ?)
        
        (I have to choose between XonXoff and RTS/CTS)
        The number of maximum of bits to be read from the generator is set arbitruary to 516 bits.
        The information about the generator are obtained using the function \*IDN?
        
        :param port: port name to which the device is connected
        :type port: string
        
        """

        serial.Serial.__init__(self,port=port,baudrate=9600,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,timeout=1,xonxoff=0,rtscts=1,dsrdtr=0)
        self.info = self.query('*IDN?')        

    def send(self,command):
        r""" Send a command to the device.
        
        The command is a text that is converted in bytes to be understood
        by the device.
         
        :param command: command to be sent
        :type command: string
         
        :return: number of bytes sent
        :rtype: bytes
        
        """
        line = command + '\n'
        value = self.write(line.encode('utf-8'))
        return value
    
    def receive(self):
        r""" Get information from the device
         
        :return: data or information given by the device
        :rtype: string
        
        """
        data = self.read(516).decode('utf-8')
        return data.rstrip()   
    
    def query(self,command):
        r""" Make a query to the device using the function write and read
        of the class pyserial.
        
        :param command: command to perform
        :type command: string
        
        """
        line = command + '\n'
        value = self.write(line.encode('utf-8'))
        data = self.read(516).decode('utf-8')
        return data.rstrip()       
    
    def output(self,status):
        r""" Enable or disable the output of the waveform function generator.
        
        When status is *on*, the generator output is enabled and a signal is sent,
        while when the status is *off* no signal is going out from the generator.
        To perform these actions, 
        the command OUTP, followed by either ON or OFF,
        is sent to the generator.
        
        :param status: is either *on* or *off*'
        :type status: string
        
        :return: the status of the generator, that is ON or OFF
        :rtype: string
        
        """
        if status == 'on':
            self.send('OUTP ON')
        elif status == 'off':
            self.send('OUTP OFF')
        value = self.query('OUTP?')
        return value

    def reset(self): 
        r""" Reset the device
        """       
        self.send('*RST')
###############################################################################
