# -*- coding: utf-8 -*-
import serial

###############################################################################
class NRT(serial.Serial):
    r""" RS-232 interface :
    
    section 3.1.2.
    It is assumed that the baud rate at the NRT is set to 9600 (factory setting, alternative are 4800, 2400, 1200)
    and the handshake is set to XON/OFF. 

    For configuration of the communication partner it should be considered that the
    NRT is basically set for the transmission of 10 bits: 1 start bit, 8 data bits, 1 stop
    bit, no parity bit.

    for USB the baudrate is set at 921600
    """

    def __init__(self, port):       
        serial.Serial.__init__(self,port=port,baudrate=9600,bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,timeout=1,xonxoff=1,rtscts=1,dsrdtr=0)
        self.info = self.query('*IDN?')
        self.identifier = 'AL00BXCMA'
        self.model = 'None'


    def send(self,command):
        line = command + '\n'
        value = self.write(line.encode('utf-8'))
        return value
    
    def receive(self):
        data = self.read(516).decode('utf-8')
        return data.rstrip()   
    
    def query(self,command):
        line = command + '\n'
        value = self.write(line.encode('utf-8'))
        data = self.read(516).decode('utf-8')
        return data.rstrip()       


    def reset(self):
        self.send('*RST;*CLS;*WAI')


    def PEP(self,n,status):
        r"""
          active or desactivate the PNP function
          
        """
        if status == 'on':
            self.send(':SENSe'+str(n)+':FUNC "POW:FORW:PEP"')
        elif status == 'off':
            self.send(':SENSe'+str(n)+':FUNC:OFF "POW:FORW:PEP"')
        return True
 
    def AVER(self,n,status):
        r"""
          active or desactivate the PNP function
        """
        if status == 'on':
            self.send(':SENSe'+str(n)+':FUNC "POW:FORW:AVER"')
        elif status == 'off':
            self.send(':SENSe'+str(n)+':FUNC:OFF "POW:FORW:AVER"')
        return True 
  
 
    def ChannelFuncOff(self,n,m):
        r"""
        desactivate all function in channel m
        
        """
        self.send(':SENSe'+str(n)+':FUNC:ALL'+str(m))
            
    def deviceInfo(self,status):
        self.send('*IDN?<CR><NL>')
        info = self.read('')
        return info

    def dataAllFunction(self,n):
        self.send(self,':SENSe'+str(n)+':DATA?')
        data = self.read()
        return data
        
###############################################################################
