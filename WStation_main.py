import time, os.path, shutil
import RPi.GPIO as GPIO
import threading as thr

import WStation_fun as WS

#-----------------------------------------------------------------------------
# Threaded functions for graphs creation
def curves_upd_threaded(lcd_refresh_dur,web_refresh_dur,logfile,figs,titles):    
    # Web Figures & Configuration
    dayinsec=24*60*60
    weekinsec=dayinsec*7
    monthinsec=dayinsec*30
    yearinsec=dayinsec*365
    
    durs=[dayinsec,weekinsec,monthinsec,yearinsec]
    durnames=['day','week','month','year']
    web_figs  =['web_figure_1','web_figure_2','web_figure_3']
    web_titles=['Temperature (dgC)','Pressure (hPa)','Relative humidity (%)']
    DocRoot = '/var/www/html'
    # --> ex: /var/www/html/web_figure_1_day.png

    lcd_prev_time=time.time()
    web_prev_time=lcd_prev_time
    
    while True:
        cur_time=time.time()
        if cur_time-lcd_prev_time>lcd_refresh_dur:
            print 'Updating LCD curves'
            WS.gen_curve(logfile,figs,titles)
            lcd_prev_time=cur_time

        if cur_time-web_prev_time>web_refresh_dur:
            print 'Updating web curves'
            WS.gen_web_curve(logfile,web_figs,web_titles,durs,durnames,DocRoot)
            web_prev_time=cur_time

        # Small trick to save some CPU
        time.sleep(min(lcd_refresh_dur, web_refresh_dur))
#-----------------------------------------------------------------------------

if __name__ == "__main__":
    print "Weather Station initializing... Please wait"
    
    ##############################################################################
    # Durations settings
    measu_period = 10.*60. # in seconds - measurement period
    measu_period = 10. # in seconds - measurement period
    display_dura = 10. # in seconds - display duration
    bl_dura=display_dura/2 # backlight duration
    
    web_refresh_dur = 60. # in seconds
    lcd_refresh_dur = 10. # in seconds
    
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
    
    ##############################################################################
    # Sensor Initialize
    temperature, pressure, humidity = WS.get_sensordata()
    
    print 'Temp      = {0:0.3f} deg C'.format(temperature)
    print 'Pressure  = {0:0.2f} hPa'.format(pressure)
    print 'Humidity  = {0:0.2f} %'.format(humidity)
    
    ##############################################################################
    # LCD Figures
    figs  =['figure_1.png','figure_2.png','figure_3.png']
    titles=['T 24h (dgC)','P 24h (hPa)','HR 24h (%)']
    
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
        log.write('%17.6f %.2f %.2f %.2f\n' % (time.time(), temperature, pressure, humidity)) # duplicate to ensure multiple lines for plot
    
    # Measurement file is ready
    print "Launching plotting thread..."
    curves_thread=thr.Thread(target=curves_upd_threaded, args=(lcd_refresh_dur, web_refresh_dur, logfile, figs, titles))
    curves_thread.start()
    
    ##############################################################################
    # Initialize loop
    prev_inread=0
    mod=0
    
    # Reference time
    press_time = time.time()
    measu_time = press_time
    
    print "Initialization done !"
    print "Entering the infinite loop"
    
    while True:
        cur_time=time.time()
        
        # Sensor actualisation
        if (cur_time-measu_time)>measu_period:
            temperature, pressure, humidity = WS.get_sensordata()
            measu_time=cur_time
            print 'Measured @%.2f' % cur_time
            with open(logfile,'a') as log:
                log.write('%17.6f %.2f %.2f %.2f\n' % (cur_time, temperature, pressure, humidity))
    
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
    
