import client.extraClientApi as clientApi

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
TouchEvent = clientApi.GetMinecraftEnum().TouchEvent
ClientSystem = clientApi.GetSystem("utils", "utilsClient")

class rankScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        print '==== %s ====' % 'init TestScreen'

        self.panel = '/panel0'
        self.closeBtn = self.panel+'/button0'
        self.title = self.panel+'/title'
        self.time = self.panel+'/time'
        self.rankContent = None

    def Create(self):
        print '==== %s ====' % 'rankScreen Create'
        self.AddTouchEventHandler(self.closeBtn, self.ExitUi, {"isSwallow": True})

    def InitScreen(self):
        print '==== %s ====' % 'uiScreen Init'

        # self.SetVisible('/panel0', False)
        self.SetVisible("", False)

    def ShowUi(self, title, content, time):
        ui = clientApi.GetUI('rank', 'rankUI')
        mPath = '/panel0/scroll_view0'
        # UC: UiControl
        scrollUC = ui.GetBaseUIControl(mPath).asScrollView()
        scroll = scrollUC.GetScrollViewContentPath()
        self.rankContent = scroll + '/content'

        print 'UISCRIPT CALL ShowUi'
        self.SetVisible("", True)
        self.SetText(self.title, title)
        self.SetText(self.rankContent, content)
        self.SetText(self.time, time)
        clientApi.SetInputMode(1)
        clientApi.HideSlotBarGui(True)

    def ExitUi(self, args):
        print 'UISCRIPT CALL ExitUi args=%s' % (args,)
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.close()

    def close(self):
        self.SetVisible("", False)
        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)