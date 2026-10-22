import platform
import time
import serial.tools.list_ports
import pyvisa


import agilent
import newport
import rohde_schwarz
import keysight


###############################################################################
class scan():

    def scan_RS232():
        ports = list(serial.tools.list_ports.comports())
        return ports


    def scan_USB():
        if platform.system() == "Windows":
            devices = pyvisa.ResourceManager()
        else:
            devices = pyvisa.ResourceManager('@py')
        liste = devices.list_resources()
        print(liste)
        return liste
###############################################################################

###############################################################################
def get_instrument_address(base_address):
    if platform.system() == "Windows":
        # Convertir en format Windows
        parts = base_address.split("::")
        vendor_id = "0x{:04X}".format(int(parts[1]))
        product_id = "0x{:04X}".format(int(parts[2]))
        serial = parts[3]
        return f"USB0::{vendor_id}::{product_id}::{serial}::INSTR"
    else:
        # Garder le format Linux
        return base_address
###############################################################################

###############################################################################
def initialize(devices):
    r""" The function checks if the computer is communicating 
    with the waveform generator, the wattmeter and the motion controller.
    
    In our setup,
    we obtained the following information about the ports:
    
    - EXAMPLE USB serial connection (device ID removed)
    - EXAMPLE USB serial connection (device ID removed)
    - EXAMPLE USB serial connection (device ID removed)
    - EXAMPLE USB serial connection (device ID removed)
    
    Unfortunately, the VID:PID is the same as the same usb hub is used for all devices.
    The difference lies in the model version of the instrument.
    We found out that:
    
    - AL00CFGJA is for the waveform generator
    - PAFOHS74A is for echograph ?
    - AL0mm0BXCMA is for the wattmeter
    - A60409XQA is for motion controller
    
    In addition to checking the port some initialization are done:
    
    - For the generator: 
        * the trigger is set to on (:OUTP:TRIG:SLOP)
        * the triggered is set on positive slope (:OUTP:TRIG ON)
        * The burst stat is set to on (:BURS:STAT ON)
        
    - For the wattmeter
       * The unit is set to Watt (:UNIT0:POW W)
       * All functions of channel 1 are desactivated (:SENSe0:FUNC:OFF:ALL1)
       * All functions of channel 2 are desactivated (:SENSe0:FUNC:OFF:ALL2)
       * Tiggered source is set to internal (:TRIG:SOUR INT)
       * The functiun peak average power is activated (:SENSe0:FUNC "POW:FORW:AVER")
       * The function reverse power is activated (:SENSe0:FUNC "POW:REV")
       
    - For the motion controller:
       * All motors are set to on (1MO;2MO;3MO)
       * The units of all motors are set to millimeter (1SN2;2SN2;3SN2)

    Our wave function generator is out of order. So the device AL00CFGJA does not exist anymore.
    It was replaced by an usb device 'USB::2391::9991::REPLACE_WITH_YOUR_INSTRUMENT_ID::0::INSTR'
    or 'USB::0x0957::0x2707::REPLACE_WITH_YOUR_INSTRUMENT_ID::0::INSTR'

    An additional laboratory example is 'USB0::2391::11015::REPLACE_WITH_YOUR_INSTRUMENT_ID::0::INSTR'
    and its oscilloscope is 'USB::10893::5995::REPLACE_WITH_YOUR_INSTRUMENT_ID::INSTR'


    keysight DSOX1204G : USB0::10893::918::REPLACE_WITH_YOUR_INSTRUMENT_ID::INSTR (touche "Utility", puis choisir "I/O")
    Créez un fichier /etc/udev/rules.d/99-keysight.rules (sudo nano 99-keysight.rules) et ajouter la ligne
    SUBSYSTEM=="usb", ATTR{idVendor}=="2a8d", ATTR{idProduct}=="0396", MODE="0666", GROUP="dialout"


    In linux, the user needs to be in the groupe dialout, otherwise he won't be able to access ttyS0

    https://www.ni.com/fr/support/downloads/drivers/download.ni-visa.html

    """

    ### Port COM
    # First, create a device for each devices connected through a RS232 port using pyserial
    gen = None
    watt = None
    motion = None
    osc = None

    ports = list(serial.tools.list_ports.comports())

    for item in ports:
        (port,description,ID) = item
        p = str(port)

        # RS232 wave generator
        if devices.gen['enabled'] == True:
            if devices.gen['model'] == "RS232 Agilent":
                print(devices.gen['model'])
                if devices.gen['identifier'] in ID:
                    gen = agilent.model33250(p)
                    gen.reset()  # It resets the generator, in particular shutdown the output
                     #set a positive slope
                    print(gen.info)

        # RS232 wattlemeter
        if devices.watt['enabled'] == True:
            if devices.watt['model'] == "RS232 Rohde & Schwarz":
                if devices.watt['identifier'] in ID:
                    ### Wattmeter #################################
                    watt = rohde_schwarz.NRT(p)
                    watt.reset()
                    watt.send(':UNIT0:POW W')          # Set the unit to Watt
                    watt.send(':SENSe0:FUNC:OFF:ALL1') # it desactivates all functions of channel 1
                    watt.send(':SENSe0:FUNC:OFF:ALL2') # it desactivates all functions of channel 2
                    watt.send(':TRIG:SOUR INT')        # Déclenchement de mesure int ou ext. si déclenchement EXT relier la sortie TTL à l'arrière du générateur à AUX TTL du wattmètre (si on branche Sync en face avant du générateur ne marche pas)
                    #watt.send(':TRIG:SOUR OUT')
                    #watt.send(':SENSe0:BURS:MODE AUTO') # Automatically measures the duty cycle
                    #watt.send(':SENSe0:BURS:MODE USER')
                    #watt.send(':SENSe0:BURS:PER  5ms ')  # 1/PRF
                    #watt.send(':SENSe0:BURS:WIDT  0.25ms ') # 1/PRF*DC
                    #watt.send(':SENSe0:FREQ  1MHz')  # f
                    #watt.send(':SENSe0:RRES HIGH')  # resolution on the display, does not affect remote control #######################################
                    #watt.send(':SENSe0:FREQ USER') ## frequency will be given
                    #watt.send(':SENSe0:FUNC:CONC ON')  # two functions possible     ###############################################################
                    watt.send(':SENSe0:FUNC "POW:FORW:AVER"') # it activates the average measurement
                    #watt.send(':SENSe0:FUNC "POW:FOR"')  #display power forward      ###############################################################
                    #watt.send(':SENSe0:FUNC "POW:FORW:PEP"')  # it activates the function peak envelop power
                    watt.send(':SENSe0:FUNC "POW:REV"')
                    #watt.send(':SENSe0:BAND:VID:FNUM 200E3'), at 200 kHz

        # RS232 motion controller
        if devices.motion['enabled'] == True:
            if devices.motion['model'] == "RS232 Newport":
                if devices.motion['identifier'] in ID:
                    ### Motion controller ##########################
                    motion = newport.ESP301_RS232(p)
                    motion.send('1MO;2MO;3MO')        # it puts all motors are on
                    motion.send('1SN2;2SN2;3SN2')     # All motors are in mm units

    ### Port USB
    # Then, create a device for each device connected through a usb port using pyvisa

    # USB devices
    systeme = platform.system().lower()
    if systeme == "windows":
        dev = pyvisa.ResourceManager()
    elif systeme == "linux":
        dev = pyvisa.ResourceManager('@py')
    elif systeme == "darwin":
        dev = pyvisa.ResourceManager()

    liste = dev.list_resources()
    print(f'la liste est {liste}')
    for d in liste:
        if devices.gen['enabled'] == True:
            if devices.gen['model'] == "USB keysight":
                add = get_instrument_address(devices.gen['identifier'])
                if d == add:
                    gen = keysight.usb(add,dev)
                    gen.reset()  # It resets the generator, in particular shutdown the output
            elif devices.gen['model'] == "USB agilent":
                add = get_instrument_address(devices.gen['identifier'])
                if d == add:
                    gen = agilent.usb(add,dev)
                    gen.reset()  # It resets the generator, in particular shutdown the output
        if devices.osc['enabled'] == True:
            if devices.osc['model'] == "USB keysight":
                add = get_instrument_address(devices.osc['identifier'])
                if d == add:
                    osc = keysight.Oscilloscope(add,dev)
                    osc.reset()

    return (gen,watt,motion,osc)

###############################################################################


###############################################################################
def check_port(instrument):
        r""" The function checks if all ports are open.
        Otherwise the closed ports are opened.
        All device should be different from None.
        If not, something wrong occured.

        :param status: a list of instruments
        :type status: list

        :return: an array of True of False
        :rtype: array
        """
        check = numpy.ones(len(instrument))
        i = 0
        for inst in instrument:
            check = True
            if (inst != 'None'):
                if not(inst.is_open):
                    inst.open()
            else:
                check[i] = 0
            i += 1
        return check
###############################################################################
