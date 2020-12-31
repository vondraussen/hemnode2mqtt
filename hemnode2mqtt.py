#!/usr/bin/python3
import serial
import ctypes
import ssl
import paho.mqtt.client as mqtt
import os
from dotenv import load_dotenv

def getInt16(data1, data2):
  return ctypes.c_short(data1 + (data2 * 256)).value

def getBattery(data1, data2):
  raw = ctypes.c_ushort(data1 + (data2 * 256)).value
  return round((raw * 3020) / 1024)

def decodeMsg(data):
  msg = {}
  if data[0] != 4 and data[0] != 5:
    return None

  msg['id'] = data[0]
  msg['temp1'] = getInt16(data[4], data[5]) / 10
  msg['temp2'] = getInt16(data[6], data[7]) / 10
  msg['battery'] = getBattery(data[12], data[13])

  return msg

def main():
  load_dotenv()
  MQTT_USER = os.getenv('HEMNODE2MQTT_MQTT_USER')
  MQTT_PW = os.getenv('HEMNODE2MQTT_MQTT_PW')
  MQTT_CLIENT_ID = os.getenv('HEMNODE2MQTT_MQTT_CLIENT_ID', default='hemnode2mqtt')
  MQTT_BROKER = os.getenv('HEMNODE2MQTT_MQTT_BROKER', default='localhost')
  MQTT_PORT = os.getenv('HEMNODE2MQTT_MQTT_PORT', default=8883)
  MQTT_CA_CERT = os.getenv('HEMNODE2MQTT_MQTT_CA_CERT', default='/etc/ssl/certs/ca-certificates.crt')
  MQTT_TOPIC = os.getenv('HEMNODE2MQTT_MQTT_TOPIC', default='homey/yourHome')
  INFLUX_MEASUREMENT_TAG = os.getenv('HEMNODE2MQTT_INFLUX_MEASUREMENT_TAG', default='homes,Location=yourHome')
  SERIAL_DEV = os.getenv('HEMNODE2MQTT_SERIAL_DEV', default='/dev/ttyUSB0')

  mqttClient = mqtt.Client(client_id=MQTT_CLIENT_ID, transport="tcp")
  mqttClient.tls_set(ca_certs=MQTT_CA_CERT, tls_version=ssl.PROTOCOL_TLS)
  mqttClient.username_pw_set(MQTT_USER, password=MQTT_PW)
  mqttClient.connect(MQTT_BROKER, MQTT_PORT, 60)
  mqttClient.loop_start()

  ser = serial.Serial(SERIAL_DEV, 38400, timeout=0.2)

  while True:
    line = ser.read_until('\r\n')
    if line == b'':
      continue

    try:
      msg = decodeMsg(line)
    except:
      print('decode error')

    if msg is None:
      continue

    if msg['id'] == 4:
      influxInline = f"{INFLUX_MEASUREMENT_TAG},Room=outside "
      influxInline += f"Temperature={msg['temp1']}"
      influxInline += f",Battery={msg['battery']}"
      mqttClient.publish(MQTT_TOPIC, influxInline)

    if msg['id'] == 5:
      influxInline = f"{INFLUX_MEASUREMENT_TAG},Room=garage "
      influxInline += f"Temperature={msg['temp2']}"
      influxInline += f",Battery={msg['battery']}"
      mqttClient.publish(MQTT_TOPIC, influxInline)
      influxInline = f"{INFLUX_MEASUREMENT_TAG},Room=battery "
      influxInline += f"Temperature={msg['temp1']}"
      influxInline += f",Battery={msg['battery']}"
      mqttClient.publish(MQTT_TOPIC, influxInline)

  mqttClient.disconnect

if __name__ == '__main__':
  main()
