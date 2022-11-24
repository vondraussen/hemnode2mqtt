from unittest.mock import MagicMock
import serial
from hemnode2mqtt import hemnode2mqtt
import pytest


@pytest.mark.parametrize("data1, data2, expected", [
    (0, 1, 256),
    (0, 256, 0),
    (0, 128, -32768),
    (255, 127, 32767),
])
def test_getInt16(data1, data2, expected):
    result = hemnode2mqtt.getInt16(data1, data2)
    assert result == expected, f"Should be {expected}"


@pytest.mark.parametrize("data1, data2, expected", [
    (0, 1, 755),
    (0, 256, 0),
    (0, 128, 96640),
    (255, 127, 96637),
])
def test_getBattery(data1, data2, expected):
    result = hemnode2mqtt.getBattery(data1, data2)
    assert result == expected, f"Should be {expected}"


@pytest.mark.parametrize("data, expected", [
    (b'\x00\r\n', {'battery': None, 'id': None,
     'temp1': None, 'temp2': None, 'rssi': None}),
    (b'\x01\r\n', {'battery': None, 'id': None,
     'temp1': None, 'temp2': None, 'rssi': None}),
    (b'\x06\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x9e\r\n', {
     'battery': None, 'id': None, 'temp1': None, 'temp2': None, 'rssi': None}),
    (b'\x04\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x9e\r\n',
     {'battery': 0, 'id': 4, 'temp1': 0.0, 'temp2': 0.0, 'rssi': -79.0}),
    (b'\x04\x0c\x00\x00\x1c\x00\xff\xff\xff\xff\x02\x12\xa3\x01\x9e\r\n', {
     'battery': 1236, 'id': 4, 'temp1': 2.8, 'temp2': -0.1, 'rssi': -79.0}),
    (b'\x04\x0c\x00\x00\x1c\x00\xff\xff\xff\xff\x02\x13\xa4\x01\x9e\r\n', {
     'battery': 1239, 'id': 4, 'temp1': 2.8, 'temp2': -0.1, 'rssi': -79.0}),
    (b'\x05\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xb6\r\n',
     {'battery': 0, 'id': 5, 'temp1': 0.0, 'temp2': 0.0, 'rssi': -91.0}),
    (b'\x05\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf1\x01\xb6\r\n', {
     'battery': 1466, 'id': 5, 'temp1': 0.0, 'temp2': 0.0, 'rssi': -91.0}),
    (b'\x05\x0c\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00\x00\x00\xb6\r\n',
     {'battery': 0, 'id': 5, 'temp1': 10.0, 'temp2': 0.0, 'rssi': -91.0}),
    (b'\x05\x0c\x00\x00\x7f\xff\x00\x00\x00\x00\x00\x00\x00\x00\xb6\r\n', {
     'battery': 0, 'id': 5, 'temp1': -12.9, 'temp2': 0.0, 'rssi': -91.0}),
    (b'\x05\x0c\x00\x00\x00\x00\x7f\xff\x00\x00\x00\x00\x00\x00\xb6\r\n',
     {'battery': 0, 'id': 5, 'temp1': 0, 'temp2': -12.9, 'rssi': -91.0}),
    (b'\x05\x0c\x00\x00\x9c\x00\x9c\x00\xff\xff\x02\xd5\xb4\x01\xb6\r\n', {
     'battery': 1286, 'id': 5, 'temp1': 15.6, 'temp2': 15.6, 'rssi': -91.0}),
    (b'\x05\x0c\x00\x00\x9c\x00\x9c\x00\xff\xff\x02\xd6\xc3\x01\xb5\r\n', {
     'battery': 1330, 'id': 5, 'temp1': 15.6, 'temp2': 15.6, 'rssi': -90.5}),
    (b'\x00\xd0\x07\xd6\x01\r\n', {
     'id': 0, 'humi': 47.0, 'temp1': 20.0, 'temp2': None, 'battery': None, 'rssi': None}),
    (b'\x00\xd0\x07\xd7\x01\r\n', {
     'id': 0, 'humi': 47.1, 'temp1': 20.0, 'temp2': None, 'battery': None, 'rssi': None}),
])
def test_decode(data, expected):
    ser = serial.Serial()
    ser.read_until = MagicMock(return_value=data)
    msg_obj = hemnode2mqtt.HemnodeMessage(ser)
    msg_obj.receive_next_msg()
    msg_obj.decode_last_msg()
    assert msg_obj.id == expected['id']
    assert msg_obj.battery == expected['battery']
    assert msg_obj.temp1 == expected['temp1']
    assert msg_obj.temp2 == expected['temp2']
    assert msg_obj.rssi == expected['rssi']


@pytest.mark.parametrize("data, expected", [
    (b'\x00\r\n', None),
    (b'\x01\r\n', None),
    (b'\x06\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x9e\r\n', None),
    (b'\x04\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x9e\r\n',
     ['homes,Location=yourHome,Room=outside Temperature=0.0,Battery=0,rssi=-79.0']),
    (b'\x04\x0c\x00\x00\x1c\x00\xff\xff\xff\xff\x02\x12\xa3\x01\x9e\r\n', [
     'homes,Location=yourHome,Room=outside Temperature=2.8,Battery=1236,rssi=-79.0']),
    (b'\x04\x0c\x00\x00\x1c\x00\xff\xff\xff\xff\x02\x13\xa4\x01\x9e\r\n', [
     'homes,Location=yourHome,Room=outside Temperature=2.8,Battery=1239,rssi=-79.0']),
    (b'\x05\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xb6\r\n', [
     'homes,Location=yourHome,Room=garage Temperature=0.0,Battery=0,rssi=-91.0', 'homes,Location=yourHome,Room=battery Temperature=0.0,Battery=0,rssi=-91.0']),
    (b'\x05\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf1\x01\xb6\r\n', [
     'homes,Location=yourHome,Room=garage Temperature=0.0,Battery=1466,rssi=-91.0', 'homes,Location=yourHome,Room=battery Temperature=0.0,Battery=1466,rssi=-91.0']),
    (b'\x05\x0c\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00\x00\x00\xb6\r\n', [
     'homes,Location=yourHome,Room=garage Temperature=0.0,Battery=0,rssi=-91.0', 'homes,Location=yourHome,Room=battery Temperature=10.0,Battery=0,rssi=-91.0']),
    (b'\x05\x0c\x00\x00\x7f\xff\x00\x00\x00\x00\x00\x00\x00\x00\xb6\r\n', [
     'homes,Location=yourHome,Room=garage Temperature=0.0,Battery=0,rssi=-91.0', 'homes,Location=yourHome,Room=battery Temperature=-12.9,Battery=0,rssi=-91.0']),
    (b'\x05\x0c\x00\x00\x00\x00\x7f\xff\x00\x00\x00\x00\x00\x00\xb6\r\n',
     ['homes,Location=yourHome,Room=garage Temperature=-12.9,Battery=0,rssi=-91.0', 'homes,Location=yourHome,Room=battery Temperature=0.0,Battery=0,rssi=-91.0']),
    (b'\x05\x0c\x00\x00\x9c\x00\x9c\x00\xff\xff\x02\xd5\xb4\x01\xb6\r\n', [
     'homes,Location=yourHome,Room=garage Temperature=15.6,Battery=1286,rssi=-91.0', 'homes,Location=yourHome,Room=battery Temperature=15.6,Battery=1286,rssi=-91.0']),
    (b'\x05\x0c\x00\x00\x9c\x00\x9c\x00\xff\xff\x02\xd6\xc3\x01\xb5\r\n', [
     'homes,Location=yourHome,Room=garage Temperature=15.6,Battery=1330,rssi=-90.5', 'homes,Location=yourHome,Room=battery Temperature=15.6,Battery=1330,rssi=-90.5']),
    (b'\x00\xd0\x07\xd6\x01\r\n', [
     'homes,Location=yourHome,Room=hwr Temperature=20.0,Humidity=47.0']),
    (b'\x00\xd0\x07\xd7\x01\r\n', [
     'homes,Location=yourHome,Room=hwr Temperature=20.0,Humidity=47.1']),
])
def test_encode_influx(data, expected):
    ser = serial.Serial()
    ser.read_until = MagicMock(return_value=data)
    msg_obj = hemnode2mqtt.HemnodeMessage(ser)
    msg_obj.receive_next_msg()
    msg_obj.decode_last_msg()
    influx = msg_obj.get_influx_inline()
    assert influx == expected
