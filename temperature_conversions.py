def convertKtoF( float ):
	fDegF = (9*(float-273.15)/5)+32
	return fDegF
	
def convertKtoC( float ):
	fDegC = float-273.15
	return fDegC
	
def convertFtoK( float ):
	fDegK = 273.15+(float-32)*5/9
	return fDegK
	
def convertCtoK( float ):
	fDegK = float+273.15
	return fDegK
	
