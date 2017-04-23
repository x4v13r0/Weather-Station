import time, os.path, shutil
import RPi.GPIO as GPIO
#import Adafruit_Nokia_LCD as LCD
#import Adafruit_GPIO.SPI as SPI
#import Adafruit_BME280 as BME280

import WStation_fun as WS
#import numpy as np

##############################################################################
# Durations settings
measu_period = 10.*60. # in seconds - measurement period
measu_period = 10. # in seconds - measurement period
display_dura = 10. # in seconds - display duration
bl_dura=display_dura/2 # backlight duration

# LCD display modes
modmax=4             # 0: no display, 1: data, 2: temp, 3: pres, 4: humidity

##############################################################################
# Control button
buttonPin=21

# Control button initialization
GPIO.setmode(GPIO.BCM)
GPIO.setup(buttonPin,GPIO.IN)

##############################################################################
# Backlight pin
blPin=20

# initialization
GPIO.setup(blPin,GPIO.OUT,initial=0)

###############################################################################
## LCD contrast
#default_contrast=50

## Raspberry Pi hardware SPI config for Nokia 5110 display
#DC = 23
#RST = 24
#SPI_PORT = 0
#SPI_DEVICE = 0

## Hardware SPI usage:
#spidev=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000)
#disp = LCD.PCD8544(DC, RST, spi=spidev)
## Initialize library.
#disp.begin(contrast=default_contrast)

##############################################################################
# Sensor Initialize
#sensor = BME280.BME280(mode=BME280.BME280_OSAMPLE_8)
temperature, pressure, humidity = WS.get_sensordata()

print 'Temp      = {0:0.3f} deg C'.format(temperature)
print 'Pressure  = {0:0.2f} hPa'.format(pressure)
print 'Humidity  = {0:0.2f} %'.format(humidity)

##############################################################################
# Log file initialization
logfile='WS_log.txt'
line=[]
if os.path.isfile(logfile):
	with open(logfile,'r') as log:
		line.append(log.readlines())
	shutil.move(logfile,'WS_log_'+time.strftime('%Y%m%d%H%M%S')+'.txt')

with open(logfile,'a') as log:
	if 'line' in locals() and len(line)!=0 :
		log.writelines(line[-1])
	log.write('%17.6f %.2f %.2f %.2f\n' % (time.time(), temperature, pressure, humidity))
	log.write('%17.6f %.2f %.2f %.2f\n' % (time.time(), temperature, pressure, humidity)) # duplicate to ensure multiple lines

# LCD Figures
figs  =['figure_1.png','figure_2.png','figure_3.png']
titles=['T 24h (dgC)','P 24h (hPa)','HR 24h (%)']
# LCD Figures initialization
WS.gen_curve(logfile,figs,titles)
##############################################################################
# Initialize loop
prev_inread=0
mod=0

# Reference time
press_time = time.time()
measu_time = press_time

while True:
	cur_time=time.time()
	
	# Sensor actualisation
	if (cur_time-measu_time)>measu_period:
		temperature, pressure, humidity = WS.get_sensordata()
		measu_time=cur_time
		print 'Measured @%.2f' % cur_time
		with open(logfile,'a') as log:
			log.write('%17.6f %.2f %.2f %.2f\n' % (cur_time, temperature, pressure, humidity))
		
		WS.gen_curve(logfile,figs,titles)
	# Button interactions
	inread=GPIO.input(buttonPin)
	if inread and not prev_inread:
		print 'Button pressed'
		press_time=time.time()
		if mod==0 or mod==modmax:
			WS.display_reset()
			WS.display_curdata(temperature,pressure,humidity)
			GPIO.output(blPin,1)
			mod=1

		elif mod>0:
			WS.display_reset()
			WS.display_image(figs[mod-1])
			GPIO.output(blPin,1)
			mod+=1
			if mod>modmax:
				mod=0
	# Clear display when inactive
	if mod!=0 and (time.time()-press_time)>display_dura:
		print 'Inactivity: Clearing disp'
		WS.display_reset()
		mod=0

	# Backlight off
	if GPIO.input(blPin) and (time.time()-press_time)>bl_dura:
		print 'Backlight Off'
		GPIO.output(blPin,0)

	prev_inread=inread
	time.sleep(0.05)
