
import defs

def selectChannel(ftdDevice, channel):
        ftdDevice.setBitMode(1<<defs.GPIO_CTRLA | 1<<defs.GPIO_CTRLB | 1<<defs.GPIO_CTRLC, 1)
        
        val=0
        val=defs.channelValueLookup[channel][0]<<defs.GPIO_CTRLA | defs.channelValueLookup[channel][1]<<defs.GPIO_CTRLB | defs.channelValueLookup[channel][2]<<defs.GPIO_CTRLC
        ftdDevice.write(bytes([val]))
                
