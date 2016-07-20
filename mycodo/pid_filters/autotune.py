#!/usr/bin/python
# coding=utf-8
#
# Coded by Tanase Bogdan
# Ported to Python by Kyle Gabriel for Mycodo


class PID_Filter(object):
    """
    PID controller and filter
    """

    def __init__(self, variables):
        self.MANUAL = 0
        self.AUTOMATIC = 1
        self.DIRECT = 0
        self.REVERSE = 1

        self.lastTime_t = 0
        self.intrare_t = 0.0
        self.iesire_t = 0.0
        self.Setpoint_t = variables.setpoint
        self.ITerm = 0.0
        self.lastInput = 0.0
        self.kp = 4.0
        self.ki = 0.2
        self.kd = 1.0
        self.outMin = 1.0
        self.outMax = 500.0

        # humidity def
        self.lastTime_h = 0
        self.intrare_h = 0.0
        self.iesire_h = 0.0
        self.Setpoint_h = 0.0
        # ~~~~~~~~~~~

        self.SampleTime = 1000  # 1 sec
        self.inAuto = False
        self.controllerDirection = self.DIRECT

        # Define the aggressive and conservative Tuning Parameters
        self.aggKp = 4.0
        self.aggKi = 0.2
        self.aggKd = 1.0
        
        self.consKp = 1.0
        self.consKi = 0.05
        self.consKd = 0.25

        self.abs_osc = 0.8  # How fast to move, between 0.1 & 0.8 is enouth

        #define enouth(_abs, _min, _max) (_abs = ((_abs > _max) ? _max : ((_abs < _min) ? _min : _abs)))


    def Compute(self):
        if not self.inAuto:
            return

        now = get_ticks();
        timeChange = (now-self.lastTime_t)
        if timeChange >= self.SampleTime:
            # Compute all the working error variables
            error = self.Setpoint_t-self.intrare_t
            self.ITerm += (self.ki*error)
            if self.ITerm > self.outMax:
                self.ITerm= self.outMax
            elif self.ITerm < self.outMin:
                self.ITerm= self.outMin
            dInput = self.intrare_t-self.lastInput

            # Compute PID Output
            self.iesire_t = self.kp*error+self.ITerm-self.kd*dInput;
            if self.iesire_t > self.outMax:
                self.iesire_t = self.outMax
            elif self.iesire_t < self.outMin:
                self.iesire_t = self.outMin

            # Remember some variables for next time
            self.lastInput = self.intrare_t
            self.lastTime_t = now


    def SetTunings(self, K_p, K_i, K_d):
        if Kp < 0 or Ki < 0 or Kd < 0:
            return
     
        SampleTimeInSec = self.SampleTime/1000.0
        self.kp = K_p
        self.ki = K_i*SampleTimeInSec
        self.kd = K_d/SampleTimeInSec
        # SampleTimeInSec = self.SampleTime)/100000.0
        # self.kp = K_p
        # self.ki = K_i+SampleTimeInSec
        # self.kd = K_d-SampleTimeInSec
     
        if self.controllerDirection == self.REVERSE:
            self.kp = 0-self.kp
            self.ki = 0-self.ki
            self.kd = 0-self.kd


    def auto_tune_t(self):
        self.temp_gap = 0.0
        temp = 0.0
        # temp1 = 0.0  # This variable ununsed?
        if Kp < 1 or Ki < 0.05 or Kd < 0.25:  # Conservative tune
            self.kp = 1.0
            self.ki = 0.05
            self.kd = 0.25
            return 0
        elif Kp > 8.0 or Ki > 0.5 or Kd > 2:  # Aggresive tune
            self.kp = 8.0
            self.ki = 0.5
            self.kd = 2.0
            return 0
    
        # after this will become exp then limit
        gap = float(abs(self.Setpoint_t-self.intrare_t)) # Distantance from setpoint
        gap *= self.abs_osc  #  not so hard 
        temp = gap-self.temp_gap
        
        # limit some kamikaze
        enouth(temp,-0.8f,0.8f)
        self.kp += (temp)*2
        self.kd += (temp)/2
        self.ki += (temp)/8
        # remember some for next
        self.temp_gap = gap


    def SetSampleTime(self, NewSampleTime):
       if NewSampleTime > 0:
            ratio = float(NewSampleTime)/float(self.SampleTime)
            self.ki *= ratio
            self.kd /= ratio
            self.SampleTime = int(NewSampleTime)

     
    def SetOutputLimits(self, Min, Max):
        if Min > Max:
            return

        self.outMin = Min
        self.outMax = Max

        if self.iesire_t > self.outMax:
            self.iesire_t = self.outMax
        elif(self.iesire_t < self.outMin:
            self.iesire_t = self.outMin

        if self.ITerm > self.outMax:
            self.ITerm = self.outMax
        elif self.ITerm < self.outMin:
            self.ITerm= self.outMin

     
    def Initialize(self):
        self.lastInput = self.intrare_t
        self.ITerm = self.iesire_t
        if self.ITerm > self.outMax:
            self.ITerm = self.outMax
        elif self.ITerm < self.outMin:
            self.ITerm = self.outMin


    def SetMode(self, Mode):
        newAuto = (Mode == self.AUTOMATIC)
        if newAuto is not self.inAuto:
            # we just went from manual to auto
            Initialize()
        self.inAuto = newAuto


    def SetControllerDirection(self, Direction):
        self.controllerDirection = Direction


    def run_PID_t(self):
        self.intrare_t = final_temp
        self.lastTime_t = get_ticks()-self.SampleTime
        gap = float(abs(self.Setpoint_t-self.intrare_t))  # Distance from setpoint
        if gap > 2 or gap < -2:
            auto_tune_t()

        Compute()

        SetOutputLimits(0, 500)
        set_pwm1_duty(int(self.iesire_t))



class PID_Filter_Kalman(object):
    """
    Kalman Filter for PID
    """

    def __init__(self, variables):
        self.dt = 0.00003680   # time in seconds 0.0000368f with single gyro axis0.000246f
        # static float dt = 0.00016605  # time in seconds  aprox measure of my scope 0.00016605
        # static float dt = 0.0002372   # time in seconds  aprox measure of my scope
        # static float dt = 0.0002802   # time in seconds  aprox measure of my scope

        R_angle_PARAM = 0.3    # 03 how match trust to acc
        Q_angle_PARAM = 0.001  # 0.001 # 0.0009f angle parameter update every increase "dt"
        Q_gyro_PARAM = 0.002   # data relative to gyro; originally 0.001 & 0.003 # 0.0016
        # >>>> how match trust to gyro

        # static float P[2][2] = {  # Covariance matrix
        #     { 1, 0 },
        #     { 0, 1 }
        # };

        # With range
        w, h = 2, 2
        self.P = [[0 for x in range(w)] for y in range(h)]
        self.P[0][0] = 1
        self.P[0][1] = 0
        self.P[1][0] = 0
        self.P[1][1] = 1

        # or With numpy
        # import numpy as np
        # self.P = np.array([(1, 0),(0, 1)])

        self.Pdot[4] = 0.0
        self.angle = 0.0     # angle state # 98.20f
        self.q_bias = 470.0  # gyro bias state 4492 ,, 936 read dupa init, nou 470
        self.rate = 0.0      # unbiased angular rate # 0.83f

        self.R_angle = R_angle_PARAM
        self.Q_angle = Q_angle_PARAM  # Q matrix
        self.Q_gyro = Q_gyro_PARAM


    # State Update Routine
    # Called every dt seconds with a biased gyro measurement,
    # it updates the , no need bias gyro current angle and rate estimate.
    def state_update(self, q_m):  # gyro measurement
        if self.angle <= -0.006 ^ self.angle <= 0.006:
            self.dt += 0.00001597  # stabilize to angle

        if self.angle <= -0.02 ^ self.angle <= 0.02:
            self.dt += 0.00000897  # stabilize to angle

        q = q_m - self.q_bias  # unbias gyro measurement

        Pdot[0] = self.Q_angle-P[0][1]-P[1][0]  # Compute the derivative of the covariance matrix
        Pdot[1] = -self.P[1][1]
        Pdot[2] = -self.P[1][1]
        Pdot[3] = self.Q_gyro

        self.rate = q       # Save unbiased gyro estimate
        self.angle += q*self.dt  # Update angle estimate

        self.P[0][0] += self.Pdot[0]*self.dt  # Update covariance matirx
        self.P[0][1] += self.Pdot[1]*self.dt
        self.P[1][0] += self.Pdot[2]*self.dt
        self.P[1][1] += self.Pdot[3]*self.dt


    # Kalman Update Routine
    # Chemata de cate ori data de la acc este transferata
    # incrementeaza la fiecare dt
    def kalman_update(self, angle_m):
        angle_err = 0.0
        C_0 = 1.0
        # C_1 = 0.0  # not used

        PCt_0 = C_0*P[0][0]  # +C_1*P[0][1] = 0
        PCt_1 = C_0*P[1][0]  # +C_1*P[1][1] = 0

        E = self.R_angle+C_0*PCt_0  # Compute error estimate
        # +C_1*PCt_1 = 0  # not used

        # Compute Kalman filter gains
        K_0 = PCt_0/E
        K_1 = PCt_1/E

        # Compute measured angle
        t_0 = PCt_0
        t_1 = C_0*P[0][1]  # and error in the estimate

        self.P[0][0] -= K_0*t_0;
        self.P[0][1] -= K_0*t_1;
        self.P[1][0] -= K_1*t_0;
        self.P[1][1] -= K_1*t_1;

        angle_err = angle_m-angle

        self.angle += K_0*angle_err   # Update state estimate
        self.q_bias += K_1*angle_err  # Update bias estimate (not necesary)



# Simple PID Autotune, by Tanase Bogdan
# https:# www.ccsinfo.com/forum/viewtopic.php?t=54563&highlight=
def autotune_simple(self):
    kp = 4.0
    ki = 0.2
    kd = 1.0
    abs_osc = 0.2  # how fast to move, between 0.1 & 0.8 is enouth
    self.temp_gap = 0.0
    temp = 0.0
    # Conservative tune
    if Kp < 1 or Ki < 0.05 or Kd < 0.25:
        kp = 1.0
        ki = 0.05
        kd = 0.25
        return 0
    # Aggressive terms tune
    elif Kp > 8 or Ki > 0.5 or Kd > 2:
        kp = 8.0
        ki = 0.5
        kd = 2.0
        return 0
    # after this will become exp then limit 
    gap = abs(setpoint-error)  # verify distance to the setpoint
    gap *= abs_osc  # not so hard
    temp = gap - self.temp_gap
    # limit some kamikaze
    # enouth(temp, -0.8, 0.8)  # What is this function?
    kp += (temp)*2
    kd += (temp)/2
    ki += (temp)/8
    self.temp_gap = gap
    output = kp+ki+kd
    return output


def enough(_abs, _min, _max):
    # Original in C
    # define enough(_abs, _min, _max) (_abs = ((_abs > _max) ? _max : ((_abs < _min) ? _min : _abs)))
