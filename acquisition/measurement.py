# -*- coding: utf-8 -*-
import math
import scipy.constants

###############################################################################
class ultrasound:
    r""" This class gathers all the information about ultrasound, that is:
    
    - the function of the pulse 'function', by default it is  'SIN'
    - the frequency 'frequency' in Hz
    - the duty cycle 'DC' in %
    - the number of cycle 'n_cycle' (no unit)
    - the duration of the ultrasonic signal   'duration' in s
    -   'function' 'None'
    - the amplitude of the ultrasonic signal  'amplitude' in V
    - the pulse repetition frequency of the signal  'PRF' in Hz
    - the section area of the ultrasonic beam at the focal region   'section'  = 0.0284 cm2
    - the convertion of the electrical signal to the acoustic signal by the transducer  'convertion'  = 0.82 %
    
    """
    def __init__(self):
        r""" Initialization of all parameters
        """
        self.function = 'SIN'
        self.frequency = 1.1e6        # in Hz
        self.fmth = 'FM'
        self.n_cycle = 275            # no unit
        self.duration = 30           # in s
        self.function = 'None'
        self.amplitude = 0.05          # in V
        self.PRF = 400                # in Hz
        self.section = 0.0284       # in cm2
        self.convertion = 0.82      # in percentage
        self.pulse_number = self.duration*self.PRF
        self.DC = 100*self.n_cycle*self.PRF/self.frequency             # in %
###############################################################################

###############################################################################
class sample:
    
    def __init__(self):
        r""" Initialization of all parameters
        """
        self.Preparation_date = "today"
        self.temperature = 25 +  scipy.constants.zero_Celsius
        self.temperature_zero = 273.15 # in K
        self.Volume_fraction = 0    # Volume fraction of droplet
        self.C_Drug = 0           # Concentration of drug
        self.filename = None
        self.Diameter = 0
        self.Operator = None
        self.Info = None
        self.Cells = None
        self.directory = ''
        self.duration = 0
###############################################################################

###############################################################################
class data:
    
    def __init__(self):
        self.AVER = []
        self.REV = []
        self.elapsedTime = []
        
    def Isata(self,convertion,section):
        r""" Calculate the spatial average, temporal average intensity 
        :math:`I_{sata}` by multiplying the electrical average 
        (peak and temporal) power :math:`P_{el}` (in Watts) 
        going through the transducer
        by the percentage of electrical power converted to acoustic power 
        (i.e. a coefficient named "convertion", in percent) 
        and dividing it by the area at the focal of the ultrasonic beam 
        (i.e. "section", in cm\ :superscript:`2`):
        
        .. math:: I_{sata} = P_{el} \times \frac{\mathrm{convertion}}{\mathrm{section}}
        
        The electrical power, :math:`P_{el}`, 
        going through the transducer is determined from the wattmeter
        that measures the average (AVER) and reverse (REV) electrical power:

        .. math:: P_{el} = \mathrm{AVER} - \mathrm{REV}
   
        :param convertion: percentage of electrical power converted to acoustic power
        :type convertion: float

        :param section: section of the focal of the ultrasonic beam
        :type section: float

        :return: value
        :rtype: float

        """
        value = convertion*(self.AVER.mean() - self.REV.mean())/section
        return value
    
    
    def Isapa(self,DC,convertion,section):
        r""" Calculate the spatial average, peak average intensity
        :math:`I_{sapa}` by dividing :math:`I_{sata}` by the duty cycle :math:`\mathrm{DC}`
        
        
         .. math:: I_{sapa} = \frac{I_{sapa}}{\mathrm{DC}}       

        :param DC: percentage of electrical power converted to acoustic power
        :type DC: float
        
        :param convertion: percentage of electrical power converted to acoustic power
        :type convertion: float

        :param section: section of the focal of the ultrasonic beam
        :type section: float

        :return: value
        :rtype: float
        
        """
        
        value = self.Isata(convertion,section)/DC
        return value    
    
    def Psapa(self,T,DC,convertion,section):
        r""" Calculate the spatial average, peak average pressure 
        :math:`p_{sapa}` from :math:`I_{sapa}` using the equation :
        
        
        .. math:: p_{sapa} = \sqrt{ 2 \rho c I_{sapa}} \times 10^{-5} 
         
        where :math:`\rho` and :math:`c` are respectively the density (in kg/cm\ :superscript:`3`) 
        of the medium in which the ultrasound propagates and the ultrasound speed of sound (in m/s).
        The value of speed of sound  :math:`c` is given by the Marczak equation (the range 0-40°C):
        
        .. math:: c = 1405.03 + 4.624 T - 0.0383 T^{2}
        
        and the density :math:`\rho` (5-40°C) of air-free water is calculate from Eq 3 in doi: 10.6028/jres.097.013:
        
        .. math:: \rho = 999.85308 + 6.32693 \times 10^{-2} T - 8.523829 \times 10^{-3} T^{2} + 6.943248 \times 10^{-5} T^{3} - 3.821216 \times 10^{-7} T^{4}

        :param T: temperature in celsius degree
        :type DC: float

        :param DC: percentage of electrical power converted to acoustic power
        :type DC: float
        
        :param convertion: percentage of electrical power converted to acoustic power
        :type convertion: float

        :param section: section of the focal of the ultrasonic beam
        :type section: float

        :return: value
        :rtype: float
        
        """
        
        c = 1405.03+4.624*T-0.0383*(T**2)
        rho = 999.85308 + 6.32693*1e-2*T-8.523829*1e-3*math.pow(T,2)+6.943248*1e-5*math.pow(T,3)-3.821216*1e-7*math.pow(T,4)
        value = math.sqrt(2*rho*c*self.Isapa(DC,convertion,section))/10000
        return value
###############################################################################
 

###############################################################################
def checkParameters(amplitude,DC,harmonic):
    r""" Operating conditions. Values of voltage that should not be overpassed
    From what I could observe, we have for the gain button :
    
    
    +-----------+----+----+----+----+----+----+----+----+----+----+----+
    | mark      |  1 |  2 |  3 | 4  |  5 | 6  | 7  | 8  | 9  | 10 | 11 |
    +------+----+----+----+----+----+----+----+----+----+----+----+----+
    | gain (dB) |17.2|23.9|30.6|30.6|37.3| 44 |50.7|57.4|64.1|70.8|77.5|
    +------+----+----+----+----+----+----+----+----+----+----+----+----+

     The voltage :math:`V` (in Volts) produced by the function generator 
     is converted into a power :math:`W_{input}` (in Watts) using the equation :
  
     .. math:: W_{input} = (V)^2 / Z
     
     where :math:`Z` is the impedance (50 Ohms).
    
     
  
    .. math:: G= 10 \log(W_{output}/W_{input})
    
    .. math:: W_{output} = e^{G/10} \times W_{input} 
    
   
    Note that the amplifier cannot deliver a peak power more than 300 W.
    Thus there is no meaning to go over a voltage of 1.1 VPP
    
    Limits of power as given by the manufacturer for the fundamental mode 
    (I derived the last column based on the estimated gain...):
        
    +--------+-------+-------+---------+
    | DC     | P_pk  | P_avg | V_pp max|
    +--------+-------+-------+---------+
    |  %     | Watts | Watts | Volts   |
    +--------+-------+-------+---------+
    | 100    | 150   | 150   |0.39     |
    +--------+-------+-------+---------+
    | 87.5   | 187.5 | 150   |0.41     |
    +--------+-------+-------+---------+
    | 75     | 225   | 150   |0.44     |
    +--------+-------+-------+---------+
    | 62.5   | 262.5 | 150   |0.48     |
    +--------+-------+-------+---------+
    | 50     | 300   | 150   |0.54     |
    +--------+-------+-------+---------+
    | 25     | 600   | 150   |0.78     |
    +--------+-------+-------+---------+
    | 10     | 1500  | 150   |1.2      |
    +--------+-------+-------+---------+
    |  5     | 2054.7| 102.7 |1.44     |
    +--------+-------+-------+---------+
    |  1     | 2054.7|  20.5 |1.44     |
    +--------+-------+-------+---------+
    |  0.1   | 2054.7|   2.1 |1.44     |
    +--------+-------+-------+---------+      
    
        
    For the third harmonic:
    
    +--------+-------+-------+
    | DC     | P_pk  | P_avg |
    +--------+-------+-------+
    |  %     | Watts | Watts |
    +--------+-------+-------+
    | 100    | 40    | 40    |
    +--------+-------+-------+
    | 87.5   | 51    | 40    |
    +--------+-------+-------+
    | 75     | 57    | 40    |
    +--------+-------+-------+
    | 62.5   | 68.5  | 40    |
    +--------+-------+-------+
    | 50     | 80    | 40    |
    +--------+-------+-------+
    | 25     | 160   | 40    |
    +--------+-------+-------+
    | 10     | 400   | 40    |
    +--------+-------+-------+
    |  5     | 800   | 40    |
    +--------+-------+-------+
    |  1     | 4000  | 40    |
    +--------+-------+-------+
    |  0.1   | 9750  | 9.8   |
    +--------+-------+-------+    
    
    
    
    :param amplitude: value of voltage given in the function generator (in Volt)
    :type amplitude: float

    :param DC: percentage of electrical power converted to acoustic power
    :type DC: float
        
    :param harmonic: 'FM' or 'TH' for respectively fondamental mode or third harmonic
    :type section: string 

    :return: GO
    :rtype: binary    
    
    :return: message
    :rtype: string      
    """
    GO = True
    message = 'Parameters are ok'
    
    if harmonic == 'FM':
        if (amplitude>0.35) and (DC>87.5) and (DC<=100):
            message = '\nToo high energy: lower amplitude OR duty cycle (at DC=100%, AMP < 0.35 VPP )'
            GO = False
        elif (amplitude>0.4) and (DC>75 and DC<=87.5):
            message += '\nToo high energy: lower amplitude OR duty cycle (at DC=87.5%, AMP < 0.4 VPP)'
            GO = False
        elif (amplitude>0.44) and (DC>62.5 and DC<=75):
            message = '\nToo high energy: lower amplitude OR duty cycle (at DC=75%, AMP < 0.44 VPP)'
            GO = False
        elif (amplitude>0.5) and (DC>50 and DC<=62.5):
            message = '\nToo high energy: lower amplitude OR duty cycle (at DC=62.5%, AMP < 0.5 VPP)'
            GO = False
        elif (amplitude>1.1):
            message = '\nToo high energy: lower amplitude (AMPmax=1.1 VPP)'
            GO = False
    elif harmonic == 'TH':
        if (amplitude>(0.35/3.75)) and (DC>87.5) and (DC<=100):
            message = '\nToo high energy: lower amplitude OR duty cycle (at DC=100%, AMP < 0.35 VPP )'
            GO = False
        elif (amplitude>(0.4/3.75)) and (DC>75 and DC<=87.5):
            message += '\nToo high energy: lower amplitude OR duty cycle (at DC=87.5%, AMP < 0.4 VPP)'
            GO = False
        elif (amplitude>(0.44/3.75)) and (DC>62.5 and DC<=75):
            message = '\nToo high energy: lower amplitude OR duty cycle (at DC=75%, AMP < 0.44 VPP)'
            GO = False
        elif (amplitude>(0.5/3.75)) and (DC>50 and DC<=62.5):
            message = '\nToo high energy: lower amplitude OR duty cycle (at DC=62.5%, AMP < 0.5 VPP)'
            GO = False
        elif (amplitude>(1.1/3.75)):
            message = '\nToo high energy: lower amplitude (AMPmax=1.1 VPP)'
            GO = False
        
    return (GO,message)
            
###############################################################################
