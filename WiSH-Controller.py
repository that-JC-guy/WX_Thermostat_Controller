import requests
import json
import time
import logging
import logging.handlers
from datetime import datetime
import RPi.GPIO as GPIO
import temperature_conversions as tempConv 	# Custom module for converting temperatures within the app
import WiSH-WX-Data as wx				# Custom module for acquiring weather data


# User-configurable constants
apiKey = "{YOUR API KEY}" 					# unique to each station, you must register fo your own at https://home.openweathermap.org/users/sign_up
homeLat = "{YOUR LATITUDE}"					# North/South
homeLon = "{YOUR LONGITUDE}"  					# East/West
triggerTemp = 34							# Temperature in Fahrenheit at which the system should trigger the system on.
tempUnit = "F"								# Use "F" for Fahrenheit or "C" for Celsius
evaluationCycle = 1							# The hour-based period in which data is refreshed and an trigger/untrigger decision is made.
relayPin1 = 37								# Corresponds to physical pin 37 on Raspberry Pi 3 Model B v2
preHeatTime = .25							# The number of hours ahead to switch on the relay prior to a forecasted temperature below triggerTemp. 
cycleHoursOn = 2							# When the instantSysArm is triggered, this value is the number of hours to run to have the relay switched on. When testFlag is enabled, the value is the number of seconds.
cycleHoursOff = 1							# When the instantSysArm is triggered, this vale is the number of hours to have the relay switched off. When testFlag is enabled, the value is the number of seconds.
testFlag = False							# True to enable test mode (using local json files so you don't oversubscribe your API calls). False to disable test mode (use False for production. )
debugConsole = False							# True to show debug output in console, False to not show it (production use should be False.)
disableInstantTrigger = False				# Set to true to disable instant (current) weather evaluation.
disablePredictiveTrigger = False			# Set to true to disable predictive (future) weather evaluation.
############################## DO NOT MODIFY BELOW THIS LINE  ##############################

############################## TESTING SETUP  ##############################
if (testFlag == True):
	forecastDataSrc = "OpenWeather API Forecast.json"
	instantDataSrc = "OpenWeather API Instant.json"

	with open(forecastDataSrc) as json_file:
		forecastData = json.load(json_file)
	
	with open(instantDataSrc) as json_file:
		instantData = json.load(json_file)

	currentTime = instantData['dt']															#Pulls the test current time from the OpenWeather API Instant file.
	currentTimeStd = datetime.utcfromtimestamp(currentTime).strftime('%Y-%m-%d %H:%M:%S')
############################## TESTING SETUP  ##############################

############################## LOGGING SETUP  ##############################
# Setup the root logging facility
logRoot = logging.getLogger('SidewalkWX')	
logRoot.setLevel(logging.DEBUG)													# DEBUG info abd above goes to syslog
handler = logging.handlers.SysLogHandler(address = '/dev/log')					# Direct logger output to syslog
syslogFormatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')	# Set formation of messages in syslog.
handler.setFormatter(syslogFormatter)											# Apply the formatter to the handlers
logRoot.addHandler(handler)														# Add handler to logger.

console = logging.StreamHandler()
if (debugConsole == True):
	console.setLevel(logging.DEBUG)
else:
	console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('SidewalkWX').addHandler(console)

# # For testing root logger.
# logRoot.debug('this is debug')
# logRoot.critical('this is critical')
# logRoot.warning('this is warning')
# logRoot.info('this is info')

# Root logger is setup. Append child loggers.
logWX = logging.getLogger('SidewalkWX.WX')
logRPi = logging.getLogger('SidewalkWX.RPi')

# #For testing child loggers.
# logWX.error("This is an error.")
# logRPi.warning("This is a warning")
############################## LOGGING SETUP  ##############################

############################## SETUP RPi CONFIGURATION  ##############################
GPIO.setmode(GPIO.BOARD)
GPIO.setup(relayPin1, GPIO.OUT)

GPIO.output(relayPin1, True)

instantSysArmActive = 0
instantSysArmInactive = 0
predictiveSysArmActive = 0
predictiveSysArmInactive = 0

try:
	while True:
		############################## BEGIN - WEATHER DATA GATHERING ##############################
		#Get all temps to K
		if tempUnit == "F":
			triggerTempK = tempConv.convertFtoK(triggerTemp)
		elif tempUnit == "C":
			triggerTempK = tempConv.convertCtoK(triggerTemp)
		else:
			logWX.error(tempUnit,"is not an allowed temperature unit.")

		############ INSTANTANEOUS WX DATA ###############	
		if (testFlag == True):
			nowTempK = instantData['main']['temp']
			nowReportTime = instantData['dt']
		else:
			nowReportTime,nowTempK = wx.getInstantWX(homeLat,homeLon,apiKey)
		
		nowReportTimeStd = datetime.utcfromtimestamp(nowReportTime).strftime('%Y-%m-%d %H:%M:%S')
		nowTempF = round(tempConv.convertKtoF(nowTempK),2)
		nowTempC = round(tempConv.convertKtoC(nowTempK),2)
		
		logWX.info("INSTANT SYSTEM REPORT - Report Time: '{0}'/'{1}' - Current temperature is '{2}' K/ '{3}' F / '{4}' C.".format(nowReportTimeStd,nowReportTime, nowTempK, nowTempF, nowTempC))

		############ ANALYZE INSTANT WX DATA ############
		if (disableInstantTrigger == False):
			if (nowTempK <= triggerTempK):
				instantSysArm = True
				logWX.info("INSTANT SYSTEM TRIGGER: ARMED - Current temperature is below trigger temperature.")
			else:
				instantSysArm = False
				logWX.info("INSTANT SYSTEM TRIGGER: DISARMED - Current temperature is above trigger temperature.")
		else:
			instantSysArm = False
		
		############ FORECAST WX DATA ############
		if (disablePredictiveTrigger == False):
			if (testFlag == True):
				forecastReportTime = forecastData['list'][0]['dt']
				forecastMinTempK = forecastData['list'][0]['main']['temp_min']
			elif (instantSysArm == False):
				forecastReportTime, forecastMinTempK = wx.getForecastWX(homeLat,homeLon,apiKey)
			else:
				bypassPredictiveAnalysis = True
				
			if (bypassPredictiveAnalysis != True):
				forecastReportTimeStd = datetime.utcfromtimestamp(forecastReportTime).strftime('%Y-%m-%d %H:%M:%S')	
				forecastTempF = round(tempConv.convertKtoF(forecastMinTempK),2)
				forecastTempC = round(tempConv.convertKtoC(forecastMinTempK),2)
				logWX.info("FORECAST SYSTEM REPORT - During the three hour period starting at '{0}' the minimum temperature is expected to be '{1}' K / '{2}' F / '{3}' C.".format(forecastReportTimeStd,forecastMinTempK,forecastTempF,forecastTempC))

				############ ANALYZE PREDICTIVE WX DATA ############
				if ((forecastMinTempK <= triggerTempK) and (instantSysArm == False)):
					predictiveSysArm = True
					if (testFlag == True):
						relayTriggerTime = 	forecastReportTime - preHeatTime
					else:
						relayTriggerTime = 	forecastReportTime - preHeatTime*3600	#Sets the relay to trigger the amount of time specified ahead of the forecast time.
						
					relayTriggerTimeStd = datetime.utcfromtimestamp(relayTriggerTime).strftime('%Y-%m-%d %H:%M:%S')	
					logWX.info("PREDICTIVE SYSTEM TRIGGER: ARMED - Forecast temperature is expected to be below trigger temperature. Relay will be triggered at '{0}'. Forecast time is '{1}'".format(relayTriggerTimeStd,forecastReportTimeStd))
				else:
					predictiveSysArm = False
					if (instantSysArm == True):
						logWX.info("PREDICTIVE SYSTEM TRIGGER: DISARMED - The CURRENT temperature is below the trigger temperature and the instantSysArm trigger is armed.")
					else:
						logWX.info("PREDICTIVE SYSTEM TRIGGER: DISARMED - The CURRENT temperature is above the trigger temperature.")
			else:
				predictiveSysArm = False
		else:
			predictiveSysArm = False
		
		############################## END - WEATHER DATA GATHERING ##############################
		#========================================================================================#
		############################## BEGIN - RPi CONTROL #######################################

		logWX.info("instantSysArm = '{0}'".format(instantSysArm) )
		logWX.info("predictiveSysArm = '{0}'".format(predictiveSysArm))

		if (instantSysArm == True):								#This instantSysArm trigger supercedes the predictiveSysArm. In other words, if the current temp is less than the trigger temp, the instantSysArm trigger takes priority.
			if (instantSysArmActive <= cycleHoursOn-1):			#This is the counter used to cycle the system on.
				instantSysArmActive = instantSysArmActive+1
				logRPi.info("instantSysArmActive PASS NUMBER: '{0}' of '{1}'".format(instantSysArmActive,cycleHoursOn))
				instantSysArmInactive = 0						#Reset the instantSysArmInactive for its next cycle.
				GPIO.output(relayPin1, False)
				logRPi.info("INSTANT SYSTEM TRIGGER SET GPIO PIN '{0}' TO LOW. RELAY ACTIVATED AT '{1}'".format(relayPin1,time.time()))
				if (testFlag == True):
					time.sleep(1)
			elif (instantSysArmInactive <= cycleHoursOff-1):	#This counter is used to time the relay deactivation time.
				instantSysArmInactive = instantSysArmInactive+1
				logRPi.info("instantSysArmInactive PASS NUMBER: '{0}' of '{1}'".format(instantSysArmInactive,cycleHoursOff))
				GPIO.output(relayPin1, True)
				logRPi.info("INSTANT SYSTEM TRIGGER SET GPIO PIN '{0}' TO HIGH. RELAY DEACTIVATED AT '{1}'".format(relayPin1, time.time()))
				if (instantSysArmInactive == cycleHoursOff):	#Once the last instantSysArmInactive is triggered, reset the instantSysArmActive to activate on next evaluation.
					instantSysArmActive = 0	
				if (testFlag == True):
					time.sleep(1)
		elif (predictiveSysArm == True):
			if (testFlag == True):
				logRPi.debug("TEST INFO: Current Test Time: '{0}'".format(currentTimeStd))
				logRPi.debug("TEST INFO: Trigger Test Time: '{0}'".format(relayTriggerTimeStd))
			else:
				currentTime = time.time()
				logRPi.info("PREDICTIVE SYSTEM TRIGGER WILL SET GPIO PIN '{0}' TO LOW AT '{1}'".format(relayPin1,relayTriggerTimeStd))
			while (currentTime < relayTriggerTime): 			#Interrupt normal timing cycle to wait for the relayTriggerTime to be met. Once met, exit while and turn on relay.
				time.sleep(1)
				if (testFlag == True):
					currentTime = currentTime+1
					logRPi.debug("Current Time: '{0}'".format(currentTime))
				else:
					currentTime = time.time()
			if (predictiveSysArmActive <= cycleHoursOn-1):		#This is the counter used to cycle the system on.
				predictiveSysArmActive = predictiveSysArmActive+1
				logRPi.info("predictiveSysArmActive PASS NUMBER: '{0}' of '{1}'".format(predictiveSysArmActive,cycleHoursOn))
				predictiveSysArmInactive = 0
				GPIO.output(relayPin1, False)
				logRPi.info("PREDICTIVE SYSTEM TRIGGER SET GPIO PIN '{0}' TO LOW AT '{1}'".format(relayPin1,relayTriggerTimeStd))
				if (testFlag == True):
					time.sleep(1)
					
			elif (predictiveSysArmInactive <= cycleHoursOff-1):	#This is the counter used to cycle the system on.
				predictiveSysArmInactive = predictiveSysArmInactive+1
				logRPi.info("predictiveSysArmInactive PASS NUMBER: '{0}' of '{1}'".format(predictiveSysArmInactive,cycleHoursOff))
				GPIO.output(relayPin1, True)
				logRPi.info("GPIO Pin '{0}' SET TO HIGH. RELAY SWITCHED OFF AT '{1}'.".format(relayPin1,datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')))
				if (predictiveSysArmInactive == cycleHoursOff):
					predictiveSysArmActive = 0
				if (testFlag == True):
					time.sleep(1)
		if (testFlag == True):
			time.sleep(evaluationCycle)
		else:
			time.sleep(evaluationCycle*3600)
except KeyboardInterrupt: #If CTRL+C is pressed, exit cleanly.
	logRoot.info("Process killed by keyboard interrupt.")
	
except IOError as e:
	errno, strerror = e.args
	logRoot.error("I/O error({0}): {1}".format(errno,strerror))

finally:
	logRoot.info("Cleaning up...")
	GPIO.cleanup() #Clean up all GPIO
	logRoot.info("Clean up completed. Exiting...")



















############################## END - RPi CONTROL ##############################