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
    (b'\x00', None),
    (b'\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', {'battery': 0, 'id': 4, 'temp1': 0.0, 'temp2': 0.0}),
    (b'\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', {'battery': 0, 'id': 5, 'temp1': 0.0, 'temp2': 0.0}),
    (b'\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf1\x01', {'battery': 1466, 'id': 5, 'temp1': 0.0, 'temp2': 0.0}),
    (b'\x05\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00\x00\x00', {'battery': 0, 'id': 5, 'temp1': 10.0, 'temp2': 0.0}),
    (b'\x05\x00\x00\x00\x7f\xff\x00\x00\x00\x00\x00\x00\x00\x00', {'battery': 0, 'id': 5, 'temp1': -12.9, 'temp2': 0.0}),
    (b'\x05\x00\x00\x00\x00\x00\x7f\xff\x00\x00\x00\x00\x00\x00', {'battery': 0, 'id': 5, 'temp1': 0, 'temp2': -12.9}),
])
def test_decodeMsg(data, expected):
    result = hemnode2mqtt.decodeMsg(data)
    assert result == expected, f"Should be {expected}"

@pytest.mark.parametrize("data, expected", [
    (b'\x00', None),
    (b'\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', {'battery': 0, 'id': 4, 'temp1': 0.0, 'temp2': 0.0}),
    (b'\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', {'battery': 0, 'id': 5, 'temp1': 0.0, 'temp2': 0.0}),
    (b'\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf1\x01', {'battery': 1466, 'id': 5, 'temp1': 0.0, 'temp2': 0.0}),
    (b'\x05\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00\x00\x00', {'battery': 0, 'id': 5, 'temp1': 10.0, 'temp2': 0.0}),
    (b'\x05\x00\x00\x00\x7f\xff\x00\x00\x00\x00\x00\x00\x00\x00', {'battery': 0, 'id': 5, 'temp1': -12.9, 'temp2': 0.0}),
    (b'\x05\x00\x00\x00\x00\x00\x7f\xff\x00\x00\x00\x00\x00\x00', {'battery': 0, 'id': 5, 'temp1': 0, 'temp2': -12.9}),
])
def test_parseToInfluxLine(data, expected):
    result = hemnode2mqtt.parseToInfluxLine(data)
    assert result == expected, f"Should be {expected}"