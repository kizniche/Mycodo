# coding=utf-8
#
# From https://github.com/wlong007/psypy
#
# The MIT License (MIT)
#
# Copyright (c) 2015 wlong007
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.

import math as m

# All functions expect base SI units for any arguments given
# DBT   - Dry bulb temperature          - Kelvins, K
# DPT   - Dew point temperature         - Kelvins, K
# H     - Specific enthalpy             - kiloJoules per kilogram, kJ/kg
# P     - Atmospheric pressure          - Pascals, Pa
# Pw    - Water vapor partial pressure  - Pascals, Pa
# RH    - Relative humidity             - Decimal (i.e. not a percentage)
# V     - Specific volume               - Cubic meters per kilogram, m^3/kg
# W     - Humidity ratio                - kilograms per kilograms, kg/kg
# WBT   - Wet bulb temperature          - Kelvins, K

# Minimum dry bulb temperature
Min_DBT=273.15
# Maximum dry bulb temperature
Max_DBT=473.15
# Convergence tolerance
TOL=0.0005

def __DBT_H_RH_P(H, RH, P):
    [DBTa, DBTb]=[Min_DBT, Max_DBT]
    DBT=(DBTa+DBTb)/2
    while DBTb-DBTa>TOL:
        ya=__W_DBT_RH_P(DBTa, RH, P)-__W_DBT_H(DBTa, H)
        y=__W_DBT_RH_P(DBT, RH, P)-__W_DBT_H(DBT, H)
        if __is_positive(y)==__is_positive(ya):
            DBTa=DBT
        else:
            DBTb=DBT
        DBT=(DBTa+DBTb)/2
    return DBT

def __DBT_H_V_P(H, V, P):
    [DBTa, DBTb]=[Min_DBT, Max_DBT]
    DBT=(DBTa+DBTb)/2
    while DBTb-DBTa>TOL:
        ya=__W_DBT_V_P(DBTa, V, P)-__W_DBT_H(DBTa, H)
        y=__W_DBT_V_P(DBT, V, P)-__W_DBT_H(DBT, H)
        if __is_positive(y)==__is_positive(ya):
            DBTa=DBT
        else:
            DBTb=DBT
        DBT=(DBTa+DBTb)/2
    return DBT

def __DBT_H_W(H, W):
    [DBTa, DBTb]=[Min_DBT, Max_DBT]
    DBT=(DBTa+DBTb)/2
    while DBTb-DBTa>TOL:
        ya=W-__W_DBT_H(DBTa, H)
        y=W-__W_DBT_H(DBT, H)
        if __is_positive(y)==__is_positive(ya):
            DBTa=DBT
        else:
            DBTb=DBT
        DBT=(DBTa+DBTb)/2
    return DBT

def __DBT_H_WBT_P(H, WBT, P):
    [DBTa, DBTb]=[Min_DBT, Max_DBT]
    DBT=(DBTa+DBTb)/2
    while DBTb-DBTa>TOL:
        ya=__W_DBT_WBT_P(DBTa, WBT, P)-__W_DBT_H(DBTa, H)
        y=__W_DBT_WBT_P(DBT, WBT, P)-__W_DBT_H(DBT, H)
        if __is_positive(y)==__is_positive(ya):
            DBTa=DBT
        else:
            DBTb=DBT
        DBT=(DBTa+DBTb)/2
    return DBT

def __DBT_RH_V_P(RH, V, P):
    [DBTa, DBTb]=[Min_DBT, Max_DBT]
    DBT=(DBTa+DBTb)/2
    while DBTb-DBTa>TOL:
        ya=__W_DBT_RH_P(DBTa, RH, P)-__W_DBT_V_P(DBTa, V, P)
        y=__W_DBT_RH_P(DBT, RH, P)-__W_DBT_V_P(DBT, V, P)
        if __is_positive(y)==__is_positive(ya):
            DBTa=DBT
        else:
            DBTb=DBT
        DBT=(DBTa+DBTb)/2
    return DBT

def __DBT_RH_W_P(RH, W, P):
    [DBTa, DBTb]=[Min_DBT, Max_DBT]
    DBT=(DBTa+DBTb)/2
    while DBTb-DBTa>TOL:
        ya=__W_DBT_RH_P(DBTa, RH, P)-W
        y=__W_DBT_RH_P(DBT, RH, P)-W
        if __is_positive(y)==__is_positive(ya):
            DBTa=DBT
        else:
            DBTb=DBT
        DBT=(DBTa+DBTb)/2
    return DBT

def __DBT_RH_WBT_P(RH, WBT, P):
    [DBTa, DBTb]=[Min_DBT, Max_DBT]
    DBT=(DBTa+DBTb)/2
    while DBTb-DBTa>TOL:
        ya=__W_DBT_WBT_P(DBTa, WBT, P)-__W_DBT_RH_P(DBTa, RH, P)
        y=__W_DBT_WBT_P(DBT, WBT, P)-__W_DBT_RH_P(DBT, RH, P)
        if __is_positive(y)==__is_positive(ya):
            DBTa=DBT
        else:
            DBTb=DBT
        DBT=(DBTa+DBTb)/2
    return DBT

def __DBT_V_W_P(V, W, P):
    [DBTa, DBTb]=[Min_DBT, Max_DBT]
    DBT=(DBTa+DBTb)/2
    while DBTb-DBTa>TOL:
        ya=W-__W_DBT_V_P(DBTa, V, P)
        y=W-__W_DBT_V_P(DBT, V, P)
        if __is_positive(y)==__is_positive(ya):
            DBTa=DBT
        else:
            DBTb=DBT
        DBT=(DBTa+DBTb)/2
    return DBT

def __DBT_V_WBT_P(V, WBT, P):
    [DBTa, DBTb]=[Min_DBT, Max_DBT]
    DBT=(DBTa+DBTb)/2
    while DBTb-DBTa>TOL:
        ya=__W_DBT_WBT_P(DBTa, WBT, P)-__W_DBT_V_P(DBTa, V, P)
        y=__W_DBT_WBT_P(DBT, WBT, P)-__W_DBT_V_P(DBT, V, P)
        if __is_positive(y)==__is_positive(ya):
            DBTa=DBT
        else:
            DBTb=DBT
        DBT=(DBTa+DBTb)/2
    return DBT

def __DBT_W_WBT_P(W, WBT, P):
    [DBTa, DBTb]=[Min_DBT, Max_DBT]
    DBT=(DBTa+DBTb)/2
    while DBTb-DBTa>TOL:
        ya=__W_DBT_WBT_P(DBTa, WBT, P)-W
        y=__W_DBT_WBT_P(DBT, WBT, P)-W
        if __is_positive(y)==__is_positive(ya):
            DBTa=DBT
        else:
            DBTb=DBT
        DBT=(DBTa+DBTb)/2
    return DBT

# ASHRAE 2009 Chapter 1 Equation 39
def __DPT_Pw(Pw):
    Pw=Pw/1000
    C14=6.54
    C15=14.529
    C16=0.7389
    C17=0.09486
    C18=0.4569
    a=m.log(Pw)
    return (C14+C15*a+C16*a**2+C17*a**3+C18*Pw**0.1984)+273.15

# ASHRAE 2009 Chapter 1 Equation 32
def __H_DBT_W(DBT, W):
    if __valid_DBT(DBT):
        DBT=DBT-273.15
        return 1.006*DBT+W*(2501+1.86*DBT)

def __is_positive(x):
    if x>0:
        return True
    else:
        return False

# ASHRAE 2009 Chapter 1 Equation 22
def __Pw_W_P(W, P):
    return W*P/(W+0.621945)

# ASHRAE 2009 Chapter 1 Equation 6
def __Pws(DBT):
    if __valid_DBT(DBT):
        C8=-5.8002206*10**3
        C9=1.3914993
        C10=-4.8640239*10**-2
        C11=4.1764768*10**-5
        C12=-1.4452093*10**-8
        C13=6.5459673
        return m.exp(C8/DBT+C9+C10*DBT+C11*DBT**2+C12*DBT**3+C13*m.log(DBT))

def state(prop1, prop1val, prop2, prop2val, P):
    if prop1==prop2:
        print("Properties must be independent.")
        return
    prop=["DBT","WBT","RH","W","V","H"]
    if prop1 not in prop or prop2 not in prop:
        print("Valid property must be given.")
        return
    prop1i=prop.index(prop1)
    prop2i=prop.index(prop2)
    if prop1i<prop2i:
        cd1=prop1
        cd1val=prop1val
        cd2=prop2
        cd2val=prop2val
    else:
        cd1=prop2
        cd1val=prop2val
        cd2=prop1
        cd2val=prop1val
    if cd1=="DBT":
        DBT=cd1val
        if cd2=="WBT":
            WBT=cd2val
            W=__W_DBT_WBT_P(DBT, WBT, P)
            H=__H_DBT_W(DBT, W)
            RH=__RH_DBT_W_P(DBT, W, P)
            V=__V_DBT_W_P(DBT, W, P)
        elif cd2=="RH":
            RH=cd2val
            W=__W_DBT_RH_P(DBT, RH, P)
            H=__H_DBT_W(DBT, W)
            V=__V_DBT_W_P(DBT, W, P)
            WBT=__WBT_DBT_W_P(DBT, W, P)
        elif cd2=="W":
            W=cd2val
            H=__H_DBT_W(DBT, W)
            RH=__RH_DBT_W_P(DBT, W, P)
            V=__V_DBT_W_P(DBT, W, P)
            WBT=__WBT_DBT_W_P(DBT, W, P)
        elif cd2=="V":
            V=cd2val
            W=__W_DBT_V_P(DBT, V, P)
            H=__H_DBT_W(DBT, W)
            RH=__RH_DBT_W_P(DBT, W, P)
            WBT=__WBT_DBT_W_P(DBT, W, P)
        elif cd2=="H":
            H=cd2val
            W=__W_DBT_H(DBT, H)
            RH=__RH_DBT_W_P(DBT, W, P)
            V=__V_DBT_W_P(DBT, W, P)
            WBT=__WBT_DBT_W_P(DBT, W, P)
    elif cd1=="WBT":
        WBT=cd1val
        if cd2=="RH":
            RH=cd2val
            DBT=__DBT_RH_WBT_P(RH, WBT, P)
            W=__W_DBT_RH_P(DBT, RH, P)
            H=__H_DBT_W(DBT, W)
            V=__V_DBT_W_P(DBT, W, P)
        elif cd2=="W":
            W=cd2val
            DBT=__DBT_W_WBT_P(W, WBT, P)
            H=__H_DBT_W(DBT, W)
            RH=__RH_DBT_W_P(DBT, W, P)
            V=__V_DBT_W_P(DBT, W, P)
        elif cd2=="V":
            V=cd2val
            DBT=__DBT_V_WBT_P(V, WBT, P)
            W=__W_DBT_V_P(DBT, V, P)
            H=__H_DBT_W(DBT, W)
            RH=__RH_DBT_W_P(DBT, W, P)
        elif cd2=="H":
            H=cd2val
            DBT=__DBT_H_WBT_P(H, WBT, P)
            W=__W_DBT_H(DBT, H)
            RH=__RH_DBT_W_P(DBT, W, P)
            V=__V_DBT_W_P(DBT, W, P)
    elif cd1=="RH":
        RH=cd1val
        if cd2=="W":
            W=cd2val
            DBT=__DBT_RH_W_P(RH, W, P)
            H=__H_DBT_W(DBT, W)
            V=__V_DBT_W_P(DBT, W, P)
            WBT=__WBT_DBT_W_P(DBT, W, P)
        elif cd2=="V":
            V=cd2val
            DBT=__DBT_RH_V_P(RH, V, P)
            W=__W_DBT_RH_P(DBT, RH, P)
            H=__H_DBT_W(DBT, W)
            WBT=__WBT_DBT_W_P(DBT, W, P)
        elif cd2=="H":
            H=cd2val
            DBT=__DBT_H_RH_P(H, RH, P)
            W=__W_DBT_RH_P(DBT, RH, P)
            V=__V_DBT_W_P(DBT, W, P)
            WBT=__WBT_DBT_W_P(DBT, W, P)
    elif cd1=="W":
        W=cd1val
        if cd2=="V":
            V=cd2val
            DBT=__DBT_V_W_P(V, W, P)
            H=__H_DBT_W(DBT, W)
            RH=__RH_DBT_W_P(DBT, W, P)
            WBT=__WBT_DBT_W_P(DBT, W, P)
        elif cd2=="H":
            H=cd2val
            DBT=__DBT_H_W(H, W)
            RH=__RH_DBT_W_P(DBT, W, P)
            V=__V_DBT_W_P(DBT, W, P)
            WBT=__WBT_DBT_W_P(DBT, W, P)
    elif cd1=="V":
        V=cd1val
        H=cd2val
        DBT=__DBT_H_V_P(H, V, P)
        W=__W_DBT_V_P(DBT, V, P)
        RH=__RH_DBT_W_P(DBT, W, P)
        WBT=__WBT_DBT_W_P(DBT, W, P)
    return [DBT, H, RH, V, W, WBT]

# ASHRAE 2009 Chapter 1 Equation 22 and Equation 24
def __RH_DBT_W_P(DBT, W, P):
    if __valid_DBT(DBT):
        return W*P/((0.621945+W)*__Pws(DBT))

# ASHRAE 2009 Chapter 1 Equation 28
def __V_DBT_W_P(DBT, W, P):
    if __valid_DBT(DBT):
        return 287.042*DBT*(1+1.607858*W)/P

# ASHRAE 2009 Chapter 1 Equation 32
def __W_DBT_H(DBT, H):
    if __valid_DBT(DBT):
        DBT=DBT-273.15
        return (H-1.006*DBT)/(2501+1.86*DBT)

# ASHRAE 2009 Chapter 1 Equation 22 and Equation 24
def __W_DBT_RH_P(DBT, RH, P):
    if __valid_DBT(DBT):
        Pw=RH*__Pws(DBT)
        return 0.621945*Pw/(P-Pw)

# ASHRAE 2009 Chapter 1 Equation 28
def __W_DBT_V_P(DBT, V, P):
    if __valid_DBT(DBT):
        return (P*V-287.042*DBT)/(1.607858*287.042*DBT)

# ASHRAE 2009 Chapter 1 Equation 35
def __W_DBT_WBT_P(DBT, WBT, P):
    if __valid_DBT(DBT):
        DBT=DBT-273.15
        WBT=WBT-273.15
        return ((2501-2.326*WBT)*__W_DBT_RH_P(WBT+273.15,1,P)-1.006*(DBT-WBT))/\
               (2501+1.86*DBT-4.186*WBT)

# ASHRAE 2009 Chapter 1 Equation 35
def __WBT_DBT_W_P(DBT, W, P):
    if __valid_DBT(DBT):
        WBTa=__DPT_Pw(__Pw_W_P(W, P))
        WBTb=DBT
        WBT=(WBTa+WBTb)/2
        while WBTb-WBTa>TOL:
            Ws=__W_DBT_WBT_P(DBT, WBT, P)
            if W>Ws:
                WBTa=WBT
            else:
                WBTb=WBT
            WBT=(WBTa+WBTb)/2
        return WBT

def __valid_DBT(DBT):
    if Min_DBT<=DBT<=Max_DBT:
        return True
    else:
        return False
