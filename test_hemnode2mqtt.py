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
    (b'\x00\r\n', None),
    (b'\x01\r\n', None),
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
    (b'\x00\xd0\x07\xd6\x01\r\n', {'id': 0, 'humi': 47.0, 'temp1': 20.0}),
    (b'\x00\xd0\x07\xd7\x01\r\n', {'id': 0, 'humi': 47.1, 'temp1': 20.0}),
    # (b'\x04\x0c\x00\x00\x1b\x00\xff\xff\xff\xff\x02!\x9d\x01\x9c\r\n\x04\x0c\x00\x00\x1b\x00\xff\xff\xff\xff\x02!\x9d\x01\x9c\r\n\x04\x0c\x00\x00\x1b\x00\xff\xff\xff\xff\x02!\x9d\x01\x9d\r\n', None),
])
def test_decodeMsg(data, expected):
    result = hemnode2mqtt.decodeMsg(data)
    assert result == expected, f"Should be {expected}"


@pytest.mark.parametrize("data, expected", [
    ({'battery': 0, 'id': 4, 'temp1': 0.0, 'temp2': 0.0},
     ['homes,Location=yourHome,Room=outside Temperature=0.0,Battery=0']),
    ({'battery': 0, 'id': 5, 'temp1': 10.0, 'temp2': -20.0},
     ['homes,Location=yourHome,Room=garage Temperature=-20.0,Battery=0',
     'homes,Location=yourHome,Room=battery Temperature=10.0,Battery=0', ]),
])
def test_parseToInfluxLine(data, expected):
    result = hemnode2mqtt.parseToInfluxLine(data)
    assert result == expected, f"Should be {expected}"
