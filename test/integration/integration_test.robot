*** Settings ***
Library               Process
Library               String
Library               OperatingSystem
Library               SerialLibrary
Library               MQTTLibrary
Suite Setup           Setup Serial Port and MQTT Broker
Suite Teardown        Teardown Serial Port and MQTT Broker

*** Variables ***
${MOSQUITTO_CONF}     ${EXECDIR}/test/integration/mosquitto.conf
${MOSQUITTO_LOG}      ${EXECDIR}/test/integration/mosquitto.log
${PTYA}               ${EMPTY}
${PTYB}               ${EMPTY}

*** Keywords ***
Setup Serial Port
    Remove File  ${TEMPDIR}${/}socat.log
    ${process} =  Start Process  socat  -dd  -lf${TEMPDIR}${/}socat.log  pty,raw,echo\=0  pty,raw,echo\=0  stderr=STDOUT
    Sleep  0.1
    ${socatlog} =  Get File  ${TEMPDIR}${/}socat.log
    ${matches} =  Get Regexp Matches  ${socatlog}  \/dev\/pts\/\\d+
    Set Global Variable  ${PTYA}  ${matches}[0]
    Set Global Variable  ${PTYB}  ${matches}[1]

Setup MQTT Broker
    # in case of ungraceful exit of previous test, remove the mosquitto container
    Run Process  docker  stop  mosquitto_hemnode2mqtt_test
    Run Process  docker  rm  mosquitto_hemnode2mqtt_test
    ${process} =  Run Process  docker  run  -d  --rm  -p  1883:1883  -v  ${EXECDIR}/test/integration/mosquitto.conf:/mosquitto/config/mosquitto.conf:ro  --name  mosquitto_hemnode2mqtt_test  eclipse-mosquitto:1.6  shell=yes

Setup Serial Port and MQTT Broker
    Setup Serial Port
    Setup MQTT Broker

Teardown Serial Port
    Log  not implemented

Teardown MQTT Broker
    Run Process  docker  stop  mosquitto_hemnode2mqtt_test
    Run Process  docker  rm  mosquitto_hemnode2mqtt_test

Teardown Serial Port and MQTT Broker
    Teardown Serial Port
    Teardown MQTT Broker
    Terminate All Processes

Start hemnode2mqtt
    ${result} =  Start Process  hemnode2mqtt  env:PYTHONUNBUFFERED=False  env:HEMNODE2MQTT_MQTT_PORT=${1883}  env:HEMNODE2MQTT_MQTT_USE_TLS=False  env:HEMNODE2MQTT_MQTT_BROKER=127.0.0.1  env:HEMNODE2MQTT_SERIAL_DEV=${PTYA}  alias=hemnode2mqtt  stderr=STDOUT
    ${result} =  Wait For Process  timeout=2 secs
    Process Should Be Running

Stop hemnode2mqtt
    Terminate Process  hemnode2mqtt
    ${result} =  Get Process Result  hemnode2mqtt
    Log To Console  ${result.stdout}
    Log To Console  ${result.stderr}

hemnode2mqtt can connect to broker
    ${result} =  Run Process  docker  logs  mosquitto_hemnode2mqtt_test  stderr=STDOUT
    ${matches} =  Get Regexp Matches  ${result.stdout}  New client connected from .* as hemnode2mqtt
    Should Be Equal  ${{ len(${matches}) >= 1}}  ${True}  Client was not able to connect to broker! ${result.stdout}

sends message to broker
    Connect                 127.0.0.1
    ${messages}=  Subscribe And Validate  topic=homey/yourHome  qos=1  timeout=5  payload=homes,Location=yourHome,Room=outside Temperature=0.1,Battery=0
    Log to Console  ${messages}
    [Teardown]              Disconnect

Send and Verify Temperature 1 Node Message
    [Arguments]     ${node_id}=04  ${temp1_hex}=  ${temp1_influx}=
    Write Data     ${node_id} 0c 00 00 ${temp1_hex} 00 00 00 00 00 00 00 00 9e 0d 0a
    Connect                 127.0.0.1
    IF  '${node_id}' == '04'
        Set Local Variable  ${node_room}  outside
    ELSE IF  '${node_id}' == '05'
        Set Local Variable  ${node_room}  battery
    END
    Subscribe And Validate  topic=homey/yourHome  qos=1  timeout=2  payload=homes,Location=yourHome,Room=${node_room} Temperature=${temp1_influx},Battery=0,rssi=-79.0
    [Teardown]              Disconnect

Send and Verify Battery Node Message
    [Arguments]     ${node_id}=04  ${bat_hex}=  ${bat_influx}=
    Write Data     ${node_id} 0c 00 00 00 00 00 00 00 00 00 00 ${bat_hex} 9e 0d 0a
    Connect                 127.0.0.1
    IF  '${node_id}' == '04'
        Set Local Variable  ${node_room}  outside
    ELSE IF  '${node_id}' == '05'
        Set Local Variable  ${node_room}  battery
    END
    Subscribe And Validate  topic=homey/yourHome  qos=1  timeout=2  payload=homes,Location=yourHome,Room=${node_room} Temperature=0.0,Battery=${bat_influx},rssi=-79.0
    [Teardown]              Disconnect

Send and Verify RSSI Node Message
    [Arguments]     ${node_id}=04  ${rssi_hex}=  ${rssi_influx}=
    Write Data     ${node_id} 0c 00 00 00 00 00 00 00 00 00 00 00 00 ${rssi_hex} 0d 0a
    Connect                 127.0.0.1
    IF  '${node_id}' == '04'
        Set Local Variable  ${node_room}  outside
    ELSE IF  '${node_id}' == '05'
        Set Local Variable  ${node_room}  battery
    END
    Subscribe And Validate  topic=homey/yourHome  qos=1  timeout=2  payload=homes,Location=yourHome,Room=${node_room} Temperature=0.0,Battery=0,rssi=${rssi_influx}
    [Teardown]              Disconnect

Setup Serial Test
    Add Port  ${PTYB}  timeout=0.2
    Start hemnode2mqtt

Teardown Serial Test
    Stop hemnode2mqtt
    Delete All Ports

*** Test Cases ***
Temperature 1 works
    [Setup]  Setup Serial Test
    [Template]  Send and Verify Temperature 1 Node Message
    #   node_id      temp1_hex    temp1_influx
          04           01 00          0.1
          04           01 01         25.7
          04           01 FF        -25.5
          04           FF FF         -0.1
          05           FF FF         -0.1
    [Teardown]  Teardown Serial Test

Battery works
    [Setup]  Setup Serial Test
    [Template]  Send and Verify Battery Node Message
    #   node_id      bat_hex    bat_influx
          04          01 00             3
          04          01 01           758
          04          01 FF        192528
          04          FF FF        193277
          05          FF FF        193277
    [Teardown]  Teardown Serial Test

RSSI works
    [Setup]  Setup Serial Test
    [Template]  Send and Verify RSSI Node Message
    #   node_id      bat_hex    bat_influx
          04           00           -0.0
          04           01           -0.5
          04           02           -1
          04           FF         -127.5
          05           FF         -127.5
    [Teardown]  Teardown Serial Test