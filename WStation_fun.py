import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI

import Adafruit_BME280 as BME280
import Adafruit_Nokia_LCD as LCD

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdt

import datetime

##############################################################################
# matplotlib initialization valid for ALL plots (LCD & web)
##############################################################################
mpl.rcParams["axes.formatter.useoffset"]=False

##############################################################################
# BME280 sensor initialization
##############################################################################
sensor = BME280.BME280(mode=BME280.BME280_OSAMPLE_8)

##############################################################################
# LCD display
##############################################################################
# LCD contrast
default_contrast=50

# Raspberry Pi hardware SPI config for Nokia 5110 display
DC = 23
RST = 24
SPI_PORT = 0
SPI_DEVICE = 0

# Hardware SPI usage:
spidev=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000)
disp = LCD.PCD8544(DC, RST, spi=spidev)
# Initialize library.
#disp.begin(contrast=default_contrast)

##############################################################################
# Functions
##############################################################################
def get_sensordata():
    temp = sensor.read_temperature()
    pres = sensor.read_pressure() / 100. # hectopascals
    humi = sensor.read_humidity()
    return [temp, pres, humi]

def display_curdata(temperature,pressure,humidity):
    # Hardware SPI usage:
    disp = LCD.PCD8544(DC, RST, spi=spidev)
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
    font_path='dotmatrixnormal.ttf'
    font = ImageFont.truetype(font_path,8)

    datastring='T = %6.1f C' % temperature
    draw.text((4,8), datastring, font=font)
    datastring='P = %6.1f Pa' % pressure
    draw.text((4,20), datastring, font=font)
    datastring='HR= %6.1f %%' % humidity
    draw.text((4,32), datastring, font=font)
    
    # Display image.
    disp.image(image)
    disp.display()

def display_image(image_file):
    # Hardware SPI usage:
    disp = LCD.PCD8544(DC, RST, spi=spidev)
    # Initialize library.
    disp.begin(contrast=default_contrast)
    
    # Clear display.
    disp.clear()
    disp.display()
    
    # Load image and convert to 1 bit color and resize
    image = Image.open(image_file).convert('1').resize((LCD.LCDWIDTH, LCD.LCDHEIGHT))
    # Force black and white
    imgbw=image.point(lambda x: 0 if x<230 else 255, '1')

    # Display image.
    disp.image(imgbw)
    disp.display()
    
def display_image_old(spidev,image_file,title):
    # Hardware SPI usage:
    disp = LCD.PCD8544(DC, RST, spi=spidev)
    # Initialize library.
    disp.begin(contrast=default_contrast)
    
    # Clear display.
    disp.clear()
    disp.display()
    
    # Load image and convert to 1 bit color and resize
    image = Image.open(image_file).convert('1')

    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)

    # Load font.
    font_path='dotmatrixnormal.ttf'
    font = ImageFont.truetype(font_path,8)
    draw.text((15,40), title, font=font)
    
    # Display image.
    disp.image(image)
    disp.display()
    
def display_reset():
    # Hardware SPI usage:
    disp = LCD.PCD8544(DC, RST, spi=spidev)
    disp.reset()

def gen_curve(datafile,figs,titles):
    data=np.loadtxt(datafile)
    ind=data[:,0]>data[-1,0]-24*60*60 # Last day restriction
    dat=data[ind,:]
    t=dat[:,0]
    for i in range(1,dat.shape[1]):
        title=titles[i-1]
        fig=figs[i-1]
        dati=dat[:,i]

        f1=plt.figure(i,figsize=(LCD.LCDWIDTH/100., LCD.LCDHEIGHT/100.),dpi=100)
        f1.subplots_adjust(bottom=0.39,top=0.8,left=0.,right=1.)
        ax=plt.axes(frameon=False)
        plt.plot(t,dati,'sk',ms=1,mfc='k')
        ma=np.ceil(dati.max())
        mi=np.floor(dati.min())
        plt.ylim([mi,ma])
        plt.xlim([t.min()-1.,t.max()+1.])
        # Ticks config
        med=np.floor((mi+ma)/2.)
        ytis=np.unique([mi,med,ma])
        dig=max(len(str(mi)),len(str(ma)))
        plt.yticks(ytis,fontsize=8,fontname="Dot-Matrix",fontweight="bold")
        plt.tick_params(axis='y',direction='in', pad=-2-4*dig)
        plt.xticks([])
        plt.xlabel(title,fontsize=8,fontname="Dot-Matrix",fontweight="bold")
        plt.savefig(fig,dpi=100)
        #Force black and white
        imggray=Image.open(fig).convert('L')
        imgbw=imggray.point(lambda x: 0 if x<230 else 255, '1')
        imgbw.save(fig)
    plt.close('all')
        
def gen_web_curve(datafile,figs,titles,durs,durnames):
    data=np.loadtxt(datafile)
    t1=data[-1,0]
    for idur,dur in enumerate(durs):
        t0=t1-dur
        tt0=datetime.datetime.fromtimestamp(t0)
        ind=data[:,0]>t0
        dat=data[ind,:]
        t=dat[:,0]
        tt=[]
        for it,tmp in enumerate(t):
            tt.append(datetime.datetime.fromtimestamp(dat[it,0]))
        for i in range(1,data.shape[1]):
            title=titles[i-1]
            fig=figs[i-1]
            
            dati=dat[:,i]
            plt.figure(i,figsize=(12,8))
            plt.plot(tt,dati,'b',lw=2)
            plt.xlim(tt0,tt[-1])
            plt.xlabel('time',fontsize=14)
            plt.ylabel(title,fontsize=14)
            if durnames[idur]=='day':
                plt.gca().xaxis.set_major_formatter(mdt.DateFormatter('%Hh'))
                plt.gca().xaxis.set_major_locator(mdt.HourLocator())
            elif durnames[idur]=='week':
                plt.gca().xaxis.set_major_formatter(mdt.DateFormatter('%a'))
                plt.gca().xaxis.set_major_locator(mdt.DayLocator())
            elif durnames[idur]=='month':
                plt.gca().xaxis.set_major_formatter(mdt.DateFormatter('%b %d'))
                plt.gca().xaxis.set_major_locator(mdt.WeekdayLocator())
            else:
                plt.gca().xaxis.set_major_formatter(mdt.DateFormatter('%b %y'))
                plt.gca().xaxis.set_major_locator(mdt.MonthLocator())

            plt.grid()
            plt.savefig('/var/www/html/'+fig+'_'+durnames[idur])
            plt.close(i)
    plt.close('all')
