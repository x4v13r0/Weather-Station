import time
import WStation_fun as WS

# Web Figures & Configuration
dayinsec=24*60*60
weekinsec=dayinsec*7
monthinsec=dayinsec*30
yearinsec=dayinsec*365

durs=[dayinsec,weekinsec,monthinsec,yearinsec]
durnames=['day','week','month','year']
web_figs  =['web_figure_1','web_figure_2','web_figure_3']
web_titles=['Temperature (dgC)','Pressure (hPa)','Relative humidity (%)']
# --> ex: /var/www/html/web_figure_1_day.png
##############################################################################
refresh_dur=60.       # refresh duration in s
logfile='WS_log.txt'  # logfile to plot

# Web Figures initialization
print "Initializing web curves"
WS.gen_web_curve(logfile,web_figs,web_titles,durs,durnames)

prev_time=time.time()

while True:
    cur_time=time.time()
    if time.time()-prev_time>refresh_dur:
        print 'Updating web curves @%.2f' % cur_time
        WS.gen_web_curve(logfile,web_figs,web_titles,durs,durnames)
        prev_time=time.time()
