import client.extraClientApi as clientApi

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
TouchEvent = clientApi.GetMinecraftEnum().TouchEvent
ClientSystem = clientApi.GetSystem("vkick", "vkickClient")

class vkickScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        print '==== %s ====' % 'init TestScreen'

        self.isVoting = False
        self.ayeVotes = 0
        self.nayVotes = 0

        self.votePanel = '/panel0'
        self.targetNameInd = self.votePanel + '/name'
        self.ayeButton = self.votePanel + '/button0'
        self.nayButton = self.votePanel + '/button1'
        self.ayeInd = self.votePanel + '/label0'
        self.nayInd = self.votePanel + '/label1'

        self.resultPanel = '/panel1'
        self.resultAyeInd = self.resultPanel + '/pass'
        self.resultNayInd = self.resultPanel + '/fail'

    def Create(self):
        print '==== %s ====' % 'rankScreen Create'
        self.AddTouchEventHandler(self.ayeButton, self.voteAye, {"isSwallow": True})
        self.AddTouchEventHandler(self.nayButton, self.voteNay, {"isSwallow": True})

    def reset(self):
        self.SetVisible(self.votePanel, True)
        self.SetVisible(self.resultPanel, False)
        self.SetVisible("", False)

        self.SetVisible(self.ayeInd, False)
        self.SetVisible(self.nayInd, False)
        self.SetVisible(self.resultAyeInd, False)
        self.SetVisible(self.resultNayInd, False)

    def InitScreen(self):
        print '==== %s ====' % 'uiScreen Init'

        self.reset()

    def voteAye(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and self.isVoting:
            ClientSystem.ReturnToServer({'vote': True})
            self.SetVisible(self.ayeButton, False)
            self.SetVisible(self.nayButton, False)
            self.SetVisible(self.ayeInd, True)
            self.SetVisible(self.nayInd, True)
            self.isVoting = False

    def voteNay(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and self.isVoting:
            ClientSystem.ReturnToServer({'vote': False})
            self.SetVisible(self.ayeButton, False)
            self.SetVisible(self.nayButton, False)
            self.SetVisible(self.ayeInd, True)
            self.SetVisible(self.nayInd, True)
            self.isVoting = False

    def StartVote(self, name, startAsVoted=False):

        print 'UISCRIPT CALL ShowUi'
        self.SetVisible("", True)
        self.SetText(self.targetNameInd, name)
        self.SetText(self.ayeInd, '§l§a1')
        self.SetText(self.nayInd, '§l§c1')
        self.SetVisible(self.ayeButton, True)
        self.SetVisible(self.nayButton, True)
        self.isVoting = True

        self.ayeVotes = 1
        self.nayVotes = 1

        if startAsVoted:
            self.SetVisible(self.ayeButton, False)
            self.SetVisible(self.nayButton, False)
            self.SetVisible(self.ayeInd, True)
            self.SetVisible(self.nayInd, True)
            self.isVoting = False

    def UpdateVote(self, aye, nay):
        self.ayeVotes = aye
        self.nayVotes = nay

        self.SetText(self.ayeInd, '§l§a'+str(self.ayeVotes))
        self.SetText(self.nayInd, '§l§c'+str(self.nayVotes))

    def EndVote(self, suc):
        print 'voting ended'
        self.isVoting = False
        self.SetVisible(self.votePanel, False)
        self.SetVisible(self.resultPanel, True)

        if suc:
            self.SetVisible(self.resultAyeInd, True)
        else:
            self.SetVisible(self.resultNayInd, True)

        comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        comp.AddTimer(5.0, self.close)

    def ExitUi(self, args):
        print 'UISCRIPT CALL ExitUi args=%s' % (args,)
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.close()

    def close(self):
        self.reset()
        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)