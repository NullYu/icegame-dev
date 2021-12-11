import client.extraClientApi as clientApi
import datetime

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
TouchEvent = clientApi.GetMinecraftEnum().TouchEvent
ClientSystem = clientApi.GetSystem("fb", "fbClient")

class fbScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        print '==== %s ====' % 'init TestScreen'

        self.startScreen = '/image0'
        self.votePanel = '/panel0'
        self.reportBtn = self.votePanel + '/report'
        # Vote Button Pattern: /panel0/button0, common=/panel0/button
        self.timerPanel = '/panel1'
        self.timerInd = self.timerPanel + '/label2'
        self.themeInd = self.timerPanel + '/label3'

        self.isVoting = False
        self.alreadyReported = False
        self.time = 0

    def Create(self):
        print '==== %s ====' % 'rankScreen Create'
        for i in range(5):
            self.AddTouchEventHandler('/panel0/button%s' % i, self.VotePress, {"isSwallow": True})
        self.AddTouchEventHandler(self.reportBtn, self.ReportPress, {"isSwallow": True})

    def reset(self):
        self.SetVisible("", False)
        self.SetVisible(self.startScreen, False)
        self.SetVisible(self.votePanel, False)
        self.SetVisible(self.timerPanel, False)

    def InitScreen(self):
        print '==== %s ====' % 'uiScreen Init'

        # self.SetVisible('/panel0', False)
        self.SetVisible("", False)
        self.reset()

    def ShowStartScreen(self, theme, time):
        self.SetVisible("", True)
        self.SetVisible(self.startScreen, True)
        self.time = time
        clientApi.SetInputMode(1)
        comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        def a():
            self.SetVisible(self.timerPanel, True)
            self.SetText(self.timerInd, "%s:00" % time)
            self.SetText(self.themeInd, "§l§3主题： §f%s" % theme)
            self.SetVisible(self.startScreen, False)
            clientApi.SetInputMode(0)
            comp.AddRepeatedTimer(1.0, self.tick)
        comp.AddTimer(11.0, a)

    def tick(self):
        print 'tick'
        if self.time > 1:
            print 'going tick'
            self.time -= 1
            self.SetText(self.timerInd, str(datetime.timedelta(seconds=self.time)))

    def StartVoting(self):
        self.SetVisible(self.votePanel, True)
        if self.alreadyReported:
            self.SetVisible(self.reportBtn, False)
        self.isVoting = True

    def VotePress(self, args):
        event = args['TouchEvent']
        path = args['ButtonPath']
        if event == TouchEvent.TouchUp and self.isVoting:
            score = int(path.replace('/panel0/button', ''))
            ClientSystem.ReturnToServer({
                'score': score
            })

            self.SetVisible(self.votePanel, False)
            self.isVoting = False

    def ReportPress(self, args):
        event = args['TouchEvent']
        print 'report press'
        if event == TouchEvent.TouchUp and self.isVoting and not self.alreadyReported:
            print 'report press'
            self.SetVisible(self.votePanel, False)
            self.isVoting = False
            self.alreadyReported = True
            ClientSystem.ReturnToServer({
                'score': 0
            })

    def ExitUi(self, args):
        print 'UISCRIPT CALL ExitUi args=%s' % (args,)
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.close()

    def close(self):
        self.SetVisible("", False)
        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)