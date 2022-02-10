import client.extraClientApi as clientApi

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
TouchEvent = clientApi.GetMinecraftEnum().TouchEvent
ClientSystem = clientApi.GetSystem("admin", "adminClient")

class adminScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        print '==== %s ====' % 'init TestScreen'

        self.panel = '/panel0'
        self.closeBtn = self.panel+'/closeBtn'
        self.prevBtn = self.panel+'/button2'
        self.searchPanel = self.panel+'/panel1'
        self.actionPanel = self.panel+'/panel2'

        self.search = self.searchPanel+'/text_edit_box0'
        self.searchMode = self.searchPanel+'/button0'
        self.searchModeInd = self.searchPanel+'/label2'
        self.searchTargetInd = self.searchPanel+'/searchTarget'
        self.searchStatusInd = self.searchPanel+'/label5'
        self.searchSubmit = self.searchPanel+'/button1'

        self.action = self.actionPanel+'/button3'
        self.actionReason = self.actionPanel+'/text_edit_box1'
        self.actionDuration = self.actionPanel+'/text_edit_box2'
        self.actionInd = self.actionPanel+'/label8'
        self.actionPermInd = self.actionPanel+'/label10'
        self.actionSubmit = self.actionPanel+'/button5'
        self.actionPerm = self.actionPanel+'/button4'

        self.target = None
        self.duration = 0
        self.reason = None
        self.isPerm = False
        self.isInAction = False

        self.sMode = None
        self.aMode = None

    def Reset(self, resetInd=True):
        self.target = None
        self.duration = 0
        self.reason = None
        self.isPerm = False

        self.sMode = None
        self.aMode = None
        self.isInAction = False

        self.SetEditText(self.search, '')

        self.SetText(self.searchModeInd, '选择搜索模式 （点击切换）')
        self.SetText(self.actionInd, '选择操作（点击切换）')
        self.SetText(self.actionPermInd, '')

        if resetInd:
            self.SetText(self.searchTargetInd, '')
            self.SetText(self.searchStatusInd, '等待提交')

        self.SetVisible(self.searchPanel, True)
        self.SetVisible(self.actionPanel, False)

    def Create(self):
        print '==== %s ====' % 'adminScreen Create'
        self.AddTouchEventHandler(self.closeBtn, self.ExitUi, {"isSwallow": True})
        self.AddTouchEventHandler(self.prevBtn, self.Prev, {"isSwallow": True})
        self.AddTouchEventHandler(self.searchMode, self.ToggleSearchMode, {"isSwallow": True})
        self.AddTouchEventHandler(self.action, self.ToggleActionMode, {"isSwallow": True})
        self.AddTouchEventHandler(self.searchSubmit, self.SubmitSearch, {"isSwallow": True})
        self.AddTouchEventHandler(self.actionSubmit, self.SubmitAction, {"isSwallow": True})
        self.AddTouchEventHandler(self.actionPerm, self.ToggleActionPerm, {"isSwallow": True})

    def InitScreen(self):
        print '==== %s ====' % 'uiScreen Init'

        # self.SetVisible('/panel0', False)
        self.SetVisible("", False)

    def ShowUi(self):
        print 'UISCRIPT CALL ShowUi'
        self.Reset()
        self.SetVisible("", True)
        clientApi.SetInputMode(1)
        clientApi.HideSlotBarGui(True)

    def ToggleActionPerm(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and self.isInAction:
            self.isPerm = not self.isPerm
            if self.isPerm:
                self.SetText(self.actionPermInd, 'ON')
            else:
                self.SetText(self.actionPermInd, 'OFF')

    def ToggleSearchMode(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and not self.isInAction:
            if self.sMode is None:
                self.sMode = False
                self.SetText(self.searchModeInd, '精确搜索')
            else:
                self.sMode = not self.sMode
                if self.sMode:
                    self.SetText(self.searchModeInd, '模糊搜索')
                else:
                    self.SetText(self.searchModeInd, '精确搜索')

    def ToggleActionMode(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and self.isInAction:
            if self.aMode is None:
                self.aMode = 0
                self.SetText(self.actionInd, 'BAN')
            else:
                self.aMode += 1
                if self.aMode > 3:
                    self.aMode = 0

                if self.aMode == 0:
                    self.SetText(self.actionInd, 'BAN')
                elif self.aMode == 1:
                    self.SetText(self.actionInd, 'MUTE')
                elif self.aMode == 2:
                    self.SetText(self.actionInd, 'KICK')
                elif self.aMode == 3:
                    self.SetText(self.actionInd, 'CD')

    def SubmitAction(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and self.isInAction:
            if self.aMode is not None and self.GetEditText(self.actionReason):
                self.reason = self.GetEditText(self.actionReason)
                self.duration = self.GetEditText(self.actionDuration)

                response = {
                    'mode': 'action',
                    'type': self.aMode,
                    'target': self.target,
                    'isPerm': self.isPerm,
                    'reason': self.reason,
                    'duration': self.duration
                }
                ClientSystem = clientApi.GetSystem("admin", "adminClient")
                ClientSystem.ReturnToServer(response)

                self.close()

    def Prev(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and self.isInAction:
            self.isInAction = False
            self.Reset()
            self.SetVisible(self.actionPanel, False)

    def SubmitSearch(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and not self.isInAction:
            if self.sMode is not None:
                self.target = self.GetEditText(self.search)
                response = {
                    'mode': 'search',
                    'keyword': self.target,
                    'rangeSearch': self.sMode
                }
                ClientSystem = clientApi.GetSystem("admin", "adminClient")
                ClientSystem.ReturnToServer(response)

    def DispSearchResult(self, suc, nickname=None, uid=None):
        if suc:
            self.Reset(False)
            self.SetText(self.searchTargetInd, nickname)
            self.SetText(self.searchStatusInd, '成功')
            self.target = uid

            self.isInAction = True
            self.SetVisible(self.actionPanel, True)

        else:
            self.Reset(False)
            self.SetText(self.searchStatusInd, '查找出错')

    def ExitUi(self, args):
        print 'UISCRIPT CALL ExitUi args=%s' % (args,)
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.close()

    def close(self):
        self.SetVisible("", False)
        self.Reset()
        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)