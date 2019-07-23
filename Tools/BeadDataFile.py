import numpy as np
import dill as pickle 
import datetime as dt
import h5py, os, re, glob, time, sys, fnmatch, inspect

import matplotlib.pyplot as plt
import scipy.signal as signal
import scipy
from scipy.signal import welch

class BeadDataFile:
    '''Basic class that holds one data file. 
    Sotres all amplitudes, phases, bead positions, electrodes, cantilever position, as well as all attributes.'''

    def __init__(self, fname):
        '''Initialization'''
        self.fname = fname

        f = h5py.File(fname,'r')
        pos_data = np.array(f['pos_data'])
        quad_data = np.array(f['quad_data']) 
        self.fsamp = f.attrs['Fsamp']
        self.fsamp /= f.attrs['downsamp']

        
        ## estimate xyz based on amp-phase
        self.amp = quad_data.reshape(-1,12).T[:5]
        self.phase = quad_data.reshape(-1,12).T[5:10]
        right = self.amp[0] + self.amp[1]
        left = self.amp[2] + self.amp[3]
        top = self.amp[0] + self.amp[2]
        bottom = self.amp[1] + self.amp[3]
        quad_sum = right + left
        self.x2 = (right - left)/quad_sum
        self.y2 = (top - bottom)/quad_sum    
        self.z2 = self.phase[4]   

        self.x3 = (self.phase[0]+self.phase[1])-(self.phase[2]+self.phase[3])
        self.y3 = (self.phase[0]+self.phase[2])-(self.phase[1]+self.phase[3])
        self.z3 = quad_sum
        ## reshape and extract xyz data
        ## assuming the data contains the correct amount of samples ordered in a correct way
        ## in the reprocessor a testing prcedure has to be implemented
        ## pos_data contains:
        ## [x_lf_2, y_lf_2, x_lf, y_lf, z_lf, sync, x_fb, y_fb, z_fb, time1, time2]
        self.xyz = pos_data.reshape(-1,11).T[2:5]
        
        #placeholders for later analysis
        self.diag_pos_data = []
        self.cant_data = []
        self.electrode_data = []
        self.other_data = []

        #Conditions under which data is taken
        self.time = "Time not loaded"
        #loads time at end of file
        self.temps = []
        self.pressures = {} # loads to dict with keys different gauges
        self.stage_settings = {} # loads to dict. Look at config.py for keys
        self.electrode_settings = {} # loads to dict. The key "dc_settings" gives\
                # the dc value on electrodes 0-6. The key "driven_electrodes"
                # is a list where the electrode index is 1 if the electrode
                # is driven and 0 otherwise
        self.cant_calibrated = False

    def welch_psd(self, str_axis, res = 2**12):

        x = []
        if str_axis=='x':
            x = self.xyz[0]
        elif str_axis=='y':
            x = self.xyz[1]
        elif str_axis=='z':
            x = self.xyz[2]
        else:
            print('Must choose x,y,or z')
       
        #ypsd, freqs = matplotlib.mlab.psd(data_det[4], Fs = fsamp, NFFT = res)
        freq, psd = welch(x, fs = self.fsamp, nfft = res)
        return freq, psd

    
    def psd(self, str_axis, res = 2**12):
        x = [] 
        if str_axis=='x':
            x = self.xyz[0]
        elif str_axis=='y':
            x = self.xyz[1]
        elif str_axis=='z':
            x = self.xyz[2]
        else:
            print('Must choose x,y,or z')

        fft = np.abs(np.fft.rfft(x))**2 
        freq = np.fft.rfftfreq(len(x), d=1./self.fsamp)

        return freq, fft

    
    def psd2(self, str_axis, res = 2**12):
        x = [] 
        if str_axis=='x':
            x = self.x2
        elif str_axis=='y':
            x = self.y2
        elif str_axis=='z':
            x = self.z2
        else:
            print('Must choose x,y,or z')

        fft = np.abs(np.fft.rfft(x))**2 
        freq = np.fft.rfftfreq(len(x), d=1./self.fsamp)

        return freq, fft

    def response_at_freq(self, str_axis,drive_freq,bandwidth=0):

        x = [] 
        if str_axis=='x':
            x = self.xyz[0]
        elif str_axis=='y':
            x = self.xyz[1]
        elif str_axis=='z':
            x = self.xyz[2]
        else:
            print('Must choose x,y,or z')
        
        if (bandwidth==0):
            bandwidth = 1
        b, a = signal.butter(3, [2.*(drive_freq-bandwidth/2.)/self.fsamp, 2.*(drive_freq+bandwidth/2.)/self.fsamp ], btype = 'bandpass')
        responsefilt = signal.filtfilt(b, a, x)

        return responsefilt


    def response_at_freq2(self, str_axis,drive_freq,bandwidth=0,first=0,last=0):

        x = [] 
        if str_axis=='x':
            x = self.x2
        elif str_axis=='y':
            x = self.y2
        elif str_axis=='z':
            x = self.z2
        else:
            print('Must choose x,y,or z')

        if last!=0:
            x = x[:last]
        if first!=0:
            x = x[first:]
        
        if (bandwidth==0):
            bandwidth = 1
        b, a = signal.butter(3, [2.*(drive_freq-bandwidth/2.)/self.fsamp, 2.*(drive_freq+bandwidth/2.)/self.fsamp ], btype = 'bandpass')
        responsefilt = signal.filtfilt(b, a, x)

        return responsefilt
    
    def response_at_freq3(self, str_axis,drive_freq,bandwidth=0,first=0,last=0):

        x = [] 
        if str_axis=='x':
            x = self.x3
        elif str_axis=='y':
            x = self.y3
        elif str_axis=='z':
            x = self.z2
        else:
            print('Must choose x,y,or z')
        
        x = x - np.mean(x)
        if last!=0:
            x = x[:last]
        if first!=0:
            x = x[first:]
        
        if (bandwidth==0):
            bandwidth = 1
        b, a = signal.butter(3, [2.*(drive_freq-bandwidth/2.)/self.fsamp, 2.*(drive_freq+bandwidth/2.)/self.fsamp ], btype = 'bandpass')
        responsefilt = signal.filtfilt(b, a, x)


        return responsefilt


