#!/usr/bin/python3
import serial
import ctypes
import ssl
import paho.mqtt.client as mqtt
import os
from dotenv import load_dotenv


class HemnodeMessage():
    def __init__(self, serial):
        self.serial = serial
        self.lastMsg = None
        self.id = None
        self.temp1 = None
        self.temp2 = None
        self.battery = None
        self.rssi = None

    def receive_next_msg(self):
        line = self.serial.read_until('\r\n')

        if line == b'':  # on timeout
            self.lastMsg = None
            return False

        self.lastMsg = line
        return True

    def decode_last_msg(self):
        if self.lastMsg[0] != 0 and self.lastMsg[0] != 4 and self.lastMsg[0] != 5:
            return None

        if self.lastMsg[0] == 0 and len(self.lastMsg) != 7:
            return None

        self.id = self.lastMsg[0]

        if self.id == 4 or self.id == 5:
            self.temp1 = getInt16(self.lastMsg[4], self.lastMsg[5]) / 10
            self.temp2 = getInt16(self.lastMsg[6], self.lastMsg[7]) / 10
            self.battery = getBattery(self.lastMsg[12], self.lastMsg[13])
            self.rssi = -(self.lastMsg[14]/2)

        if self.id == 0:
            self.temp1 = getInt16(self.lastMsg[1], self.lastMsg[2]) / 100
            self.humi = getInt16(self.lastMsg[3], self.lastMsg[4]) / 10

    def get_influx_inline(self):
        if self.id == None:
            return None

        INFLUX_MEASUREMENT_TAG = os.getenv(
            'HEMNODE2MQTT_INFLUX_MEASUREMENT_TAG', default='homes,Location=yourHome')

        messages = []
        if self.id == 0:
            influxInline = f"{INFLUX_MEASUREMENT_TAG},Room=hwr "
            influxInline += f"Temperature={self.temp1}"
            influxInline += f",Humidity={self.humi}"
            messages.append(influxInline)

        if self.id == 4:
            influxInline = f"{INFLUX_MEASUREMENT_TAG},Room=outside "
            influxInline += f"Temperature={self.temp1}"
            influxInline += f",Battery={self.battery}"
            influxInline += f",rssi={self.rssi}"
            messages.append(influxInline)

        if self.id == 5:
            influxInline = f"{INFLUX_MEASUREMENT_TAG},Room=garage "
            influxInline += f"Temperature={self.temp2}"
            influxInline += f",Battery={self.battery}"
            influxInline += f",rssi={self.rssi}"
            messages.append(influxInline)
            influxInline = f"{INFLUX_MEASUREMENT_TAG},Room=battery "
            influxInline += f"Temperature={self.temp1}"
            influxInline += f",Battery={self.battery}"
            influxInline += f",rssi={self.rssi}"
            messages.append(influxInline)

        return messages


def getInt16(data1, data2):
    return ctypes.c_short(data1 + (data2 * 256)).value


def getBattery(data1, data2):
    raw = ctypes.c_ushort(data1 + (data2 * 256)).value
    return round((raw * 3020) / 1024)


def hemnoded():
    load_dotenv()
    MQTT_USER = os.getenv('HEMNODE2MQTT_MQTT_USER', default='None')
    MQTT_PW = os.getenv('HEMNODE2MQTT_MQTT_PW', default='None')
    MQTT_CLIENT_ID = os.getenv(
        'HEMNODE2MQTT_MQTT_CLIENT_ID', default='hemnode2mqtt')
    MQTT_BROKER = os.getenv('HEMNODE2MQTT_MQTT_BROKER', default='localhost')
    MQTT_PORT = int(os.getenv('HEMNODE2MQTT_MQTT_PORT', default='8883'))
    MQTT_USE_TLS = os.getenv('HEMNODE2MQTT_MQTT_USE_TLS',
                             default='True').lower() not in ('false', '0', 'f')
    MQTT_CA_CERT = os.getenv('HEMNODE2MQTT_MQTT_CA_CERT',
                             default='/etc/ssl/certs/ca-certificates.crt')
    MQTT_TOPIC = os.getenv('HEMNODE2MQTT_MQTT_TOPIC', default='homey/yourHome')
    INFLUX_MEASUREMENT_TAG = os.getenv(
        'HEMNODE2MQTT_INFLUX_MEASUREMENT_TAG', default='homes,Location=yourHome')
    SERIAL_DEV = os.getenv('HEMNODE2MQTT_SERIAL_DEV', default='/dev/ttyUSB0')

    mqttClient = mqtt.Client(client_id=MQTT_CLIENT_ID, transport="tcp")
    if MQTT_USE_TLS:
        mqttClient.tls_set(ca_certs=MQTT_CA_CERT, tls_version=ssl.PROTOCOL_TLS)
    mqttClient.username_pw_set(MQTT_USER, password=MQTT_PW)
    mqttClient.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqttClient.loop_start()
    ser = serial.Serial(SERIAL_DEV, 38400, timeout=0.2)
    msg_obj = HemnodeMessage(ser)

    while True:
        if not msg_obj.receive_next_msg():
            continue

        msg_obj.decode_last_msg()

        try:
            msgs = msg_obj.get_influx_inline()
        except:
            print('decode error', msgs)

        if msgs is None:
            continue

        for influx in msgs:
            mqttClient.publish(MQTT_TOPIC, influx)

    mqttClient.disconnect
