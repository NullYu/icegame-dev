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

        self.fadeInTimerHandle = None

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

    def startElementFade(self, path, duration, OnEndCallback=None, isFadeIn=True):
        comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        if isFadeIn:
            self.SetAlpha(path, 0.0)
            def a(param):
                p = param[0]
                d = param[1]
                cb = param[2]
                alpha = self.GetAlpha(p)
                if alpha >= 1:
                    comp.CancelTimer(self.fadeInTimerHandle)
                    if cb: cb()
                    return 
                else:
                    self.SetAlpha(path, alpha + (0.01 / d))
        else:
            self.SetAlpha(path, 1.0)
            def a(param):
                p = param[0]
                d = param[1]
                cb = param[2]
                alpha = self.GetAlpha(p)
                if alpha <= 0:
                    comp.CancelTimer(self.fadeInTimerHandle)
                    if cb: cb()
                    return
                else:
                    self.SetAlpha(path, alpha - (0.01 / d))

        comp.AddRepeatedTimer(0.01, a, (path, duration, OnEndCallback))


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
            def a():
                self.SetVisible(self.prepPanel, False)
            self.startElementFade(self.prepPanel, 1.0, a, False)
            self.startElementFade(self.overlay, 1.0, None, False)

    def UpdateEvacTimer(self, timer):
        self.evacTimer = timer
        self.SetText(self.gameTimerInd, time.strftime('%H:%M:%S', time.gmtime(self.evacTimer)))

    def DisplayDeath(self, data):
        timer = data['timer']
        cause = data['cause']
        uiNode = clientApi.GetUI('tarkov', 'tarkovUI')
        self.SetVisible(self.gamePanel, False)
        self.SetVisible(self.pausePanel, False)

        # set the indicator
        if cause == 'kia':
            uiNode.GetBaseUIControl(self.deathReasonIndicator).asImage().SetSprite('textures/ui/tarkovUI/kia-indicator')
        elif cause == 'mia':
            uiNode.GetBaseUIControl(self.deathReasonIndicator).asImage().SetSprite('textures/ui/tarkovUI/mia-indicator')
        elif cause == 'ee':
            uiNode.GetBaseUIControl(self.deathReasonIndicator).asImage().SetSprite('textures/ui/tarkovUI/ee-indicator')
        elif cause == 'suc':
            uiNode.GetBaseUIControl(self.deathReasonIndicator).asImage().SetSprite('textures/ui/tarkovUI/suc-indicator')

        # set the indicator blur and background
        if cause == 'suc':
            uiNode.GetBaseUIControl(self.deathIndicatorBlur).asImage().SetSprite('textures/ui/tarkovUI/suc-blur')
            uiNode.GetBaseUIControl(self.deathIndicatorBlur).asImage().SetSprite('textures/ui/tarkovUI/deathscreen-suc')

        self.SetVisible(self.overlay, True)
        self.SetVisible(self.deathPanel, True)
        self.startElementFade(self.overlay, 1.0, None)


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