import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI

from Adafruit_BME280 import *
import Adafruit_Nokia_LCD as LCD

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter

# LCD contrast
default_contrast=50

# Raspberry Pi hardware SPI config for Nokia 5110 display
DC = 23
RST = 24
SPI_PORT = 0
SPI_DEVICE = 0

# 84x48 @100dpi
mpl.rcParams["figure.figsize"] = (LCD.LCDWIDTH/100., LCD.LCDHEIGHT/100.)
mpl.rcParams["figure.subplot.bottom"]=0.3
mpl.rcParams["ytick.labelsize"]=8
mpl.rcParams["font.weight"]="bold"
mpl.rcParams["font.family"]="Dot-Matrix"
mpl.rcParams["axes.formatter.useoffset"]=False

def get_sensordata(sensor):
	temp = sensor.read_temperature()
	pres = sensor.read_pressure() / 100. # hectopascals
	humi = sensor.read_humidity()
	return [temp, pres, humi]

def display_curdata(temperature,pressure,humidity):
	# Hardware SPI usage:
	disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))
	# Initialize library.
	disp.begin(contrast=default_contrast)
	# Clear display.
	disp.clear()
	disp.display()
	
	# Create blank image for drawing.
	# Make sure to create image with mode '1' for 1-bit color.
	image = Image.new('1', (LCD.LCDWIDTH, LCD.LCDHEIGHT))
	
	# Get drawing object to draw on image.
	draw = ImageDraw.Draw(image)
	
	# Draw a white filled box to clear the image.
	draw.rectangle((0,0,LCD.LCDWIDTH,LCD.LCDHEIGHT), outline=255, fill=255)
	
	# Load font.
	font = ImageFont.load_default()
	font_path='dotmatrixnormal.ttf'
	font = ImageFont.truetype(font_path,10)

	datastring='T = %6.1f C' % temperature
	draw.text((4,8), datastring, font=font)
	datastring='P = %6.1f Pa' % pressure
	draw.text((4,20), datastring, font=font)
	datastring='HR= %6.1f %%' % humidity
	draw.text((4,32), datastring, font=font)
	
	# Display image.
	disp.image(image)
	disp.display()

def display_image(image_file,title):
	# Hardware SPI usage:
	disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))
	# Initialize library.
	disp.begin(contrast=default_contrast)
	
	# Clear display.
	disp.clear()
	disp.display()
	
	# Load image and convert to 1 bit color and resize
#	image = Image.open(image_file).convert('1').resize((LCD.LCDWIDTH, LCD.LCDHEIGHT))
	image = Image.open(image_file).convert('1')

	# Get drawing object to draw on image.
	draw = ImageDraw.Draw(image)

	# Load font.
	font = ImageFont.load_default()
	#font_path='/usr/share/fonts/truetype/roboto/Roboto-Regular.ttf'
	font_path='dotmatrixnormal.ttf'
	font = ImageFont.truetype(font_path,10)
	draw.text((15,40), title, font=font)
	
	# Display image.
	disp.image(image)
	disp.display()
	
def display_reset():
	# Hardware SPI usage:
	disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))
	disp.reset()

def gen_curve(datafile):
	data=np.loadtxt(datafile)
	ind=data[:,0]>data[-1,0]-24*60*60 # Last day restriction
	dat=data[ind,:]
	t=dat[:,0]
	for i in range(1,dat.shape[1]):
		dati=dat[:,i]
		plt.figure(i)
		ax=plt.axes(frameon=False)
		plt.plot(t,dati,'sk',ms=1,mfc='k')
		ma=np.ceil(dati.max())
		mi=np.floor(dati.min())
		plt.ylim([mi,ma])
		plt.xlim([t.min()-1.,t.max()+1.])
		# Ticks config
		med=np.floor((mi+ma)/2.)
		ytis=np.unique([mi,med,ma])
		plt.yticks(ytis)
		plt.xticks([])
		
		#dig=max(len(str(mi)),len(str(ma)))
		#fmt='%'+'%d'%dig+'.0f' #format of yticklabel: %n.0f
		#padval=-10-dig*6       #position the ytick label inside the axe
	
		#majorFormatter=FormatStrFormatter(fmt)
		#ax.yaxis.set_major_formatter(majorFormatter)
		#plt.tick_params(pad=padval)

		#plt.savefig('figure_%d.png' % i)

		# Save temporary figure
		plt.yticks([])
		plt.savefig('figure_tmp.png')
		
		# Add yticks to graph with PIL
		image = Image.open('figure_tmp.png').convert('1')
		# Get drawing object to draw on image.
		draw = ImageDraw.Draw(image)
		# Load font.
		font_path='dotmatrixnormal.ttf'
		font = ImageFont.truetype(font_path,10)
		for j,yti in enumerate(ytis):
			ypos=30-(yti-mi)*30/(ma-mi)
			draw.text((10,ypos), '-%.0f' % yti, font=font)
		image.save('figure_%1d.png' % i,'PNG')
