import math
import time
import wx
import wx.adv
import time
import sys
from threading import Thread, Lock
import threading
from pubsub import pub
import wx.lib.agw.hyperlink as hl

import ftd2xx as ftd

import filterbank_driver as fbDriver
from custom_button import CustomButton as CustomBtn

import defs
import images

MainFrameStyle  = wx.DEFAULT_FRAME_STYLE ^ (wx.RESIZE_BORDER|wx.MAXIMIZE_BOX)


class WxFrameClass(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(WxFrameClass, self).__init__(*args, **kwargs)
        
        self.SetBackgroundColour((255,255,255))
        
        self.InitUI()
        self.Centre()
        
        self.SetIcon(images.appIcon.Icon)
        self.selectedChannel = None
        self.ftdDevice = None
        self.isDeviceConnected=False
        
    def InitUI(self):
        
        self.Freeze()
        #init menubar
        self.initMenuBar()
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.AddSpacer(10)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        b = wx.Button(self, 10, "Connect", (20, 20))
        self.Bind(wx.EVT_BUTTON, self.onConnectItem, b)
        b.SetDefault()
        b.SetSize(b.GetBestSize())
        hbox.AddSpacer(10)
        hbox.Add(b,0,wx.EXPAND)
        hbox.AddSpacer(5)
        vbox.Add(hbox,0, wx.EXPAND)
        vbox.AddSpacer(10)
        self.connStatusLabel=wx.StaticText(self,-1, style = wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END)
        
        font = wx.Font()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        font.SetStyle(wx.FONTSTYLE_NORMAL)
        font.SetPointSize(14)
        self.connStatusLabel.SetFont(font) 
                
        hbox.Add(self.connStatusLabel, 0, wx.EXPAND, 0)
        
        if 'phoenix' in wx.PlatformInfo:
            hand_cursor = wx.Cursor(wx.CURSOR_HAND)
        else:
            hand_cursor = wx.StockCursor(wx.CURSOR_HAND)
            
        #create channel buttons
        self.channelButtons=[]
        for i in range(1,len(defs.channelNameLookup)+1):
            btn = CustomBtn(self, i, label=defs.channelNameLookup[i])
            btn.set_bg_color('#EEEEEE', '#00FF00', '#00DD00')
            btn.set_border((2, '#CCCCCC', 10))
            btn.set_padding((10, 10, 10, 10))
            btn.set_cursor(hand_cursor)
            btn.Bind(wx.EVT_BUTTON, self.onChBtnClicked)
            self.channelButtons.append(btn)
        
        buttonGrid = wx.GridSizer(math.ceil(len(defs.channelNameLookup)/4), 4, 5, 5)
        for btn in self.channelButtons:
            buttonGrid.Add(btn, 0, wx.EXPAND)
        
        bottomGrid = wx.GridSizer(1, 2, 5, 5)
        
        self.respImageList=[]
        for i in range(1,len(defs.channelNameLookup)+1):
            if i==8 and defs.PART_NUMBER==defs.PART_NUMBER_ATEK1001:
                self.respImageList.append(images.bypass)
            else:
                self.respImageList.append(images.catalog[str(i)])
            
        self.respImage=self.respImageList[0]
        self.respImage_bm = wx.StaticBitmap( self, wx.ID_ANY, self.respImage.Bitmap, wx.DefaultPosition, wx.DefaultSize, 0 )
        bottomGrid.Add(self.respImage_bm, 0, wx.ALIGN_LEFT | wx.ALIGN_BOTTOM | wx.ALL | wx.EXPAND, 0 )
        self.respImage_bm.Hide()
        
        self.logoImage=images.logo
        self.logoImage_bm = wx.StaticBitmap( self, wx.ID_ANY, self.logoImage.Bitmap, wx.DefaultPosition, wx.DefaultSize, 0 )
        bottomGrid.Add(self.logoImage_bm, 0, wx.ALIGN_RIGHT | wx.ALIGN_BOTTOM | wx.ALL, 10)
        
        mainGrid=wx.GridSizer(2, 1, 5, 5)
        mainGrid.Add(buttonGrid, 0, wx.ALL | wx.EXPAND, 5)
        mainGrid.Add(bottomGrid, 0, wx.EXPAND)
        
        vbox.Add(mainGrid, 1, wx.ALL | wx.EXPAND, 0)
        self.SetSizer(vbox)
        
        self.Bind(wx.EVT_SIZE, self.onResize)
        self.onResize(None)
        self.Thaw()

    def onResize(self, e):
        frame_size = self.GetSize()
        
        frame_w = (frame_size[0]-10) / 2
        frame_h = (frame_size[1]-10) / 2-30
        
        self.resizeRespGraph(frame_w, frame_h)
        self.resizeLogo(frame_w/3, frame_h)
        
        self.Refresh()
        self.Layout()
        
    def resizeRespGraph(self, frame_w, frame_h):
        if self.respImage != None:
            image_h=self.respImage.Image.GetHeight()/(self.respImage.Image.GetWidth()/frame_w)
            image_w=self.respImage.Image.GetWidth()/(self.respImage.Image.GetHeight()/frame_h)
            
            w=frame_w
            h=image_h
            if image_h>frame_h:
                h=frame_h
                w=image_w
                
            im=self.respImage.Image.Scale(int(w), int(h), wx.IMAGE_QUALITY_HIGH)
            self.respImage_bm.SetBitmap(wx.Image.ConvertToBitmap(im))

    def resizeLogo(self, frame_w, frame_h):
        image_h=self.logoImage.Image.GetHeight()/(self.logoImage.Image.GetWidth()/frame_w)
        image_w=self.logoImage.Image.GetWidth()/(self.logoImage.Image.GetHeight()/frame_h)
        
        w=frame_w
        h=image_h
        if image_h>frame_h:
            h=frame_h
            w=image_w
            
        im=self.logoImage.Image.Scale(int(w), int(h), wx.IMAGE_QUALITY_HIGH)
        self.logoImage_bm.SetBitmap(wx.Image.ConvertToBitmap(im))

    def deviceConnected(self):
        
        self.connectItem.Enable(False)
        self.disConnectItem.Enable(True)
        
        serial=self.getSerial()
        
        self.connStatusLabel.SetLabel(' Connected: '+defs.PART_NUMBER.replace('\n',' ')+' ['+serial+']')
        self.connStatusLabel.SetBackgroundColour((20,160,20))
        self.connStatusLabel.SetForegroundColour((255,255,255))
                
        self.isDeviceConnected=True
        
        #select channel 1
        self.channelButtons[0].SetFocus()
        self.onChBtnClicked(self.channelButtons[0])
        self.Layout()
        
    def deviceDisconnected(self):        
        self.connectItem.Enable(True)
        self.disConnectItem.Enable(False)
        
        self.connStatusLabel.SetLabel(' Disconnected')
        self.connStatusLabel.SetBackgroundColour((160,20,20))
        self.connStatusLabel.SetForegroundColour((255,255,255))        
        
        self.isDeviceConnected=False
        
        self.selectedChannel = None
        self.clearChannels()
        
        self.respImage_bm.Hide()
        
        self.Layout()
        
    def initMenuBar(self):
        menubar=wx.MenuBar()
        
        fileMenu=wx.Menu()
        
        fileItem=fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
        self.Bind(wx.EVT_MENU, self.OnQuit, fileItem)
        menubar.Append(fileMenu, '&File')
        
        toolsMenu=wx.Menu()
        self.connectItem=toolsMenu.Append(100, 'Connect', 'Connect')
        self.Bind(wx.EVT_MENU, self.onConnectItem, self.connectItem)
        
        self.disConnectItem=toolsMenu.Append(101, 'Disconnect', 'Disconnect')
        self.Bind(wx.EVT_MENU, self.onDisconnectItem, self.disConnectItem)
        menubar.Append(toolsMenu, '&Tools')
        
        helpMenu=wx.Menu()
        aboutItem=helpMenu.Append(102, 'About\tF1', 'About')
        self.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)
        menubar.Append(helpMenu, '&Help')
        
        self.SetMenuBar(menubar)
     
    def clearChannels(self):
        for btn in self.channelButtons:
            btn.set_bg_color('#EEEEEE', '#00FF00', '#00DD00')
                
    def onChBtnClicked(self, e):        
        channel=e.GetId()
        
        if self.isDeviceConnected:
            self.writeDevice(channel)
            if self.selectedChannel==None or self.selectedChannel!=channel:
                if self.selectedChannel!=None:
                    self.channelButtons[self.selectedChannel-1].set_bg_color('#EEEEEE', '#00FF00', '#00DD00')
                self.channelButtons[channel-1].set_bg_color( '#00DD00', '#00DD00', '#00DD00')
                self.selectedChannel=channel

                self.Freeze()
                self.respImage=self.respImageList[channel-1]
                self.respImage_bm.SetBitmap(self.respImage.Bitmap)
                self.respImage_bm.Show()
                self.Thaw()

                self.onResize(None)
        else:
            self.selectedChannel = channel
            wx.MessageBox('Please connect a device!', 'Error', wx.OK)


    def OnQuit(self, e):
        self.Close()
        
    def OnAbout(self, evt):
        # First we create and fill the info object
        info = wx.adv.AboutDialogInfo()
        logo = images.logo.Image
        logo = logo.Scale(200,int(200*234/713))
        logo = wx.Icon(logo.ConvertToBitmap())
        info.SetIcon(logo)
        info.Name = defs.SOFTWARE_NAME
        info.Version = defs.SOFTWARE_VERSION_STR
        info.Copyright = defs.COPYRIGHT
        info.WebSite = (defs.WEB_LINK,defs.WEB_TEXT)
        
        info.License = wordwrap(defs.LICENSE, 500, wx.ClientDC(self))
        
        # Then we call wx.AboutBox giving it that info object
        wx.adv.AboutBox(info)
    
    def onConnectItem(self,event):
        devs = self.listDevices()
        if len(devs) == 0:
            wx.MessageBox('No device is found to connect', 'Warning', wx.OK)
        else:
            dlg = wx.SingleChoiceDialog(
            self, 'Select Device to Connect\n\n!!!Connected Device is not shown.!!!', 'Device Selection',
            devs,
            wx.CHOICEDLG_STYLE
            )

            if dlg.ShowModal() == wx.ID_OK:
                if self.isDeviceConnected:
                    self.onDisconnectItem(None)
                dlg.Destroy()
                deviceName=dlg.GetStringSelection()
                if deviceName:
                    try:
                        self.ftdDevice=self.openDevice(deviceName)
                        self.deviceConnected()
                    except:
                        wx.MessageBox('Could not connect to device: '+ deviceName, 'Error', wx.OK)

    def onDisconnectItem(self, e):
        try:
            self.closeDevice()
            self.deviceDisconnected()
        except:
            wx.MessageBox('Error during disconnect', 'Error', wx.OK)
            pass

    def openDevice(self, deviceName):
        if not deviceName==defs.offlineModeSerial:
            return(ftd.openEx(str.encode(deviceName, 'UTF-8')))
        else:
            return(defs.offlineModeSerial)
        
    def listDevices(self):
        devs=[]
        if not self.ftdDevice == defs.offlineModeSerial:
            devs.append(defs.offlineModeSerial)
        try:
            ftdDevs = ftd.listDevices()
        except:
            ftdDevs = None
        if ftdDevs!=None:
            for dev in ftdDevs:
                if dev.decode('utf-8')!='':
                    devs.append(dev.decode('utf-8'))
        return(devs)
    
    def closeDevice(self):
        if not self.ftdDevice==defs.offlineModeSerial:
            self.ftdDevice.close()
        self.ftdDevice = None

    def writeDevice(self, channel):
        if not self.ftdDevice==defs.offlineModeSerial:
            fbDriver.selectChannel3(self.ftdDevice, channel)

    def getSerial(self):
        if self.ftdDevice==defs.offlineModeSerial:
            serial=defs.offlineModeSerial
        else:
            serial=self.ftdDevice.getDeviceInfo()['serial'].decode('utf-8')
        return(serial)


def main():
    app=wx.App()
        
    #show splash screen
    bitmap=wx.Image.ConvertToBitmap(images.logo.Image.Scale(480,int(images.logo.Image.GetHeight()/(images.logo.Image.GetWidth()/480)),wx.IMAGE_QUALITY_HIGH))
    splash=wx.adv.SplashScreen(bitmap, wx.adv.SPLASH_CENTER_ON_SCREEN | wx.adv.SPLASH_TIMEOUT, defs.SPLASH_SCREEN_TIMEOUT_MS, None)
    time.sleep(defs.SPLASH_SCREEN_TIMEOUT_MS/1000)
    
    wxFrame=WxFrameClass(None, title=defs.SOFTWARE_NAME, size=(600, 500), style=MainFrameStyle)
    wxFrame.Show()
    wxFrame.onConnectItem(None)
    if ftd == None:
        wx.MessageBox("Unable to find FTD2DXX.DLL\nPlease use proper FTDI's USB driver.", 'Error', wx.OK)
    app.MainLoop()
    
if __name__ == '__main__':
    main()
