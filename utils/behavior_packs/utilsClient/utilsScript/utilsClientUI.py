import client.extraClientApi as clientApi

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
TouchEvent = clientApi.GetMinecraftEnum().TouchEvent
ClientSystem = clientApi.GetSystem("utils", "utilsClient")

class utilsScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        print '==== %s ====' % 'init TestScreen'

        self.dialogType = None
        self.disable = False

        self.dialogPanel = '/dialogpanel'
        self.dialogOkBtn = self.dialogPanel+'/okbtn'
        self.dialogCancelBtn = self.dialogPanel+'/cancelbtn'
        self.dialogMsg = self.dialogPanel+'/dialoglabel'

        self.hubBtn = '/hubbtn'
        # self.activity1 = '/activity1'

        self.winpanel = '/winpanel'
        self.winName = self.winpanel + '/name'
        self.winMusic = self.winpanel + '/musica'

        self.textPanel = '/textboard'
        self.textBoard = self.textPanel + '/text'

        self.specPanel = '/specPanel'
        self.specNextBtn = self.specPanel + '/button0'
        self.specPrevBtn = self.specPanel + '/button1'
        self.specReportBtn = self.specPanel + '/button3'
        self.specTargetInd = self.specPanel + '/label4'

        # TODO change this to FALSE when finished debugging
        self.hasReported = True

    def Create(self):
        print '==== %s ====' % 'uiScreen Create'

        self.AddTouchEventHandler(self.hubBtn, self.HubBtn, {"isSwallow": True})
        # self.AddTouchEventHandler(self.activity1, self.Activity1, {"isSwallow": True})

        self.AddTouchEventHandler(self.dialogOkBtn, self.DialogOk, {"isSwallow": True})
        self.AddTouchEventHandler(self.dialogCancelBtn, self.DialogCancel, {"isSwallow": True})
        self.AddTouchEventHandler(self.specNextBtn, self.SpecNext, {"isSwallow": True})
        self.AddTouchEventHandler(self.specPrevBtn, self.SpecPrev, {"isSwallow": True})
        self.AddTouchEventHandler(self.specReportBtn, self.SpecReport, {"isSwallow": True})

    def Activity1(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            args = {
                'action': 'activity',
                'value': 1
            }
            ClientSystem.ReturnToServer(args)

    def DialogCancel(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.SetVisible(self.dialogPanel, False)
            self.dialogType = None
            self.disable = False

            clientApi.SetInputMode(0)
            clientApi.HideSlotBarGui(False)

    def DialogOk(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            if self.dialogType == 'hub':
                self.SetVisible(self.dialogPanel, False)
                self.dialogType = None
                self.disable = False

                args = {
                    'action': 'hub'
                }
                ClientSystem.ReturnToServer(args)

            clientApi.SetInputMode(0)
            clientApi.HideSlotBarGui(False)

    def HubBtn(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and not self.disable:
            self.ShowDialog("您即将回城，请确认")
            self.dialogType = 'hub'

    def ShowDialog(self, msg):
        self.disable = True

        self.SetVisible(self.dialogPanel, True)
        self.SetText(self.dialogMsg, msg)
        clientApi.SetInputMode(1)
        clientApi.HideSlotBarGui(True)

    def InitScreen(self):
        print '==== %s ====' % 'uiScreen Init'

        # self.SetVisible('/panel0', False)
        self.SetVisible("", True)
        self.SetVisible(self.winpanel, False)
        self.SetVisible(self.hubBtn, True)
        self.SetVisible(self.dialogPanel, False)
        self.SetVisible(self.textPanel, False)
        self.SetVisible(self.specPanel, False)

    def SpecNext(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            response = {
                'action': 'spec',
                'operation': 'next'
            }
            ClientSystem.ReturnToServer(response)

    def SpecPrev(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            response = {
                'action': 'spec',
                'operation': 'prev'
            }
            ClientSystem.ReturnToServer(response)

    def SpecReport(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and not self.hasReported:
            # TODO complete report logic
            self.hasReported = True

    def ShowBanner(self, nickname, music, isMusic=False, isMvp=False):
        self.SetText(self.winName, nickname)
        if isMvp:
            self.SetText('/winpanel/label3', '正在向所有玩家高奏您的MVP凯歌')
        else:
            self.SetText('/winpanel/label3', '正在高奏%s的MVP凯歌' % nickname)
        if music:
            self.SetText(self.winMusic, music)
        self.SetVisible(self.winMusic, isMusic)
        self.SetVisible('/winpanel/label3', isMusic)
        self.SetVisible(self.winpanel, True)
        def a():
            self.SetVisible(self.winpanel, False)
        comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        comp.AddTimer(15.0, a)

    def ShowUi(self):
        print 'utils UISCRIPT CALL ShowUi'
        self.SetVisible("", True)
        self.SetVisible(self.hubBtn, True)
        self.SetVisible(self.dialogPanel, False)
        self.SetVisible(self.winpanel, False)
        self.SetVisible(self.textPanel, False)
        # clientApi.SetInputMode(1)
        # clientApi.HideSlotBarGui(True)

    def ShowSpecUi(self, data):
        self.SetVisible(self.specPanel, data['isSpec'])

        imageButtonPath = self.specReportBtn
        buttonUIControl = clientApi.GetUI('utils', 'utilsUI').GetBaseUIControl(imageButtonPath).asButton()
        buttonDefaultUIControl = buttonUIControl.GetChildByName("default").asImage()
        buttonHoverUIControl = buttonUIControl.GetChildByName("hover").asImage()
        buttonPressedUIControl = buttonUIControl.GetChildByName("pressed").asImage()

        if self.hasReported:
            buttonDefaultUIControl.SetSprite("textures/ui/utilsUI/spec-instareport-disable")
            buttonHoverUIControl.SetSprite("textures/ui/utilsUI/spec-instareport-disable")
            buttonPressedUIControl.SetSprite("textures/ui/utilsUI/spec-instareport-disable")

        if 'nickname' in data:
            nickname = data['nickname']
            self.SetText(self.specTargetInd, '正在观战 §l%s' % nickname)

    def TextBoard(self, isShow, content):
        if isShow:
            self.SetVisible(self.textPanel, True)
            self.SetText(self.textBoard, str(content))
        else:
            self.SetVisible(self.textPanel, False)

    def ExitUi(self, args):
        print 'UISCRIPT CALL ExitUi args=%s' % (args,)
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.close()

    def close(self):
        self.SetVisible("", False)
        self.SetVisible(self.unrankedMenu, False)
        self.page = 0
        self.section = 0
        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)
        pass