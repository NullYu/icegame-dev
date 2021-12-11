import client.extraClientApi as clientApi

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
TouchEvent = clientApi.GetMinecraftEnum().TouchEvent
ClientSystem = clientApi.GetSystem("reg", "regClient")

class regScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        print '==== %s ====' % 'init TestScreen'

        self.panel = '/panel0'
        self.exitBtn = '/panel0/exit'
        self.regBtn = '/panel0/reg'
        self.doneInd = '/panel0/done'

        self.isDone = False

    def Create(self):
        print '==== %s ====' % 'regScreen Create'
        self.AddTouchEventHandler(self.exitBtn, self.ExitUi, {"isSwallow": True})
        self.AddTouchEventHandler(self.regBtn, self.Register, {"isSwallow": True})

    def Register(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and not self.isDone:
            self.isDone = True
            data = {

            }
            ClientSystem.ReturnToServer(data)
            self.close()

    def InitScreen(self):
        print '==== %s ====' % 'uiScreen Init'

        # self.SetVisible('/panel0', False)
        self.SetVisible("", False)
        self.SetVisible(self.doneInd, False)

    def ShowUi(self, isDone):
        print 'UISCRIPT CALL ShowUi'
        self.SetVisible("", True)
        self.isDone = isDone
        self.SetVisible(self.doneInd, self.isDone)
        self.SetVisible(self.regBtn, not self.isDone)
        clientApi.SetInputMode(1)
        clientApi.HideSlotBarGui(True)

    def ExitUi(self, args):
        print 'UISCRIPT CALL ExitUi args=%s' % (args,)
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.close()

    def close(self):
        self.SetVisible("", False)
        self.SetVisible(self.doneInd, False)
        self.isDone = False
        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)