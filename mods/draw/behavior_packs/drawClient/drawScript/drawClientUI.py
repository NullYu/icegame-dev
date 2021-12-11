import client.extraClientApi as clientApi

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
TouchEvent = clientApi.GetMinecraftEnum().TouchEvent
ClientSystem = clientApi.GetSystem("draw", "drawClient")

class drawScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        print '==== %s ====' % 'init TestScreen'

        self.menu = '/menu'
        self.closeBtn = '/closebtn'
        self.closeHint = '/image1'
        self.prev = self.menu + '/prev'
        self.next = self.menu + '/next'
        self.singleBtn = self.menu+'/single'
        self.tenBtn = self.menu+'/ten'
        self.singleInvalid = self.menu+'/singleInvalid'
        self.tenInvalid = self.menu+'/tenInvalid'

        self.pools = self.menu+'/pools'
        self.labelPack = self.pools+'/label_pack'

        self.draw = '/draw'
        self.drawContent = self.draw + '/content'
        self.drawDesc = self.draw + '/expire'

        self.cover = self.draw + '/cover'

        # var declaration
        self.credits = 0
        self.pool = None
        self.drawArgs = None
        self.coveredSq = 0

    def Create(self):
        print '==== %s ====' % 'drawScreen Create'
        self.AddTouchEventHandler(self.closeBtn, self.ExitUi, {"isSwallow": True})
        self.AddTouchEventHandler(self.prev, self.BtnPlaceholder, {"isSwallow": True})
        self.AddTouchEventHandler(self.next, self.BtnPlaceholder, {"isSwallow": True})
        self.AddTouchEventHandler(self.singleBtn, self.ChoiceSingle, {"isSwallow": True})
        self.AddTouchEventHandler(self.tenBtn, self.BtnPlaceholder, {"isSwallow": True})

        for i in range(102):
            self.AddTouchEventHandler(self.cover + '/button%s' % (i,), self.Uncover, {"isSwallow": True})

    def BtnPlaceholder(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            return

    def ChoiceSingle(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            if self.credits > 15:
                response = {
                    'choice': 'single',
                    'pool': self.pool
                }
                ClientSystem.ReturnToServer(response)
                self.credits -= 16
                self.UpdateCredits()

    def Uncover(self, args):
        event = args['TouchEvent']
        path = args['ButtonPath']
        if event == TouchEvent.TouchDown:
            print 'uncover args=%s' % (args,)
            self.SetVisible(path, False)
            self.coveredSq -= 1
            if self.coveredSq <= 50:
                self.SetVisible(self.closeBtn, True)
                self.SetVisible(self.closeHint, False)

    def InitScreen(self):
        print '==== %s ====' % 'uiScreen Init'

        # self.SetVisible('/panel0', False)
        self.SetVisible("", False)
        self.SetVisible(self.menu, True)

    def UpdateCredits(self):
        self.SetVisible(self.singleInvalid, False)
        self.SetVisible(self.tenInvalid, False)
        print 'credits update'

        # TODO do 10 combo
        if self.credits < 160 or True:
            print 'cannot afford 160'
            self.SetVisible(self.tenInvalid, True)
        if self.credits < 16:
            print 'cannot afford 16'
            self.SetVisible(self.singleInvalid, False)

    def ShowUi(self, credits):
        print 'UISCRIPT CALL ShowUi'
        self.SetVisible("", True)
        self.credits = credits
        self.SetVisible(self.menu, True)
        self.SetVisible(self.draw, False)
        self.UpdateCredits()
        self.SetVisible(self.labelPack, True)
        self.coveredSq = 0
        self.pool = 1
        print 'credits=%s' % self.credits
        clientApi.SetInputMode(1)
        clientApi.HideSlotBarGui(True)

    def Draw(self, data):
        self.SetVisible("", True)
        self.coveredSq = 102
        self.drawArgs = data
        self.SetVisible(self.menu, False)
        self.SetVisible(self.draw, True)
        self.SetVisible(self.cover, True)
        for i in range(102):
            self.SetVisible(self.cover+'/button%s' % (i,), True)

        self.SetVisible(self.closeBtn, False)
        self.SetVisible(self.closeHint, True)
        self.SetText(self.drawContent, data['prizeName'])
        self.SetText(self.drawDesc, data['desc'])

        self.SetVisible(self.draw+'/level3', False)
        self.SetVisible(self.draw+'/level2', False)
        self.SetVisible(self.draw+'/level1', False)
        self.SetVisible(self.draw+'/level0', False)
        self.SetVisible(self.draw+'/level%s'%(data['level'],), True)

        clientApi.SetInputMode(1)
        clientApi.HideSlotBarGui(True)

    def ExitUi(self, args):
        print 'UISCRIPT CALL ExitUi args=%s' % (args,)
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.close()

    def close(self):
        self.SetVisible("", False)
        self.SetVisible(self.menu, True)
        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)