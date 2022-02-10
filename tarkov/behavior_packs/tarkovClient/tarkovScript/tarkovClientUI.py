import client.extraClientApi as clientApi
import random

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
TouchEvent = clientApi.GetMinecraftEnum().TouchEvent
ClientSystem = clientApi.GetSystem("tarkov", "tarkovClient")

class tarkovScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        print '==== %s ====' % 'init tarkovScreen'

        self.overlay = '/overlay'

        self.pausePanel = '/pausePanel'
        self.pauseReturnBtn = self.pausePanel + '/button0'
        self.pauseDisconnectBtn = self.pausePanel + '/button1'

        self.deathPanel = '/deathPanel'
        self.deathPanelBackground = self.deathPanel + '/image1'
        self.deathReasonIndicator = self.deathPanel + '/image3'
        self.deathIndicatorBlur = self.deathPanel + '/image2'
        self.endPlayerDoll = self.deathPanel + '/netease_paper_doll0'
        self.missionTimeInd = self.deathPanel + '/label0'
        self.endDisconnectBtn = self.deathPanel + '/button2'

    def SetProgressbarValue(self, path, value):
        progressBarUIControl = clientApi.GetUI('tarkov', 'tarkovUI').GetBaseUIControl(path).asProgressBar()
        progressBarUIControl.SetValue(value)

    def Create(self):
        print '==== %s ====' % 'tarkovScreen Create'
        uiNode = clientApi.GetUI('tarkov', 'tarkovUI')

        self.AddTouchEventHandler(self.pauseReturnBtn, self.resumeGame, {"isSwallow": False})
        self.AddTouchEventHandler(self.pauseDisconnectBtn, self.disconnectGame, {"isSwallow": False})
        self.AddTouchEventHandler(self.endDisconnectBtn, self.endGame, {"isSwallow": False})

    def InitScreen(self):
        print '==== %s ====' % 'uiScreen Init V5UI'

        # self.SetVisible('/panel0', False)
        self.SetVisible("", True)
        self.SetVisible(self.pausePanel, False)
        self.SetVisible(self.deathPanel, False)

        self.SetVisible(self.overlay, True)

        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)

    def resumeGame(self, args):
        pass

    def disconnectGame(self, args):
        pass

    def endGame(self, args):
        pass

    def tick(self):
        pass

    def reset(self):
        self.selectionsData = None

        self.defuserTimer = 44
        self.defuseStarted = False
        self.timerText = '0:02:50'

        self.eqpDur1 = 20
        self.eqpDur2 = 20
        self.eqpDur2Max = 20
        self.eqpDur3 = 0
        self.eqpDur3Max = 0
        self.slot1 = None
        self.slot2 = None
        self.slotSkill = None
        self.fixProgress = 0
        self.fixStarted = False
        self.currentEquipped = 0

        self.defuserPlantProgress = 0

        self.reinfsLeft = 0

        self.SetVisible("", True)
        self.SetVisible(self.prepPanel, False)
        self.SetVisible(self.timerPanel, False)
        self.SetVisible(self.eqpPanel, False)
        self.SetVisible(self.reinforcementPanel, False)
        self.SetVisible(self.defuserPlantPanel, False)
        self.resetPrepPanel()

    def ExitUi(self, args):
        print 'UISCRIPT CALL ExitUi args=%s' % (args,)
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.close()

    def close(self):
        self.SetVisible("", False)
        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)