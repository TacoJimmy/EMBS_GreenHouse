'''
Created on 20220812
@author: infilink_Jimmy
'''
import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp
from modbus_tk import modbus_rtu
import struct
import paho.mqtt.client as mqtt
import random
import json  
import datetime 
import time
import schedule
import serial
import math

def ReadFloat(*args,reverse=False):
    for n,m in args:
        n,m = '%04x'%n,'%04x'%m
    if reverse:
        v = n + m
    else:
        v = m + n
    y_bytes = bytes.fromhex(v)
    y = struct.unpack('!f',y_bytes)[0]
    y = round(y,6)
    return y

def conver32(LSB,MSB):
    conv32value = LSB + ( MSB << 16 )
    return (conv32value)

def GetVantage2Data(ComPort,BbaudRate,ID):
    try:
        master = modbus_rtu.RtuMaster(serial.Serial(port=ComPort, baudrate=BbaudRate, bytesize=8, parity='N', stopbits=1, xonxoff=0))
        master.set_timeout(5.0)
        master.set_verbose(True)
        weather = master.execute(ID, cst.READ_HOLDING_REGISTERS, 0, 11)
        OutHumi = master.execute(ID, cst.READ_HOLDING_REGISTERS, 18, 1)
        RainRate = master.execute(ID, cst.READ_HOLDING_REGISTERS, 23, 1)
        UVIndex = master.execute(ID, cst.READ_HOLDING_REGISTERS, 24, 1)
        SolarRadi = master.execute(ID, cst.READ_HOLDING_REGISTERS, 25, 1)
        TimeofSun = master.execute(ID, cst.READ_HOLDING_REGISTERS, 51, 2)
        CommsStatus = master.execute(ID, cst.READ_HOLDING_REGISTERS, 59, 1)
        Barometer = round(weather[3]/1000,3)
        InTemp = round((weather[4]-32)*0.056,1)
        InHumi = round(weather[5])
        OutTemp = round((weather[6]-32)*0.056,1)
        OutHumi = round(OutHumi[0])
        WindSpeed = round(weather[7])
        AveWindSpeed = round(weather[8])
        WindDirection = round(weather[9])
        RainRateload =  round(RainRate[0]*0.01)
        UVIndexload = UVIndex[0]*0.1
        TimeofSunrisemin = TimeofSun[0]%100
        TimeofSunrisehr = math.floor(TimeofSun[0]/100)
        TimeofSunsetmin = TimeofSun[1]%100
        TimeofSunsethr = math.floor(TimeofSun[1]/100)
        
        
        
        payload = {"Barometer":Barometer,
                   "InsideTemperature":InTemp, 
                   "InsideHumidity":InHumi, 
                   "OutsideTemperature":OutTemp,
                   "OutsideHumidity":OutHumi,
                   "WindSpeed":WindSpeed,
                   "AveWindSpeed":AveWindSpeed,
                   "WindDirection":WindDirection,
                   "RainRate":RainRateload,
                   "UVIndex":UVIndexload,
                   "SolarRadiation":SolarRadi[0],
                   "TimeofSunrisemin":TimeofSunrisemin,
                   "TimeofSunrisehr":TimeofSunrisehr,
                   "TimeofSunsetmin":TimeofSunsetmin,
                   "TimeofSunsethr":TimeofSunsethr,
                   "CommsStatus":CommsStatus[0]
                   }
        
        time.sleep(0.5)
        
        
    except:
        payload = {"CommsStatus":0}
    
    return (payload)

def getMainPower(HOST_Addr):
    
    try:
        MainSysPower = [0,0,0,0,0,0,0,0,0,0,0,0]
        master = modbus_tcp.TcpMaster(host=HOST_Addr)
        master.set_timeout(5.0)
        demo1 = master.execute(1, cst.READ_HOLDING_REGISTERS, 1, 24)
        for i in range(12):
            MainSysPower[i] = conver32(demo1[i*2],demo1[i*2+1])
            
        MainSysPayload = {"MainSysPower01" : round(MainSysPower[0]*0.1,1),
                          "MainSysPower02" : round(MainSysPower[1]*0.1,1),
                          "MainSysPower03" : round(MainSysPower[2]*0.1,1),
                          "MainSysPower04" : round(MainSysPower[3]*0.1,1),
                          "MainSysPower05" : round(MainSysPower[4]*0.1,1),
                          "MainSysPower06" : round(MainSysPower[5]*0.001,3),
                          "MainSysPower07" : round(MainSysPower[6]*0.001,3),
                          "MainSysPower08" : round(MainSysPower[7]*0.1,1),
                          "MainSysPower09" : round(MainSysPower[8]*0.001,3),
                          "MainSysPower10" : round(MainSysPower[9]*0.1,1),
                          "MainSysPower11" : round(MainSysPower[10]*0.01,2),
                          "MainSysPower12" : round(MainSysPower[11]*0.1,1) }
    except:
        MainSysPayload = {"MainSysPower01" : 9999,
                          "MainSysPower02" : 9999,
                          "MainSysPower03" : 9999,
                          "MainSysPower04" : 9999,
                          "MainSysPower05" : 9999,
                          "MainSysPower06" : 9999,
                          "MainSysPower07" : 9999,
                          "MainSysPower08" : 9999,
                          "MainSysPower09" : 9999,
                          "MainSysPower10" : 9999,
                          "MainSysPower11" : 9999,
                          "MainSysPower12" : 9999, }
    #print (MainSysPayload)
    return MainSysPayload

def Battery_charging(HOST_Addr):
    
    try:
        MainSysPower = [0,0,0,0]
        master = modbus_tcp.TcpMaster(host=HOST_Addr)
        master.set_timeout(5.0)
        demo1 = master.execute(1, cst.READ_HOLDING_REGISTERS, 5, 4)
        for i in range(2):
            MainSysPower[i] = conver32(demo1[i*2],demo1[i*2+1])
            
        MainSysPayload = {"MainChargingPower" : MainSysPower[0]*0.1,
                          "MainDischargingPower" : MainSysPower[1]*0.1}
    except:
        MainSysPayload = {"MainChargingPower" : 9999,
                          "MainDischargingPower" : 9999 }
    #print (MainSysPayload)
    return MainSysPayload

def SendCharg(token,IPaddr):
    try:
        client1 = mqtt.Client()
        client1.username_pw_set(token," ")
        client1.connect("thingsboard.cloud", 1883, 60)
        print(client1.publish("v1/devices/me/telemetry", json.dumps(Battery_charging(IPaddr))))
    except:
        pass

def SendMainSystem01(token,IPaddr):
    try:
        client1 = mqtt.Client()
        client1.username_pw_set(token," ")
        client1.connect("thingsboard.cloud", 1883, 60)
        print(client1.publish("v1/devices/me/telemetry", json.dumps(getMainPower(IPaddr))))
    except:
        pass

def Sendweather(token,comport):
    try:
        client1 = mqtt.Client()
        client1.username_pw_set(token," ")
        client1.connect("thingsboard.cloud", 1883, 60)
        print(client1.publish("v1/devices/me/telemetry", json.dumps(GetVantage2Data(comport,9600,16))))
    except:
        pass

def sendBatteryOP(num,ID):
    try:
        client3 = mqtt.Client()
        client3.username_pw_set("1AZnqejWVF8cm3BBy6xg"," ")
        client3.connect("thingsboard.cloud", 1883, 60)
        print(client3.publish("v1/devices/me/telemetry", json.dumps(getBatteryOP('192.186.50.6'))))
    except:
        pass
    
def getBatteryOP(HOST_Addr):
    try:
        clientB01 = mqtt.Client()
        clientB01.username_pw_set("1AZnqejWVF8cm3BBy6xg"," ")
        clientB01.connect("thingsboard.cloud", 1883, 60)
        
        master = modbus_tcp.TcpMaster(host=HOST_Addr)
        master.set_timeout(100.0)
        battery01 = master.execute(1, cst.READ_HOLDING_REGISTERS, 801, 100)
        time.sleep(2)
        
        for i in range(10):
           battery01payload={str(i)+"stBatterystateofcharge" : battery01[i*10],
                   str(i)+"stBatteryPackWarningFlag" : conver32(battery01[i*10+1],battery01[i*10+2]),
                   str(i)+"stBatteryCurrent" : conver32(battery01[i*10+3],battery01[i*10+4]),
                   str(i)+"stBatteryVoltage" : conver32(battery01[i*10+5],battery01[i*10+6]),
                   str(i)+"stHighTemperature" : conver32(battery01[i*10+7],battery01[i*10+8]),
                   str(i)+"stSOH" : battery01[i*10+9]
                   }
           print(battery01payload)
        
        #print(clientB01.publish("v1/devices/me/telemetry", json.dumps(battery01payload)))
        print(battery01payload)
        time.sleep(10)
        battery02 = master.execute(1, cst.READ_HOLDING_REGISTERS, 901, 100)
        time.sleep(2)
        for i in range(10):
           battery01payload={str(10+i)+"stBatterystateofcharge" : battery01[i*10],
                   str(10+i)+"stBatteryPackWarningFlag" : conver32(battery01[i*10+1],battery01[i*10+2]),
                   str(10+i)+"stBatteryCurrent" : conver32(battery01[i*10+3],battery01[i*10+4]),
                   str(10+i)+"stBatteryVoltage" : conver32(battery01[i*10+5],battery01[i*10+6]),
                   str(10+i)+"stHighTemperature" : conver32(battery01[i*10+7],battery01[i*10+8]),
                   str(10+i)+"stSOH" : battery01[i*10+9]
                   }
           print(battery01payload)
        #print(clientB01.publish("v1/devices/me/telemetry", json.dumps(battery01payload)))
        print(battery01payload)
        time.sleep(10)
        battery03 = master.execute(1, cst.READ_HOLDING_REGISTERS, 1001, 100)
        time.sleep(2)
        for i in range(10):
           battery01payload={str(20+i)+"stBatterystateofcharge" : battery01[i*10],
                   str(20+i)+"stBatteryPackWarningFlag" : conver32(battery01[i*10+1],battery01[i*10+2]),
                   str(20+i)+"stBatteryCurrent" : conver32(battery01[i*10+3],battery01[i*10+4]),
                   str(20+i)+"stBatteryVoltage" : conver32(battery01[i*10+5],battery01[i*10+6]),
                   str(20+i)+"stHighTemperature" : conver32(battery01[i*10+7],battery01[i*10+8]),
                   str(20+i)+"stSOH" : battery01[i*10+9]
                   }
           print(battery01payload)
        #print(clientB01.publish("v1/devices/me/telemetry", json.dumps(battery01payload)))
        print(battery01payload)
        time.sleep(10)
        
        
    except:
        pass

def dojob01():
    SendMainSystem01("oHdFlje4ZHbBTgrrueCA",'192.168.7.100')
    time.sleep(5)

def dojob02():
    Sendweather('nJZOWiKj6IDQQNGn2nTK','/dev/ttyS1')
    #Sendweather('nJZOWiKj6IDQQNGn2nTK','COM3')
    time.sleep(5)

schedule.every(2).minutes.do(dojob01)

schedule.every(2).minutes.do(dojob02)


while True:
    #print (getMainPower('192.168.7.100'))
    schedule.run_pending()
    time.sleep(1)