#!/usr/bin/env python
'''
Copyright 2015 Zhi Xiang Lin
Python based Modbus server
'''
#---------------------------------------------------------------------------# 
# import various server implementations
#---------------------------------------------------------------------------# 
from pymodbus.server.async import StartTcpServer
from pymodbus.server.async import StartUdpServer
from pymodbus.server.async import StartSerialServer

from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer

from twisted.internet.task import LoopingCall

import sys
import logging
import logging.handlers
import socket

#---------------------------------------------------------------------------# 
# configure server parameters
#---------------------------------------------------------------------------# 

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("www.google.com", 80))

server_address = s.getsockname()[0] # Make sure your box can bind to this IP
server_port = 502 # default port for Modbus is 502

if len(sys.argv) == 3: # set server params if given cmd line args
    server_address = sys.argv[1]
    server_port = int(sys.argv[2])

#---------------------------------------------------------------------------# 
# configure service logging
#---------------------------------------------------------------------------# 
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# Add syslog handler 
handler = logging.handlers.SysLogHandler('/dev/log')
log.addHandler(handler)


#---------------------------------------------------------------------------# 
# callback processes for simulating register updating on its own
#---------------------------------------------------------------------------# 

# increments holding regsiters register #0x0 
def updating_writer(a):
    log.debug("register update simulation")
    context = a[0]
    slave_id = 0x00
    holdingRegister = 3
    coil = 1
    
    # access holding registers addr 0 - 3 = drums 1 - 4 in lab 6
    drumsAddress = 0x0
    drums = context[slave_id].getValues(holdingRegister, drumsAddress, count=4)
    # access coils addr 0 - 3 = pumps 1 - 4 in lab6
    pumpsAddress = 0x0
    pumps = context[slave_id].getValues(coil, pumpsAddress, count=4)

    # access coils addr 10 - 11 = input and output valves respectively
    valvesAddress = 0x0a # dec 10 = hex 0x0a
    valves = context[slave_id].getValues(coil, valvesAddress, count=2)

    # update drums 
    if valves[0] == True: 
        drums[1] = drums[1] + 2
    if valves[1] == True:
        drums[0] = drums[0] - 2

    if pumps[0] == True:
        if drums[0] > 0:
            drums[1] = drums[1] + 1
            drums[0] = drums[0] - 1
    if pumps[1] == True:
        if drums[2] > 0:
            drums[1] = drums[1] + 1
            drums[2] = drums[2] - 1
    if pumps[2] == True:
        if drums[3] > 0:
            drums[2] = drums[2] + 1
        drums[3] = drums[3] - 1
    if pumps[3] == True:
        if drums[0] > 0:
            drums[3] = drums[3] + 1
            drums[0] = drums[0] - 1

    for i in range(0,4):
        if drums[i] >= 100:
            drums[i] = 100
        if drums[i] <= 0:
            drums[i] = 0


    log.debug("drums: " + str(drums));
    log.debug("pumps: " + str(pumps));
    log.debug("valves: " + str(valves));
    context[slave_id].setValues(holdingRegister, drumsAddress, drums)
   
    

#---------------------------------------------------------------------------# 
# initialize data store
#---------------------------------------------------------------------------# 

store = ModbusSlaveContext(
    di = ModbusSequentialDataBlock(0, [False]*100),
    co = ModbusSequentialDataBlock(0, [False]*100),
    hr = ModbusSequentialDataBlock(0, [0]*100),
    ir = ModbusSequentialDataBlock(0, [0]*100))
context = ModbusServerContext(slaves=store, single=True)

#---------------------------------------------------------------------------# 
# initialize the server information
#---------------------------------------------------------------------------# 

identity = ModbusDeviceIdentification()
identity.VendorName = 'ZXL'
identity.ProductCode = 'PLC'
identity.VendorUrl = 'https://github.com/zxlin/Modbus-PLC-Simulator'
identity.ProductName = 'PLC-Sim'
identity.ModelName = 'Modbus-Server'
identity.MajorMinorRevision = '1.0'


#---------------------------------------------------------------------------# 
# Start running the server
#---------------------------------------------------------------------------#
time = 1
loop = LoopingCall(f=updating_writer, a=(context,))
loop.start(time, now=True)
StartTcpServer(context, identity=identity, address=(server_address, server_port))
