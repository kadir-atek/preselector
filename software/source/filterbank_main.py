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

wxFrame=None

app=None

ftdDevice=None
offlineMode=False
offlineConnected=False

devSelMutex = Lock()
devConnMutex = Lock()

ConstFrameStyle = wx.DEFAULT_FRAME_STYLE ^ (wx.RESIZE_BORDER|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX)
MainFrameStyle = wx.DEFAULT_FRAME_STYLE ^ (wx.RESIZE_BORDER|wx.MAXIMIZE_BOX)
    
def scale_bitmap(bitmap, width, height=None):
    image = wx.Bitmap.ConvertToImage(bitmap)
    
    return wx.Image.ConvertToBitmap(scale_image(image, width, height))

def scale_image(image, width, height=None):
    if height==None:
        height=image.GetHeight()/(image.GetWidth()/width)
        
    return image.Scale(int(width), int(height), wx.IMAGE_QUALITY_HIGH)

class AboutFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(AboutFrame, self).__init__(*args, **kwargs)        
        self.SetBackgroundColour((255,255,255))
        self.Bind(wx.EVT_KILL_FOCUS, self.keepFocus)
        
        topGrid=wx.GridSizer(1, 2, 0, 0)
        
        logo=scale_image(wx.Image('resources/logo.png', wx.BITMAP_TYPE_ANY),100)
        logo_bm = wx.StaticBitmap(self, wx.ID_ANY, wx.Image.ConvertToBitmap(logo), wx.DefaultPosition, wx.DefaultSize, 0 )
        topGrid.Add(logo_bm, 0, wx.ALL | wx.EXPAND, 10)
      
        soft=wx.StaticText(self, -1, defs.SOFTWARE_NAME+' '+defs.SOFTWARE_VERSION_STR)
        topGrid.Add(soft, 0, wx.ALL, 10)
        
        mainGrid=wx.GridSizer(3, 1, 0, 0)
        
        #top grid
        mainGrid.Add(topGrid, 0, wx.ALIGN_CENTER, 5)
        
        mainGrid.Add(wx.StaticText(self, -1, 'Supported devices:\n'+defs.PART_NUMBER), 0, wx.ALIGN_CENTER, 0)
        
        #hyperlink
        hyplink=hl.HyperLinkCtrl(self, -1, defs.HOME, URL=defs.HOME)
        hyplink.SetBackgroundColour((255,255,255))
        hyplink.AutoBrowse(True)
        hyplink.SetColours("BLUE", "BLUE", "BLUE")
        hyplink.EnableRollover(True)
        hyplink.SetUnderlines(False, True, True)
        hyplink.OpenInSameWindow(True)
        hyplink.UpdateLink()
        mainGrid.Add(hyplink, 0, wx.ALIGN_CENTER, 10)
        
        self.SetSizer(mainGrid)
        
        self.Centre() 
        self.Show() 

    def keepFocus(self, e):
        print('keep focused')
        self.SetFocus()
        
class DeviceSelectFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(DeviceSelectFrame, self).__init__(*args, **kwargs) 
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.Bind(wx.EVT_SHOW, self.showed)
        self.Bind(wx.EVT_KILL_FOCUS, self.keepFocus)
        
        devSelMutex.acquire()
        
        panel = wx.Panel(self)

        self.deviceBox = wx.ListBox(panel, style = wx.LB_SINGLE)
        
        buttonGrid=wx.GridSizer(1, 2, 0, 0)    
        
        self.refreshButton = wx.Button(panel, label="Refresh")
        self.refreshButton.Bind(wx.EVT_BUTTON, self.onRefreshButton)
        buttonGrid.Add(self.refreshButton, 0, wx.ALL, 5)
        
        connectButton = wx.Button(panel, label="Connect")
        connectButton.Bind(wx.EVT_BUTTON, self.onConnectButton)
        buttonGrid.Add(connectButton, 0, wx.ALL, 5)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.deviceBox, 1, wx.LEFT | wx.RIGHT | wx.TOP | wx.CENTER | wx.EXPAND, 10)
        sizer.Add(buttonGrid, 0, wx.ALL | wx.CENTER, 10)
        panel.SetSizer(sizer)
                
        self.Centre() 
        self.Show(True)

    def showed(self, e):    
        if e.GetEventObject().IsShown():
            print('device select showed')
            fireRefreshEvent = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED,self.refreshButton.GetId())
            fireRefreshEvent.SetInt(1)
            fireRefreshEvent.SetEventObject(self.refreshButton)
            self.refreshButton.GetEventHandler().ProcessEvent(fireRefreshEvent)
        
    def keepFocus(self, e):
        print('keep focused')
        self.SetFocus()
        
    def onRefreshButton(self, e):
        self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
        e.GetEventObject().Disable()
        devConnMutex.acquire()
        
        devs=[defs.offlineModeSerial]
        ftdDevs = ftd.listDevices()
        if ftdDevs!=None:
            for dev in ftdDevs:
                if dev.decode('utf-8')!='':
                    devs.append(dev.decode('utf-8')) 
        print('found devices: '+str(devs))        
          
        sel=self.deviceBox.GetStringSelection()
        self.deviceBox.Clear()
        self.deviceBox.InsertItems(devs, 0)
                       
        devConnMutex.release()
        e.GetEventObject().Enable()
        self.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))
            
    def onConnectButton(self, e):
        devConnMutex.acquire()
        global ftdDevice
        global offlineMode
        global offlineConnected
        
        deviceName=self.deviceBox.GetStringSelection()
        if deviceName==defs.offlineModeSerial:
            offlineMode=True
            
        if deviceName:
            try:
                if offlineMode:
                    offlineConnected=True
                else:
                    ftdDevice=ftd.openEx(str.encode(deviceName, 'UTF-8'))
                    
                self.Close()
            except:
                wx.MessageBox('Could not connect to device: '+deviceName, 'Error', wx.OK)
        devConnMutex.release()
        
    def OnCloseWindow(self, event):
        self.Destroy()
        devSelMutex.release()
        
class WxFrameClass(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(WxFrameClass, self).__init__(*args, **kwargs)
        self.Bind(wx.EVT_SHOW, self.showed)
        
        self.SetBackgroundColour((255,255,255))
        
        self.InitUI()
        self.Centre()
        
        self.isDeviceConnected=False
        
    def InitUI(self):
        
        #init menubar
        self.initMenuBar()
       
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        self.connStatusLabel=wx.StaticText(self,-1, style = wx.ALIGN_LEFT | wx.ST_ELLIPSIZE_END)
        
        font = wx.Font() 
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        font.SetStyle(wx.FONTSTYLE_NORMAL)
        font.SetPointSize(14)
        self.connStatusLabel.SetFont(font) 
                
        vbox.Add(self.connStatusLabel, 0, wx.EXPAND, 0)
        
        if 'phoenix' in wx.PlatformInfo:
            hand_cursor = wx.Cursor(wx.CURSOR_HAND)
        else:
            hand_cursor = wx.StockCursor(wx.CURSOR_HAND)
            
        #create channel buttons
        self.channelButtons=[]
        for i in range(1,9):
            btn = CustomBtn(self, i, label=defs.channelNameLookup[i])
            btn.set_bg_color('#EEEEEE', '#00FF00', '#00DD00')
            btn.set_border((2, '#CCCCCC', 10))
            btn.set_padding((10, 10, 10, 10))
            btn.set_cursor(hand_cursor)
            btn.Bind(wx.EVT_BUTTON, self.onChBtnClicked)
            self.channelButtons.append(btn)
        
        buttonGrid = wx.GridSizer(2, 4, 5, 5)
        for btn in self.channelButtons:
            buttonGrid.Add(btn, 0, wx.EXPAND)
        
        bottomGrid = wx.GridSizer(1, 2, 5, 5)
        
        self.respImageList=[]
        for i in range(1,9):
            if i==8 and defs.PART_NUMBER==defs.PART_NUMBER_ATEK1001:
                self.respImageList.append(wx.Image('resources/bypass.png', wx.BITMAP_TYPE_ANY))
            else:
                self.respImageList.append(wx.Image('resources/band'+str(i)+'.png', wx.BITMAP_TYPE_ANY))
            
        self.respImage=self.respImageList[0]
        self.respImage_bm = wx.StaticBitmap( self, wx.ID_ANY, wx.Image.ConvertToBitmap(self.respImage), wx.DefaultPosition, wx.DefaultSize, 0 )
        bottomGrid.Add(self.respImage_bm, 0, wx.ALIGN_LEFT | wx.ALIGN_BOTTOM | wx.ALL | wx.EXPAND, 0 )
               
        self.logoImage=wx.Image('resources/logo.png', wx.BITMAP_TYPE_ANY)
        self.logoImage_bm = wx.StaticBitmap( self, wx.ID_ANY, wx.Image.ConvertToBitmap(self.logoImage), wx.DefaultPosition, wx.DefaultSize, 0 )
        bottomGrid.Add(self.logoImage_bm, 0, wx.ALIGN_RIGHT | wx.ALIGN_BOTTOM | wx.ALL, 10)
        
        mainGrid=wx.GridSizer(2, 1, 5, 5)
        mainGrid.Add(buttonGrid, 0, wx.ALL | wx.EXPAND, 5)
        mainGrid.Add(bottomGrid, 0, wx.EXPAND)
        
        vbox.Add(mainGrid, 1, wx.ALL | wx.EXPAND, 0)
        self.SetSizer(vbox)
        
        self.Bind(wx.EVT_SIZE, self.onResize)
        
        pub.subscribe(self.deviceConnected, 'deviceConnected')
        pub.subscribe(self.deviceDisconnected, 'deviceDisconnected')
            
    def onResize(self, e):
        frame_size = self.GetSize()
        
        frame_w = (frame_size[0]-10) / 2
        frame_h = (frame_size[1]-10) / 2-30
        
        self.resizeRespGraph(frame_w, frame_h)
        self.resizeLogo(frame_w/3, frame_h)
        
        self.Refresh()
        self.Layout()
        
    def resizeRespGraph(self, frame_w, frame_h):
        image_h=self.respImage.GetHeight()/(self.respImage.GetWidth()/frame_w)
        image_w=self.respImage.GetWidth()/(self.respImage.GetHeight()/frame_h)
        
        w=frame_w
        h=image_h
        if image_h>frame_h:
            h=frame_h
            w=image_w
            
        im=scale_image(self.respImage, w, h)
        self.respImage_bm.SetBitmap(wx.Image.ConvertToBitmap(im))
    
    def resizeLogo(self, frame_w, frame_h):
        image_h=self.logoImage.GetHeight()/(self.logoImage.GetWidth()/frame_w)
        image_w=self.logoImage.GetWidth()/(self.logoImage.GetHeight()/frame_h)
        
        w=frame_w
        h=image_h
        if image_h>frame_h:
            h=frame_h
            w=image_w
            
        im=scale_image(self.logoImage, w, h)
        self.logoImage_bm.SetBitmap(wx.Image.ConvertToBitmap(im))
    
    def showed(self, e):
        if e.GetEventObject().IsShown():
            print('main showed')
            #self.onConnectItem(None)
        
    def deviceConnected(self):
        self.selectedChannel=None
        
        self.connectItem.Enable(False)
        self.disConnectItem.Enable(True)
        
        global ftdDevice
        global offlineMode
        
        serial=None
        if offlineMode:
            serial=defs.offlineModeSerial
        else:
            serial=ftdDevice.getDeviceInfo()['serial'].decode('utf-8')
            
        self.connStatusLabel.SetLabel(' Connected: '+defs.PART_NUMBER+' ['+serial+']')
        self.connStatusLabel.SetBackgroundColour((20,160,20))
        self.connStatusLabel.SetForegroundColour((255,255,255))
                
        self.isDeviceConnected=True
        
        #select channel 1
        fireChannelEvent = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED,self.channelButtons[0].GetId())
        fireChannelEvent.SetInt(1)
        fireChannelEvent.SetEventObject(self.channelButtons[0])
        self.channelButtons[0].GetEventHandler().ProcessEvent(fireChannelEvent)
        
        self.Layout()
        
    def deviceDisconnected(self):        
        self.connectItem.Enable(True)
        self.disConnectItem.Enable(False)
        
        self.connStatusLabel.SetLabel(' Disconnected')
        self.connStatusLabel.SetBackgroundColour((160,20,20))
        self.connStatusLabel.SetForegroundColour((255,255,255))        
        
        self.isDeviceConnected=False
        
        self.clearChannels()
        
        self.respImage_bm.Hide()
        
        self.Layout()
        
    def initMenuBar(self):
        menubar=wx.MenuBar()
        
        fileMenu=wx.Menu()
        
        #newItem=fileMenu.Append(wx.ID_NEW, 'New', 'New')
        #self.Bind(wx.EVT_MENU, self.OnNew, newItem)
        
        #saveItem=fileMenu.Append(wx.ID_SAVE, 'Save', 'Save')
        #self.Bind(wx.EVT_MENU, self.OnSave, saveItem)
        
        #saveAsItem=fileMenu.Append(wx.ID_SAVEAS, 'Save As...', 'Save As')
        #self.Bind(wx.EVT_MENU, self.OnSaveAs, saveAsItem)
        
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
        aboutItem=helpMenu.Append(102, 'About', 'About')
        self.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)
        menubar.Append(helpMenu, '&Help')
        
        self.SetMenuBar(menubar)
     
    def clearChannels(self):
        for btn in self.channelButtons:
            btn.set_bg_color('#EEEEEE', '#00FF00', '#00DD00')
                
    def onChBtnClicked(self, e):        
        channel=e.GetId()
        
        if self.isDeviceConnected:
            global ftdDevice
            global fbDriver
            global offlineMode
            
            if not offlineMode:
                fbDriver.selectChannel(ftdDevice, channel)
            
            self.clearChannels()
            self.channelButtons[channel-1].set_bg_gradient(('#00DD00','#00CC00'), ('#00DD00','#00CC00'), ('#00DD00','#00CC00'))
            
            if self.selectedChannel==None or self.selectedChannel!=channel:
                self.selectedChannel=channel
                
                self.respImage=self.respImageList[channel-1]
                self.respImage_bm.SetBitmap(wx.Image.ConvertToBitmap(self.respImage))
                self.respImage_bm.Show()
                self.onResize(None)
        else:
            wx.MessageBox('Please connect a device!', 'Error', wx.OK)
        
    def OnNew(self, e):
        print('on new')
        
    def OnSave(self, e):
        print('on save')
        
    def OnSaveAs(self, e):
        print('on save as')
        
    def OnQuit(self, e):
        print('on quit')
        self.Close()
        
    def OnAbout(self, e):
        AboutFrame(parent=self, title='About', size=(320, 200), style=ConstFrameStyle).Show()
    
    def onConnectItem(self, e):
        DeviceSelectFrame(parent=self, title='Device Selection', size=(320, 200), style=ConstFrameStyle).Show()
    
    def onDisconnectItem(self, e):
        try:
            global ftdDevice
            global offlineMode
            global offlineConnected
            
            if offlineMode:
                offlineConnected=False
            else:
                ftdDevice.close()
        except:
            print('unable to disconnect from the device')
        
def TaskFtdiDetect():
    global ftdDevice
    global offlineMode
    global offlineConnected
    
    wx.CallAfter(pub.sendMessage,'deviceDisconnected')
    
    while True:
        devSelMutex.acquire()
        try:
            if offlineMode:
                if not offlineConnected:
                    raise IOError('device not connected')
            else:
                ftdDevice.getStatus()
                
            if not wxFrame.isDeviceConnected:
                wx.CallAfter(pub.sendMessage,'deviceConnected')
        except:
            if wxFrame.isDeviceConnected:
                wx.CallAfter(pub.sendMessage,'deviceDisconnected')
            
        devSelMutex.release()
      
        time.sleep(0.5)
    
def main():
    global app
    app=wx.App()
        
    #show splash screen
    bitmap=scale_bitmap(wx.Bitmap('resources/logo.png'), 480)
    splash=wx.adv.SplashScreen(bitmap, wx.adv.SPLASH_CENTER_ON_SCREEN | wx.adv.SPLASH_TIMEOUT, defs.SPLASH_SCREEN_TIMEOUT_MS, None)
    time.sleep(defs.SPLASH_SCREEN_TIMEOUT_MS/1000)
    
    global wxFrame
    wxFrame=WxFrameClass(None, title=defs.SOFTWARE_NAME, size=(600, 480), style=MainFrameStyle)
    wxFrame.Show()
    
    deviceDetTh = threading.Thread(target=TaskFtdiDetect, daemon=True)
    deviceDetTh.start()
    
    app.MainLoop()
    
if __name__ == '__main__':
    main()
    
    
    
    
    
    
    
    
    
    
    
    