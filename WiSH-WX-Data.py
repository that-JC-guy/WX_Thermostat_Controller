import requests
import json
import temperature_conversions as tempConv 	#Custom module for converting temperatures within the app

############ INSTANTANEOUS WX  DATA ###############
def getInstantWX(lat,lon,apiKey):	
	urlInstant = "https://api.openweathermap.org/data/2.5/weather?lat="+lat+"&lon="+lon+"&APPID="+apiKey
	#print("INFO: API CALL TO: ",urlInstant)
	# sending get request and saving the response as data
	instantData = requests.get(urlInstant).json()
	
	#parse returned data
	nowTempK = instantData['main']['temp']
	reportTime = instantData['dt']
	
	return reportTime,nowTempK

############ FORECAST WX DATA ############
def getForecastWX(lat,lon,apiKey):
	urlForecast = "https://api.openweathermap.org/data/2.5/forecast?lat="+lat+"&lon="+lon+"&APPID="+apiKey
	#print("INFO: API CALL TO: ",urlForecast)
	# sending get request and saving the response as data
	forecastData = requests.get(urlForecast).json()

	reportTime = forecastData['list'][0]['dt']
	forecastLowTempK = forecastData['list'][0]['main']['temp_min']	#Min temperature during 3 hour period

	return reportTime,forecastLowTempK