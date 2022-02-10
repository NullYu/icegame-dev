# -*- coding: utf-8 -*-
import client.extraClientApi as clientApi
import random
import datetime
import time

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
        self.paperDoll = '/paperDoll'

        self.pausePanel = '/pausePanel'
        self.pauseReturnBtn = self.pausePanel + '/button0'
        self.pauseDisconnectBtn = self.pausePanel + '/button1'

        self.deathPanel = '/deathPanel'
        self.deathPanelBackground = self.deathPanel + '/image1'
        self.deathReasonIndicator = self.deathPanel + '/image3'
        self.deathIndicatorBlur = self.deathPanel + '/image2'
        self.missionTimeInd = self.deathPanel + '/label0'
        self.endDisconnectBtn = self.deathPanel + '/button2'

        self.prepPanel = '/prepPanel'
        self.prepTimerInd = self.prepPanel + '/label1'

        self.gamePanel = '/gamePanel'
        self.gameTimerInd = self.gamePanel + '/label2'
        self.showEvacPointsBtn = self.gamePanel + '/button3'

        self.deployTimer = 17.0
        self.deployHasStarted = False
        self.deployTimerHandle = None

        self.evacTimer = 3600

    def SetProgressbarValue(self, path, value):
        progressBarUIControl = clientApi.GetUI('tarkov', 'tarkovUI').GetBaseUIControl(path).asProgressBar()
        progressBarUIControl.SetValue(value)

    def Create(self):
        print '==== %s ====' % 'tarkovScreen Create'
        uiNode = clientApi.GetUI('tarkov', 'tarkovUI')

        self.AddTouchEventHandler(self.pauseReturnBtn, self.resumeGame, {"isSwallow": False})
        self.AddTouchEventHandler(self.pauseDisconnectBtn, self.disconnectGame, {"isSwallow": False})
        self.AddTouchEventHandler(self.endDisconnectBtn, self.endGame, {"isSwallow": False})
        self.AddTouchEventHandler(self.showEvacPointsBtn, self.showEvacPoints, {"isSwallow": False})

    def InitScreen(self):
        print '==== %s ====' % 'uiScreen Init V5UI'

        # self.SetVisible('/panel0', False)
        self.SetVisible("", True)

        path = self.paperDoll
        param = {
            "entity_id": clientApi.GetLocalPlayerId(),
            "scale": 0.5,
            "render_depth": -50,
            "init_rot_y": 60,
            "molang_dict": {"variable.liedownamount": 1}
        }
        doll = clientApi.GetUI('tarkov', 'tarkovUI').GetBaseUIControl(path).asNeteasePaperDoll()
        doll.RenderEntity(param)

        self.SetVisible(self.pausePanel, False)
        self.SetVisible(self.deathPanel, False)
        self.SetVisible(self.prepPanel, True)
        self.SetVisible(self.gamePanel, False)

        self.SetText(self.prepTimerInd, '等待玩家进入')

        self.SetVisible(self.overlay, True)

        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)

    def StartDeploy(self):
        self.deployHasStarted = True
        comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        self.deployTimerHandle = comp.AddRepeatedTimer(0.01, self.doDeployCountdown)

    def doDeployCountdown(self):
        self.SetText(self.prepTimerInd, '00:%s%s' % (format(self.deployTimer, '.2f'), random.randint(0, 9)))
        self.deployTimer -= 0.01

        if self.deployTimer <= 0:
            comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
            comp.CancelTimer(self.deployTimerHandle)

            self.SetVisible(self.gamePanel, True)

    def UpdateEvacTimer(self, timer):
        self.evacTimer = timer
        self.SetText(self.gameTimerInd, time.strftime('%H:%M:%S', time.gmtime(self.evacTimer)))

    def resumeGame(self, args):
        pass

    def disconnectGame(self, args):
        pass

    def endGame(self, args):
        pass

    def showEvacPoints(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            response = {
                'operation': 'showEvacPoints'
            }
            ClientSystem.ReturnToServer(response)

    def tick(self):
        pass

    def reset(self):
        pass

    def ExitUi(self, args):
        print 'UISCRIPT CALL ExitUi args=%s' % (args,)
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.close()

    def close(self):
        self.SetVisible("", False)
        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)