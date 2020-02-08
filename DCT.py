from numpy import fft,array,arange,zeros,dot,transpose
from math import sqrt,cos,pi
from numpy import fft,array,arange,zeros,dot,transpose
from math import sqrt,cos,pi
import time
import os
import numpy
import wx
from PIL import Image
from threading import *
qmatrix = numpy.array([[ 16 , 11 , 10 , 16 , 24  , 40  , 51  , 61 ],
           [ 12 , 12 , 14 , 19 , 26  , 58  , 60  , 55 ],
           [ 14 , 13 , 16 , 24 , 40  , 57  , 69  , 56 ],
           [ 14 , 17 , 22 , 29 , 51  , 87  , 80  , 62 ],
           [ 18 , 22 , 37 , 56 , 68  , 109 , 103 , 77 ],
           [ 24 , 35 , 55 , 64 , 81  , 104 , 113 , 92 ],
           [ 49 , 64 , 78 , 87 , 103 , 121 , 120 , 101],
           [ 72 , 92 , 95 , 98 , 112 , 100 , 103 , 99 ] ])

Timage = None
TIMG = None

EVT_RESULT_ID = wx.NewId()

def EVT_RESULT(win,func):
    # define result event #
    win.Connect(-1,-1, EVT_RESULT_ID, func)

class ResultEvent(wx.PyEvent):
    def __init__(self,data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data

class WorkerThread(Thread):
    def __init__(self,notify_window):
        Thread.__init__(self)
        self._notify_window = notify_window
        self._want_abort = 0
        self.start()

    def run(self):
        global Timage
        global TIMG
        dct = DCT()
        PD = ProgressDialog()
        width,height = Timage.size
        TIMG = zeros((height,width,3))
        colcount = width  / 8
        rowcount = height / 8
        for i in range(rowcount):
            progress = 100 * i / rowcount
            PD.SetProgress(progress)
            for j in range(colcount):
                img = Timage.crop((j*8,i*8,j*8+8,i*8+8))
                RGB = numpy.array(img)
                R = zeros((8,8))
                G = zeros((8,8))
                B = zeros((8,8))
                for y in range(8):
                    for x in range(8):
                        R[y][x] = RGB[y][x][0]
                        G[y][x] = RGB[y][x][1]
                        B[y][x] = RGB[y][x][2]
                Rc = dct.transform(R)
                Rd = dct.itransform(Rc)
                Gc = dct.transform(G)
                Gd = dct.itransform(Gc)
                Bc = dct.transform(B)
                Bd = dct.itransform(Bc)
                for y in range(8):
                    for x in range(8):
                        if Rd[y][x] > 255: Rd[y][x] = 255
                        if Gd[y][x] > 255: Gd[y][x] = 255
                        if Bd[y][x] > 255: Bd[y][x] = 255
                        if Rd[y][x] < 0: Rd[y][x] = 0
                        if Gd[y][x] < 0: Gd[y][x] = 0
                        if Bd[y][x] < 0: Bd[y][x] = 0
                        TIMG[i*8+x][j*8+y][0] = Rd[y][x]
                        TIMG[i*8+x][j*8+y][1] = Gd[y][x]
                        TIMG[i*8+x][j*8+y][2] = Bd[y][x]
        wx.PostEvent(self._notify_window,ResultEvent(10))
        
    

class DCT(object):

    def __init__(self):
        pass
       
    def __transKernel(self,N):
        A = zeros((N,N))
        for x in xrange(0,N):
            for u in xrange(0,N):
                if u==0:
                    A[x][u] = sqrt(1/float(N))
                else:
                    A[x][u] = sqrt(2/float(N))*cos(pi*(2*x+1)*u/float(2*N))
        return A

    def __itransKernel(self,N):
        A = zeros((N,N))
        for x in xrange(0,N):
            for u in xrange(0,N):
                if x==0:
                    A[x][u] = sqrt(1/float(N))
                else:
                    A[x][u] = sqrt(2/float(N))*cos(pi*(2*u+1)*x/float(2*N))                   
        return A
    def __multiply(self,a,b):
        A = zeros((len(a),len(a)))
        for i in xrange(len(a)):
            for j in xrange(len(a)):
                A[j][i] = a[i][j]*b[i][j]
        return A
    def __add(self,a):
        A = zeros((len(a),len(a)))
        for i in xrange(len(a)):
            for j in xrange(len(a)):
                A[j][i] = int(a[i][j]+128)
        return A
    def __subtract(self,a):
        A = zeros((len(a),len(a)))
        for i in xrange(len(a)):
            for j in xrange(len(a)):
                A[j][i] = int(a[i][j]-128)
        return A
        
    def transform(self,m):
        m = self.__subtract(m)
        tk = self.__transKernel(len(m))
        t1 = dot(m,tk)
        t1 = transpose(t1)
        t1 = dot(t1,tk)
        t1 = transpose(t1)
        quant = t1/qmatrix
        qq = zeros((len(m),len(m)),dtype=numpy.int8)
        for i in xrange(0,len(t1)):
            for j in xrange(0,len(t1)):
                qq[i][j] = int(round(quant[i][j],0))
        return qq
       
    def itransform(self,m):
        R = self.__multiply(qmatrix.T,m.T)
        tk = self.__itransKernel(len(m))
        t1 = dot(R,tk)
        t1 = transpose(t1)
        t1 = dot(t1,tk)
        return self.__add(t1)
    
#############################################################################################
class Example(wx.Frame):
    
    def __init__(self, *args, **kwargs):
        super(Example, self).__init__(*args, **kwargs)
        self.args = args
        self.kwargs = kwargs
        self.fname=""    
        self.InitUI()        
        self.SetIcon(wx.Icon('favicon.ico',wx.BITMAP_TYPE_ICO))
        
    def InitUI(self):    

        menubar = wx.MenuBar() 
        self.fileMenu = wx.Menu()
        fopen = self.fileMenu.Append(wx.ID_OPEN, 'Open Image', 'Load Image')
        self.Bind(wx.EVT_MENU, self.OnOpen,fopen)
        fsave = self.fileMenu.Append(12, 'Save Image', 'Save Image')
        self.Bind(wx.EVT_MENU, self.OnSave,fsave)
        fitem = self.fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
        self.Bind(wx.EVT_MENU, self.OnQuit, fitem)
        menubar.Append(self.fileMenu, '&File')

        self.fMenu3 = wx.Menu()
        self.DCTo = self.fMenu3.Append(13,'DCT Transformation', 'Discrete Cosine Transformation operation')
        self.Bind(wx.EVT_MENU, self.DCT,self.DCTo)
        menubar.Append(self.fMenu3, '&Operation')

        menuAbout = wx.Menu()
        menuAbout.Append(2, "&About...", "About this program")
        self.Bind(wx.EVT_MENU, self.OnAbout, id=2)
        menubar.Append(menuAbout, '&Help')

        self.SetMenuBar(menubar)
        self.opened = False
        self.worker = None
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        EVT_RESULT(self,self.OnResult)

        self.statusBar = self.CreateStatusBar()
        self.Bind(wx.EVT_SIZE, self.OnSize)

        self.SetSize((800, 520))
        self.SetTitle('DCT image compression')
        self.Centre()
        self.Show(True)

    def OnSize(self,event):
        if self.opened == True:
            self.dc.DrawBitmap(self.bitmap, 10,10)
        

    def DCT(self, event):
        if not self.worker:
            self.statusBar.SetStatusText('Running DCT...')
            self.worker = WorkerThread(self)

    def OnOpen(self, event):
        global Timage
        filters = 'Image files (*.png;*.jpg;*.gif)|*.png;*.jpg;*.gif'
        dialog = wx.FileDialog(self, message="Open an Image...", defaultDir=os.getcwd(), defaultFile="", wildcard=filters, style=wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            self.opened = True
            self.fname = dialog.GetPath()
            self.image = Image.open(self.fname)
            width, height = self.image.size
            if width > 760 :
                aspect = width * 1.0 / height
                maxheight = 760 / aspect
                height = maxheight
                self.image = self.image.resize((760,int(maxheight)))
            if height > 550 :
                self.SetSize((width+40,height+100))
            Timage = self.image
            self.bitmap = PilImageToWxBitmap(self.image)
            self.dc.DrawBitmap(self.bitmap, 10,10)
            self.statusBar.SetStatusText('Image Loaded') 
        dialog.Destroy()

    def OnResult(self,event):
        global TIMG
        self.statusBar.SetStatusText('DCT has finished')
        self.image = Image.fromarray(numpy.uint8(TIMG))
        self.bitmap = PilImageToWxBitmap(self.image)
        self.dc.DrawBitmap(self.bitmap, 10,10)

    def OnPaint(self, event):
        self.dc = wx.PaintDC(self)
        
    def OnSave(self, event):
        #
        tmp = 0
        
    def OnQuit(self, e):
        self.Close()
        
    def OnAbout(self, event):
        AboutFrame().Show()

############################################################################################
class ProgressDialog(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self, wx.GetApp().TopWindow,2,"DCT progress",(750,400),(300,60))
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.pbar = wx.Gauge(self,-1,100, (5,5) , (280,20))
        self.Show(True)

    def SetProgress(self,val):
        self.pbar.SetValue(val)

    def OnPaint(self,event):
        self.dc = wx.PaintDC(self)
        
        
        
############################################################################################
class AboutFrame(wx.Frame):

    title = "About"

    def __init__(self):
        wx.Frame.__init__(self, wx.GetApp().TopWindow, title=self.title)
        panel = wx.Panel(self,-1)
        text = "Created by\nMartins Fridenbergs\n2012\nDeveloped in Python"
        font = wx.Font(10,wx.ROMAN,wx.NORMAL,wx.NORMAL)
        statictext = wx.StaticText(panel,-1,text,(30,20),style = wx.ALIGN_CENTRE)
        statictext.SetFont(font)
        self.Center()
        self.SetSize((200,150))        


############################################################################################# 
def PilImageToWxBitmap( myPilImage ) :
    return WxImageToWxBitmap( PilImageToWxImage( myPilImage ) ) 

def PilImageToWxImage( myPilImage ):
    myWxImage = wx.EmptyImage( myPilImage.size[0], myPilImage.size[1] )
    myWxImage.SetData( myPilImage.convert( 'RGB' ).tostring() )
    return myWxImage

def WxImageToWxBitmap( myWxImage ) :
    return myWxImage.ConvertToBitmap()         

#############################################################################################
    
dct_matrix =  [ [ 154, 123, 123, 123, 123, 123, 123,  136],
                [ 192, 180, 136, 154, 154, 154, 136,  110],
                [ 254, 198, 154, 154, 180, 154, 123,  123],
                [ 239, 180, 136, 180, 180, 166, 123,  123],
                [ 180, 154, 136, 167, 166, 149, 136,  136],
                [ 128, 136, 123, 136, 154, 180, 198,  154],
                [ 123, 105, 110, 149, 136, 136, 180,  166],
                [ 110, 136, 123, 123, 123, 136, 154,  136] ]

#############################################################################################
if __name__=="__main__":
    global main
    ex = wx.App()
    main = Example(None)
    ex.MainLoop()
