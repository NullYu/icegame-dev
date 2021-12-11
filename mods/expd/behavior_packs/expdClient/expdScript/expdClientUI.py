import client.extraClientApi as clientApi
import datetime

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
TouchEvent = clientApi.GetMinecraftEnum().TouchEvent
ClientSystem = clientApi.GetSystem("expd", "expdClient")

class expdScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        print '==== %s ====' % 'init expdScreen'

        self.dialogPanel = '/panel0'
        self.endDateInd = self.dialogPanel + '/label0'
        self.idInd = self.dialogPanel + '/label1'

        self.permInd = '/button1'
        self.tempInd = '/button0'

        self.showDialog = False
        self.isPerm = False

        self.endDate = None
        self.id = None

    def epoch2Datetime(self, epoch):
        ts = datetime.datetime.fromtimestamp(int(epoch))
        return ts.strftime('%Y-%m-%d %H:%M:%S')

    def Create(self):
        print '==== %s ====' % 'expdScreen Create'
        self.AddTouchEventHandler(self.permInd, self.ShowDialog, {"isSwallow": False})
        self.AddTouchEventHandler(self.tempInd, self.ShowDialog, {"isSwallow": False})

    def InitScreen(self):
        print '==== %s ====' % 'uiScreen Init'

        self.SetVisible(self.dialogPanel, False)
        self.SetVisible(self.permInd, False)
        self.SetVisible(self.tempInd, False)
        self.SetVisible("", False)

    def ShowDialog(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            if self.showDialog:
                pass
            else:
                # show the dialog
                self.SetVisible(self.dialogPanel, True)
                self.SetText(self.idInd, str(self.id))
                if self.endDate > 0:
                    self.SetText(self.endDateInd, self.epoch2Datetime(self.endDate))
                else:
                    self.SetText(self.endDateInd, "永久")

    def ShowUi(self, id, endDate):
        print 'UISCRIPT CALL ShowUi'
        self.SetVisible("", True)
        self.id = id
        self.endDate = endDate
        if endDate < 0:
            self.isPerm = True
            self.SetVisible(self.permInd, True)
        else:
            self.SetVisible(self.tempInd, True)

    def ExitUi(self, args):
        print 'UISCRIPT CALL ExitUi args=%s' % (args,)
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.close()

    def close(self):
        self.SetVisible("", False)
        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)