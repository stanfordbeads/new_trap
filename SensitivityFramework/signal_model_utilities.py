
# coding: utf-8

# ### Notebook to create the utility file for the signal model input ###

#### Import
import numpy as np
import pickle as pkl
import scipy.interpolate as interp
import scipy, sys, time
from bisect import bisect_left
sys.path.append('/home/analysis_user/New_trap_code/Tools/')
import BeadDataFile
from discharge_tools import load_dir
lambdas = np.logspace(-6.3, -3, 100)
sep_list = np.arange(1.0e-6,100.0e-6,1.0e-6)

### define functions


def take_closest(myList, myNumber):
    """
    Assumes myList is sorted. Returns closest value to myNumber.

    If two numbers are equally close, return the smallest number.
    """
    pos = bisect_left(myList, myNumber)
    if pos == 0:
        return myList[0]
    if pos == len(myList):
        return myList[-1]
    before = myList[pos - 1]
    after = myList[pos]
    if after - myNumber < myNumber - before:
        return after
    else:
        return before



### part 1:load files

## load the data dictionary file (its usually of the form results_dic[rbead][sep][height][yuklambda])

def load_file(separation,lambda_par=1e-5,alpha=1):
    try:
        res_dict_side_by_side = pkl.load( open('/home/analysis_user/New_trap_code/SensitivityFramework/results/simulation/rbead_2.4e-06_sep_%4.1e_height_0.p' %(separation), 'rb'))
    except:
        print("Your choice of separation is not existing")
        val2 = take_closest(sep_list, separation)
        separation=val2  
        res_dict_side_by_side = pkl.load( open('/home/analysis_user/New_trap_code/SensitivityFramework/results/simulation/rbead_2.4e-06_sep_%4.1e_height_0.p' %(separation), 'rb'))

        print("Taking %4.1e for separation" %val2)
        
    try:
        res_dict_side_by_side[2.4e-6][separation][0][lambda_par][0]
    except:
        print("Your choice of lambda is not existing")
        val = take_closest(lambdas, lambda_par)
        lambda_par=val  
        print("Taking %2.2e for lambda" %val)
    for item in res_dict_side_by_side[2.4e-6]:
        print("A separation of %2.2e is selected" %item)
        separation=item # as separation is saved differently here than in the file name
    force_x = res_dict_side_by_side[2.4e-6][separation][0][lambda_par][0] # force in direction of the sphere
    force_y = res_dict_side_by_side[2.4e-6][separation][0][lambda_par][1] # force in direction perpendicular to the sphere
    force_z = res_dict_side_by_side[2.4e-6][separation][0][lambda_par][2] # force in z-direction
    force_x_yuk = alpha*res_dict_side_by_side[2.4e-6][separation][0][lambda_par][3] # force by the yukawa potential , x
    force_y_yuk = alpha*res_dict_side_by_side[2.4e-6][separation][0][lambda_par][4] # force by the yukawa potential , y
    force_z_yuk = alpha*res_dict_side_by_side[2.4e-6][separation][0][lambda_par][5] # force by the yukawa potential , z
    pos = res_dict_side_by_side["posvec"] # get the position of the bead from the dictionary
    force_list = [force_x,force_y,force_z,force_x_yuk,force_y_yuk,force_z_yuk]
    return pos,force_list

### part 2: conversion of movement between the domains
# determine the center position of the attractor at a given time

def force_at_position(direction,pos,force_list,yuk_or_grav="yuk"):
    if(yuk_or_grav=="yuk"):
        if(direction=="x"):
            force_vec = force_list[3]
        if(direction=="y"):
            force_vec = force_list[4]
        if(direction=="z"):
            force_vec = force_list[5]
    if(yuk_or_grav=="grav"):
        if(direction=="x"):
            force_vec = force_list[0]
        if(direction=="y"):
            force_vec = force_list[1]
        if(direction=="z"):
            force_vec = force_list[2]        
    return force_vec


int_time =1 
sampling_frequency = 5000 # should be 5000 
time = np.arange(0,int_time,1/sampling_frequency) # make a time array

# sine
def position_at_time_sin_function(stroke,time,frequency): 
    pos_at_time = stroke/2*np.sin(2*np.pi*time*frequency)
    return pos_at_time

# triang
def position_at_time_tri_function(stroke,time,frequency,width=0.5):
    pos_at_time=stroke/2*signal.sawtooth(2 * np.pi * frequency * time+np.pi/2,width=width)
    return pos_at_time

# determine the force for a given point in time using the transformation to position

## sinusoidal movement
def force_at_a_time_sin_function(stroke,time,frequency,pos_vec,force_vec):
    osci_pos = position_at_time_sin_function(stroke,time,frequency)
    return np.interp(osci_pos,pos_vec,force_vec, left=None, right=None, period=None)

## triangle movement
def force_at_a_time_tri_function(stroke,time,frequency,pos_vec,force_vec,width=0.5):
    osci_pos_triang =  position_at_time_tri_function(stroke,time,frequency,width=width)
    return np.interp(osci_pos_triang,pos_vec,force_vec, left=None, right=None, period=None)

# use those two for most of your applications

def force_vs_position(separation,direction,lambda_par,yuk_or_grav="yuk",alpha=1):
    pos,force_list = load_file(separation,lambda_par,alpha)
    force = force_at_position(direction,pos,force_list,yuk_or_grav)
    return pos,force

def force_vs_time(separation,stroke,frequency,direction,lambda_par,yuk_or_grav="yuk",alpha=1):
    pos,force_list = load_file(separation,lambda_par,alpha)
    force_vec = force_at_position(direction,pos,force_list,yuk_or_grav="yuk")
    force = force_at_a_time_sin_function(stroke,time,frequency,pos,force_vec)
    return time,force