import threading
import time

from . import utils

class ControlThread(threading.Thread):
    "A class that shows information about a running SmartDL object."
    def __init__(self, obj):
        threading.Thread.__init__(self)
        self.obj = obj
        self.progress_bar = obj.progress_bar
        self.logger = obj.logger
        self.shared_var = obj.shared_var
        
        self.dl_speed = 0
        self.eta = 0
        self.lastBytesSamples = []  # list with last 50 Bytes Samples.
        self.last_calculated_totalBytes = 0
        self.calcETA_queue = []
        self.calcETA_i = 0
        self.calcETA_val = 0
        self.dl_time = -1.0
        
        self.daemon = True
        self.start()
        
    def run(self):
        t1 = time.time()
        self.logger.info("Control thread has been started.")
        
        while not self.obj.pool.done():
            self.dl_speed = self.calcDownloadSpeed(self.shared_var.value)
            if self.dl_speed > 0:
                self.eta = self.calcETA((self.obj.filesize-self.shared_var.value)/self.dl_speed)
                
            if self.progress_bar:
                if self.obj.filesize:
                    status = r"[*] %s / %s @ %s/s %s [%3.1f%%, %s left]   " % (utils.sizeof_human(self.shared_var.value), utils.sizeof_human(self.obj.filesize), utils.sizeof_human(self.dl_speed), utils.progress_bar(1.0*self.shared_var.value/self.obj.filesize), self.shared_var.value * 100.0 / self.obj.filesize, utils.time_human(self.eta, fmt_short=True))
                else:
                    status = r"[*] %s / ??? MB @ %s/s   " % (utils.sizeof_human(self.shared_var.value), utils.sizeof_human(self.dl_speed))
                status = status + chr(8)*(len(status)+1)
                print(status, end=' ', flush=True)
            time.sleep(0.1)
            
        if self.obj._killed:
            self.logger.info("File download process has been stopped.")
            return
            
        if self.progress_bar:
            if self.obj.filesize:
                print(r"[*] %s / %s @ %s/s %s [100%%, 0s left]    " % (utils.sizeof_human(self.obj.filesize), utils.sizeof_human(self.obj.filesize), utils.sizeof_human(self.dl_speed), utils.progress_bar(1.0)))
            else:
                print(r"[*] %s / %s @ %s/s    " % (utils.sizeof_human(self.shared_var.value), utils.sizeof_human(self.shared_var.value), utils.sizeof_human(self.dl_speed)))
                
        t2 = time.time()
        self.dl_time = float(t2-t1)
        
        while self.obj.post_threadpool_thread.is_alive():
            time.sleep(0.1)
            
        self.obj.pool.shutdown()
        self.obj.status = "finished"
        if not self.obj.errors:
            self.logger.info("File downloaded within %.2f seconds." % self.dl_time)
            
    def get_eta(self):
        if self.eta <= 0 or self.obj.status == 'paused':
            return 0
        return self.eta
    def get_speed(self):
        if self.obj.status == 'paused':
            return 0
        return self.dl_speed
    def get_dl_size(self):
        if self.shared_var.value > self.obj.filesize:
            return self.obj.filesize
        return self.shared_var.value
    def get_final_filesize(self):
        return self.obj.filesize
    def get_progress(self):
        if not self.obj.filesize:
            return 0
        return 1.0*self.shared_var.value/self.obj.filesize
    def get_dl_time(self):
        return self.dl_time
        
    def calcDownloadSpeed(self, totalBytes, sampleCount=30, sampleDuration=0.1):
        '''
        Function calculates the download rate.
        @param totalBytes: The total amount of bytes.
        @param sampleCount: How much samples should the function take into consideration.
        @param sampleDuration: Duration of a sample in seconds.
        '''
        l = self.lastBytesSamples
        newBytes = totalBytes - self.last_calculated_totalBytes
        self.last_calculated_totalBytes = totalBytes
        if newBytes >= 0: # newBytes may be negetive, will happen
                          # if a thread has crushed and the totalBytes counter got decreased.
            if len(l) == sampleCount: # calc download for last 3 seconds (30 * 100ms per signal emit)
                l.pop(0)
                
            l.append(newBytes)
            
        dlRate = sum(l)/len(l)/sampleDuration
        return dlRate
        
    def calcETA(self, eta):
        self.calcETA_i += 1
        l = self.calcETA_queue
        l.append(eta)
        
        if self.calcETA_i % 10 == 0:
            self.calcETA_val = sum(l)/len(l)
        if len(l) == 30:
            l.pop(0)

        if self.calcETA_i < 50:
            return 0
        return self.calcETA_val
