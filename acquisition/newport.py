#!/usr/bin/env python
# -*- coding: utf-8 -*-

r"""
Linux Raw USB Device Configuration

To enable writing to a USB device in raw or usbtmc mode, 
the device file must be readable writable by users. 
As this is not normally the default, 
you need to add rules to /etc/udev/rules.d to override the default permissions.
For instance, to add a Tektronix DPO 4104 oscilloscope with world-writable permissions,
add the following to rules.d:

ATTRS{idVendor}=="0699", ATTRS{idProduct}=="0401", SYMLINK+="tekdpo4104", MODE="0666"


From the manual,

Section 1.4.2:

- RS232-C, 19200 baud, 8 bits, 8, N, 1

- USB, 921600 baud, 8bits, 8, N, 1

- IEEE488 (optional)

Section 3.2.:

In this manual, Remote Interface refers to the three communication
interfaces that the controller can use to communicate with a computer
or a terminal via commands in ASCII format.

Interfaces using typical commands.

+--------------------------------------------------------------+
|Command communication and process time (in milliseconds)      |
+------------------+--------------+--------------+-------------+
|Command send      | RS232C       |   USB        | IEEE        |
+------------------+------+-------+-------+------+------+------+
|and read response |ESP301| ESP300| ESP301|ESP300|ESP301|ESP300|
+------------------+------+-------+-------+------+------+------+
|TB?               |25.08 | 28.02 | 4.18  |  -   | 1.32 | 2.88 |
+------------------+------+-------+-------+------+------+------+
|VE?               |24.84 | 27.60 | 3.92  |  -   | 0.96 | 1.68 |
+------------------+------+-------+-------+------+------+------+

Measurements have been taken from a PC using Windows XP operating system and with a 2GHz processor and 1Gb RAM.


section 3.2.1 : "The ESP301’s RS-232C configuration is fixed at 8 data bits, no parity, and 1 stop bit. To prevent buffer overflow when data is transferred to the ESP301
controller input buffer, a CTS/RTS hardware handshake protocol is
implemented."

section 3.2.2 : "The ESP301 USB configuration is fixed at 921600 baud, 8 data bits, N parity, and 1 stop bit."

Note

A controller command (or a sequence of commands) has to be terminated with
a carriage return character.
However, responses from the controller are always
terminated by a carriage return/line feed combination. 
This setting may not be changed. 
If the IEEE interface is used, the IEEE controller has to be
configured to terminate the input (read) function when it senses the line feed
character.

"""

import serial
from time import sleep

###############################################################################
class ESP301_RS232(serial.Serial):
    r""" class to interact with a ESP301 motion controller from Newport
    using a serial port.
    serial.Serial offers the function :
    
    * open(),
    
    * close(),
    
    * read(),
    
    * write(),
    
    * in_waiting(),
    
    * out_waiting()
    
    """
    def __init__(self,port):
        r"""
         
        :param port: port given to the EXP301 by the computer
        :type port: string       
        
        """
        serial.Serial.__init__(self,port=port,baudrate=19200,bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,timeout=1,xonxoff=0,rtscts=1,dsrdtr=0)
        self.info = self.query('VE?')
        self.identifier = 'A60409XQA'
        self.model = 'None'
        
    def send(self,command):
        r""" Send a command
        
        :param command: command to be sent
        :type command: string
        
        :return: ?
        :rtype: ?
        
        """
        
        line = command + '\r'
        n = self.write(line.encode('ascii'))
        return n
    
    def receive(self):
        r""" read a data
        
        :return: data
        :rtype: string
        
        """
        data = self.read(516).decode('ascii')
        return data.rstrip('\n\r')   
    
    def query(self,command):
        line = command + '\r'    
        value = self.write(line.encode('ascii'))
        #value = self.read_until('\r\n').decode('ascii')
        data = self.read(516).decode('ascii')
        return data.rstrip('\n\r')   
    
    def motorOn(self,xx):
        r""" Set the motor number xx on.
        It used the commande "MO" (For Motor On).
        
        :param xx: is either '1', '2' or '3'
        :type xx: integer
        
        :return: 1
        :rtype: boolean
        
        """
        self.send(str(xx)+'MO')
        return True

    def motorOff(self,xx):
        r""" Set the motor number xx off.
        It used the commande "MF" (for Motor oFf).
        
        :param xx: is either '1', '2' or '3'
        :type xx: integer
        
        :return: 1
        :rtype: boolean
        
        """
        self.send(str(xx)+'MF')
        return True
        
    def motorStatus(self,xx):
        r""" Get the status (on or off) of the motor number xx.
        It used the commande "MO?" (for is Motor On ?).
        
        :param xx: is either '1', '2' or '3'
        :type xx: integer
        
        :return: 'on' or 'off'
        :rtype: string
        
        """
        self.send(n+'MO?')
        data = self.device.read(1)
        status = data.rstrip()   # \n or \r
        if status == 1:
            value = 'on'
        elif statue == 0:
            value = 'off'
        return value
    
    def abortMotion(self,xx):
        r""" Stop the motion of the motor number xx.
        It used the command "AB" (for ABort).
        If no valid number xx is given all motors are stopped.
        
        :param xx: is either '1', '2' or '3'
        :type xx: integer
        
        :return: 'on' or 'off'
        :rtype: string
        
        """
        if (xx == '1') or (xx == '2') or (xx== '3'):
            self.send(str(xx) + 'AB')
        else:
            self.send('AB')
        return True
            
    def waitMotionStop(self,xx):
        r""" Wait until the motor xx stops moving.
        It used the command "WS" (for Wait for motion Stop).
        If no valid number xx is given, it waits until all motors are not moving.
        
        :param xx: is either '1', '2' or '3'
        :type xx: integer
        
        :return: 'on' or 'off'
        :rtype: string
        
        """
        self.send(str(xx) + 'WS')
        return 1

    def waitPosition(self,xx):
        r""" Suspend the motion of the motor number xx.
        It used the command "WT" (for WaiT).
        If no valid number xx is given all motors are suspended.

        :param xx: is either '1', '2' or '3'
        :type xx: integer

        :return: 'on' or 'off'
        :rtype: string

        """
        self.send(str(xx) + 'WP')
        return 1


    def readPosition(self,xx):
        r""" Read the absolute position of the motor xx
        
        :param xx: number of the motor
        :type xx: integer
        
        :return: position of the motor xx
        :rtype: float
        
        """
        self.send(str(xx) + 'TP')
        return self.receive()
  
    def infoStage(self,xx):
        r""" Read the information about the stage xx.
        
        :param xx: number of the motor
        :type xx: integer
        
        :return: stage information
        :rtype: string

        """
        
        self.send(str(xx) + 'ID?')
        return self.receive()
        
    def moveAbsolute(self,xx,nn):
        r""" Move the motor xx at the absolute position nn.
        
        :param xx: number of the motor
        :type xx: string
        
        :param nn: absolute position
        :type xx: float
        
        :return: return 1 
        :rtype: integer

        """
        self.send(str(xx) + 'PA' + str(nn)+  ';' + str(xx) + 'WP')
        return 1
        
    def moveRelative(self,xx,nn):
        r""" Move the motor xx at the relative position nn
         
        :param xx: number of the motor
        :type xx: string
        
        :param nn: absolute position
        :type xx: float
        
        :return: return 1 
        :rtype: integer
        
        """
        self.send(str(xx) + 'PR' + str(nn) +  ';' + str(xx) + 'WS'+ str(100) )
        return 1
###############################################################################
