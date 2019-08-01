#!/usr/bin/python
# -*- coding: utf8 -*-

# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import os.path
import math
import sys
import Adafruit_DHT
#from requests.auth import HTTPBasicAuth
import requests
import time
import yaml


def write_to_log(gpio, message):
    with open('/mnt/usb/log/read-dht-error', 'a') as error_log_file:
        date = time.strftime("%Y-%m-%d %H:%m:%S")
        line = "{0} GPIO_{1:02d} {2}\n".format(date, gpio, message)
        error_log_file.write(line)
        error_log_file.close()


############# Parametres #################################

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# les parametres de Domoticz
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

domoticz_ip='domotipi'
domoticz_port='8080'
user=''
password=''

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# les parametres du DHT
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#sensor est 11,22,ou 2302

sensor=22



mesures = [
    { "date": None, "domoticz_idx": 39, "pin": 26, "temperature": None, "humidity": None },
    { "date": None, "domoticz_idx": 54, "pin": 19, "temperature": None, "humidity": None },
    { "date": None, "domoticz_idx": 62, "pin": 20, "temperature": None, "humidity": None }
]

if os.path.isfile("/mnt/usb/log/dht22-mesures.yml"):
    with open('/mnt/usb/log/dht22-mesures.yml', 'r') as mesures_file:
        mesures = yaml.load(mesures_file)
    #print(mesures)

############# Fin des parametres #################################


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# le format pour la temp hum est celui ci
#/json.htm?type=command&param=udevice&idx=IDX&nvalue=0&svalue=TEMP;HUM;HUM_STAT


def maj_widget(val_url):
    requete='http://'+domoticz_ip+':'+domoticz_port+val_url
    #print requete
    #r=requests.get(requete,auth=HTTPBasicAuth(user,password))
    r=requests.get(requete)
    if  r.status_code != 200:
        print "Erreur API Domoticz"


for mesure in mesures:
    pin = mesure["pin"]
    domoticz_idx = mesure["domoticz_idx"]

    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

    print('DHT sur GPIO {0}'.format(pin))

    if humidity is None:
        write_to_log(pin, "Unable to retrieve humidity")
        print("Erreur de lecture de l'humidité du DHT sur le GPIO {0} !".format(pin))
        print("Utilisation de la dernière valeur connue...")
        humidity = mesure["humidity"]
        if humidity is None:
            print("Pas de dernière valeur connue")
            sys.exit(1)
    else:
        if mesure["humidity"] is None:
            mesure["humidity"] = int(humidity)
        else:
            if math.fabs(humidity - mesure["humidity"]) < 10:
                mesure["humidity"] = int(humidity)
            else:
                write_to_log(pin, "Unexpected humidity value: " + str(humidity))
                print("Valeur d'humidité aberrante : " + str(humidity))
                print("Utilisation de la dernière valeur connue...")
                humidity = mesure["humidity"]
                if humidity is None:
                    print("Pas de dernière valeur connue")
                    sys.exit(1)

    if temperature is None:
        write_to_log(pin, "Unable to retrieve temperature")
        print('Erreur de lecture de la température du DHT sur le GPIO {0} !'.format(pin))
        print("Utilisation de la dernière valeur connue...")
        temperature = mesure["temperature"]
        if temperature is None:
            print("Pas de dernière valeur connue")
            sys.exit(1)
    else:
        if mesure["temperature"] is None:
            mesure["temperature"] = round(temperature, 1)
        else:
            if math.fabs(temperature - mesure["temperature"]) < 5:
                mesure["temperature"] = round(temperature, 1)
            else:
                write_to_log(pin, "Unexpected temperature value: " + str(temperature))
                print("Valeur de température aberrante : " + str(temperature))
                print("Utilisation de la dernière valeur connue...")
                temperature = mesure["temperature"]
                if temperature is None:
                    print("Pas de dernière valeur connue")
                    sys.exit(1)

    print('   Température\t{0:0.1f}°\n   Humidité\t{1}%'.format(mesure["temperature"], mesure["humidity"]))

    mesure["date"] = time.strftime("%Y-%m-%d %H:%m:%S")
    with open('/mnt/usb/log/dht22-mesures.yml', 'w') as mesures_file:
        yaml.dump(mesures, mesures_file)

    # l URL Domoticz pour le widget virtuel
    url = '/json.htm?type=command&param=udevice&idx='+str(domoticz_idx)
    url += '&nvalue=0&svalue='
    url += str(mesure["temperature"]) + ';' + str(mesure["humidity"]) + ';2'
    #print url
    maj_widget(url)

