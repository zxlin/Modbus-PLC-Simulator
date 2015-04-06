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

#---------------------------------------------------------------------------# 
# configure server parameters
#---------------------------------------------------------------------------# 

server_address = "172.31.1.242" # Make sure your box can bind to this IP
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

handler = logging.handlers.SysLogHandler('/dev/log')
log.addHandler(handler)


#---------------------------------------------------------------------------# 
# callback processes for simulating register updating on its own
#---------------------------------------------------------------------------# 

# increments holding regsiters register #0x0 
def updating_writer(a):
	log.debug("register update simulation")
	context = a[0]
	register = 3
	slave_id = 0x00
	address = 0x0
	values = context[slave_id].getValues(register, address, count=1)
	values = [v + 1 for v in values]
	log.debug("new values: " + str(values))
	context[slave_id].setValues(register, address, values)

#---------------------------------------------------------------------------# 
# initialize data store
#---------------------------------------------------------------------------# 

store = ModbusSlaveContext(
	di = ModbusSequentialDataBlock(0, [17]*100),
	co = ModbusSequentialDataBlock(0, [17]*100),
	hr = ModbusSequentialDataBlock(0, [17]*100),
	ir = ModbusSequentialDataBlock(0, [17]*100))
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
# time = 5
# loop = LoopingCall(f=updating_writer, a=(context,))
# loop.start(time, now=False)
StartTcpServer(context, identity=identity, address=(server_address, server_port))