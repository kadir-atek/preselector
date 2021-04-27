#definitions

SPLASH_SCREEN_TIMEOUT_MS=1000

#Part selection
PART_NUMBER_ATEK1001='ATEK1001 Preselector'
PART_NUMBER_ATEK1002='ATEK1002 Filterbank'
PART_NUMBER=PART_NUMBER_ATEK1001

SOFTWARE_NAME=PART_NUMBER + ' GUI'
SOFTWARE_VERSION_MAJOR=1
SOFTWARE_VERSION_MINOR=0
SOFTWARE_VERSION_REV=0
SOFTWARE_VERSION_STR='v'+str(SOFTWARE_VERSION_MAJOR)+'.'+str(SOFTWARE_VERSION_MINOR)+'.'+str(SOFTWARE_VERSION_REV)

COPYRIGHT="(c) 2020 ATEK Mikrodalga AS"
WEB_LINK='https://www.atekmidas.com'
WEB_TEXT="ATEK MIDAS"
LICENSE="All rights reserved.\nwx.Widgets and wxPython is used under wxWindows Library License."

GPIO_CTRLA=0
GPIO_CTRLB=4
GPIO_CTRLC=2

#value=1 indexed channel number
#key=gpio states of [CTRLA, CTRLB, CTRLC]
channelValueLookup={
1: [0,0,0],
2: [0,1,1],
3: [0,0,1],
4: [1,0,1],
5: [0,1,0],
6: [1,1,0],
7: [1,0,0],
8: [1,1,1]
}

channelNameLookup={
1: 'Band 1',
2: 'Band 2',
3: 'Band 3',
4: 'Band 4',
5: 'Band 5',
6: 'Band 6',
7: 'Band 7'
}
if PART_NUMBER==PART_NUMBER_ATEK1001:
    channelNameLookup[8]='Bypass'
elif PART_NUMBER==PART_NUMBER_ATEK1002:
    channelNameLookup[8]='Band 8 (opt.)'

offlineModeSerial='OFFLINE MODE'
