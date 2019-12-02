# Raspberry Pi-based, temperature-driven control system for heated sidewalks/driveways
WiSH-Controller uses data from the OpenWeather API to drive the state of driveway, sidewalk, and other heating systems based on current and predicted outdoor temperatures. It can be easily modified to utilize a locally-connected temperature sensor in place of the current weather as reported by OpenWeather. This is not a replacement for a heating system controller. It is desgined to run alongside your heating system's controller and enable automation to reduce costs and lessen the associated risks of manually-triggered systems. 

This application requires that your register for an OpenWeater API ID. you must register for your own API key at https://home.openweathermap.org/users/sign_up. 

**Requirements**

- Operating platform which has Internet access, can run Python v3, and provides GPIO accessibility (e.g. Raspberry Pi, and many others.)
- Single-channel relay
- OpenWeather API Key
- Knowledge of handling low-voltage electrical circuits.

**Hookup**

Quite simply, you connect up the relay in-line on the positive wire going to your heating controller. In many systems, turning on the a specific controller channel just means shorting the two terminals for that channel, so you would run from one terminal to the relay, connect the other terminal to the normally open terminal on your relay and that should be it. See the "Sidewalk WX Controller - Wiring Diagram.png" for more details. 

**General Application Information**

The application can make up to two distinct calls for temperature information. The first is a call for the current weather conditions based upon the longitude and latitude which is user-specified and is referred to as "instant data." The second call, if needed, is for the forecasted weather predictions of that same location, which is call "predictive data." You specify a temperature at which the system is triggered, the temperature units (Celsius or Fahrenheit,) the heating/rest cycle you prefer, and the evaluation cycle. The recommended evaluation cycle is one hour or greater to ensure that you do not exceed the maximum number of API requests for a free account. 

Launch WiSH-Controller by executing the following: `python3 WiSH-Controller.py`

**Instant Data Cycle**

The Instant data cycle (current weather conditions) is prioritized over predictive data. This means that if the current temperature is below the trigger temperature, it will turn on the heating/rest cycle without regard to future predictions. The heating/rest cycle will continue so long as the current temperature remains below the trigger temperature.

**Predictive Data Cycle**

The predictive data cycle looks at the weather forecast and can proactively arm the system. Forecasts are in three-hour increments. The application enables you to set a pre-heat timer which will cause the system to arm prior to the forecast window. In locations with extreme temperature variations, the enables you to get ahead of the incoming cold weather by proactively starting the heating prior to the arrival of temperatures below the trigger temperature. The predictive cycle is only run if the instant data cycle does not arm due to the current temperature. This reduces the number of API calls and may enable you to re-use your API for other applications. 

**Heating/Rest Cycle**

The heating/rest cycle is global across the entire application. Multiple factors come into play in deciding the heating rest cycle. Some thing that you should consider:
  - The cost of operation.
  - The heat retention of the material being heated. For example, concrete will retain heat longer than wood, but also takes more energy to heat to the same temperature. 
  - Hydronic systems (water-based) need to be protected from freezing via periodic cycling. 
  
**Logging**

As the application executes, it will simultaneously log to the console and to syslog. Debug information can be shown in the console by setting debugConsole to True. 

**Testing**

By setting the testFlag to true, you can fine tune your implementation without incurring hits aaginst the OpenWeather API. Enabling this mode does two things:
  1. It utilizes the OpenWeather API Instant.json and OpenWeather API Forecast.json files to supply tmperature information locally. 
  2. It changes the timing of all settings from hours to seconds, enabling you to test more quickly.
  
  
