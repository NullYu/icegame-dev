# -*- coding: utf-8 -*-
import client.extraClientApi as clientApi

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
TouchEvent = clientApi.GetMinecraftEnum().TouchEvent
ClientSystem = clientApi.GetSystem("v5match", "v5matchClient")

class v5matchScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        print '==== %s ====' % 'init TestScreen'

        self.matchPanel = '/panel0'
        self.matchImage = self.matchPanel + '/image0'
        self.matchLabel = self.matchPanel + '/label0'

        self.entrancePanel = '/panel1'
        self.startMatchBtn = self.entrancePanel + '/button0'
        self.exitMatchBtn = self.entrancePanel + '/button1'

        self.inQueue = False
        self.matchFound = False

    def Create(self):
        print '==== %s ====' % 'rankScreen Create'
        self.AddTouchEventHandler(self.startMatchBtn, self.startMatch, {"isSwallow": True})
        self.AddTouchEventHandler(self.exitMatchBtn, self.exitMatch, {"isSwallow": True})

    def InitScreen(self):
        print '==== %s ====' % 'uiScreen Init'

        # self.SetVisible('/panel0', False)
        self.SetVisible("", True)
        self.SetVisible(self.matchPanel, False)
        self.SetVisible(self.exitMatchBtn, False)

    def startMatch(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and not self.inQueue:
            response = {
                'operation': 'start'
            }
            ClientSystem.ReturnToServer(response)

    def exitMatch(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and self.inQueue:
            response = {
                'operation': 'exit'
            }
            ClientSystem.ReturnToServer(response)

    def StartMatchmake(self):
        self.SetVisible(self.matchPanel, True)
        self.SetVisible(self.matchLabel, False)

        self.SetVisible(self.startMatchBtn, False)
        self.SetVisible(self.exitMatchBtn, True)

        self.inQueue = True

    def ExitMatchmake(self):

        self.SetVisible(self.matchPanel, False)
        self.SetVisible(self.startMatchBtn, True)
        self.SetVisible(self.exitMatchBtn, False)

        self.inQueue = False

    def UpdateInfo(self, data):
        if self.matchFound:
            return

        status = data['status']
        count = data['count']

        if status == 'wait':
            self.SetVisible(self.matchLabel, True)
            if count < 10:
                self.SetText(self.matchLabel, "%s/10 名玩家已就绪" % count)
            else:
                self.SetText(self.matchLabel, "正在等待房间分配")

        elif status == 'start':
            self.matchFound = False
            self.SetVisible(self.matchLabel, False)
            self.SetVisible(self.exitMatchBtn, False)

            uiNode = clientApi.GetUI('v5match', 'v5matchUI')
            uiNode.GetBaseUIControl(self.matchImage).asImage().SetSprite("textures/ui/v5matchUI/matchmake1")

    def ShowUi(self, title, content, time):
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