import client.extraClientApi as clientApi

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
TouchEvent = clientApi.GetMinecraftEnum().TouchEvent
ClientSystem = clientApi.GetSystem("mega", "megaClient")

class megaScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        print '==== %s ====' % 'init TestScreen'

        self.hintPanel = '/panel0'
        self.hintInd = self.hintPanel + '/image0'

        self.containerWasSafe = True

    def Create(self):
        print '==== %s ====' % 'megaScreen Create'
        # self.AddTouchEventHandler(self.closeBtn, self.ExitUi, {"isSwallow": True})

    def InitScreen(self):
        print '==== %s ====' % 'uiScreen Init'

        # self.SetVisible('/panel0', False)
        self.SetVisible("", True)
        self.SetVisible(self.hintPanel, False)

    def UpdateContainerStatus(self, data):
        status = data['status']
        progress = data['progress']
        uiNode = clientApi.GetUI('mega', 'megaUI')

        if status == 0:
            self.SetVisible(self.hintPanel, False)
            if not self.containerWasSafe:
                self.SetVisible(self.hintPanel, True)
                uiNode.GetBaseUIControl(self.hintInd).asImage().SetSprite("textures/ui/megaUI/hint-stoppedsecuring")
                def a():
                    self.SetVisible(self.hintPanel, False)
                comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
                comp.AddTimer(3.0, a)
            self.containerWasSafe = True

        elif status == 1:
            self.SetVisible(self.hintPanel, True)
            uiNode.GetBaseUIControl(self.hintInd).asImage().SetSprite("textures/ui/megaUI/hint-securing")
            self.containerWasSafe = False
        elif status == 2:
            self.SetVisible(self.hintPanel, True)
            uiNode.GetBaseUIControl(self.hintInd).asImage().SetSprite("textures/ui/megaUI/hint-contested")
            self.containerWasSafe = False
        elif status == 3:
            self.SetVisible(self.hintPanel, False)
            self.containerWasSafe = True

    def ExitUi(self, args):
        print 'UISCRIPT CALL ExitUi args=%s' % (args,)
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.close()

    def close(self):
        self.SetVisible("", False)
        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)