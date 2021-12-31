# -*- coding: utf-8 -*-
import client.extraClientApi as clientApi
import datetime

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
TouchEvent = clientApi.GetMinecraftEnum().TouchEvent
ClientSystem = clientApi.GetSystem("event", "eventClient")

class eventScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        print '==== %s ====' % 'init EventScreen'

        self.infoBtn = '/button0'

        self.infoPanel = '/infoPanel'
        self.closeBtn = self.infoPanel + '/button1'

        self.timerPanel = '/timerPanel'
        self.timerCaptionInd = self.timerPanel + '/label0'
        self.timerInd = self.timerPanel + '/label1'

        self.timer = 3600

    def epoch2Datetime(self, epoch):
        ts = datetime.datetime.fromtimestamp(int(epoch))
        return ts.strftime('%M:%S')

    def Create(self):
        print '==== %s ====' % 'eventScreen Create'
        self.AddTouchEventHandler(self.closeBtn, self.ExitUi, {"isSwallow": True})
        self.AddTouchEventHandler(self.infoBtn, self.ShowUi, {"isSwallow": True})

    def InitScreen(self):
        print '==== %s ====' % 'uiScreen Init'

        # self.SetVisible('/panel0', False)
        self.SetVisible("", True)
        self.SetVisible(self.infoPanel, False)
        self.SetVisible(self.timerPanel, False)

    def ShowUi(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.SetVisible(self.infoPanel, True)
            self.SetVisible(self.infoBtn, False)
            clientApi.SetInputMode(1)
            clientApi.HideSlotBarGui(True)

    def ExitUi(self, args):
        print 'UISCRIPT CALL ExitUi args=%s' % (args,)
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.close()

    def UpdateTimer(self, timer):
        self.SetVisible(self.timerPanel, True)

        if timer <= 0:
            self.SetText(self.timerCaptionInd, "§l§c祝§f各§2位§c玩§f家")
            self.SetText(self.timerInd, "§l§f新年快乐！！！")
        else:
            self.SetText(self.timerInd, "%s" % datetime.timedelta(seconds=int(timer)))
            if timer % 2 == 0:
                self.SetText(self.timerCaptionInd, "§l§c元旦§f庆典 §6倒计时")
            else:
                self.SetText(self.timerCaptionInd, "§l§c元旦§f庆典 §e倒计时")

    def close(self):
        self.SetVisible(self.infoPanel, False)
        self.SetVisible(self.infoBtn, True)
        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)