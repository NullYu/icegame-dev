import client.extraClientApi as clientApi
import time

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
TouchEvent = clientApi.GetMinecraftEnum().TouchEvent
ClientSystem = clientApi.GetSystem("eco", "ecoClient")

class ecoScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        print '==== %s ====' % 'init TestScreen'
        self.uiNode = None

        self.page = 0
        self.section = 0
        self.disableUi = False

        self.playerPwdStatus = None
        self.playerLastAccess = None
        self.playerUid = None
        self.playerPwd = None
        self.playerChangekey = None
        self.newpassword = None
        self.changekey = None

        self.bg = '/sudobg'
        self.closeBtn = '/close_btn'
        self.helpBtn = '/help_btn'

        self.mainPanel = self.bg+'/panel0'
        self.viewBtn = self.mainPanel+'/button0'
        self.changeBtn = self.mainPanel+'/button1'
        self.lockBtn = self.mainPanel+'/button2'

        self.viewPanel = self.bg+'/panel1'
        self.viewPrev = self.viewPanel+'/button3'
        self.statusLabel = self.viewPanel+'/statusLabel'
        self.lastAccessLabel = self.viewPanel+'/uidLabel'
        self.uidLabel = self.viewPanel+'/lastAccessLabel'

        self.changePanel = self.bg+'/panel2'
        self.changePrev = self.changePanel+'/button8'
        # newpassword and changekey are reversed
        self.changekeyInput = self.changePanel+'/newpassword'
        self.newpasswordInput = self.changePanel+'/changekey'
        self.changeConfBtn = self.changePanel+'/button9'

        self.lockPanel = self.bg+'/panel3'
        self.lockPrev = self.lockPanel+'/button4'
        self.lockPasswordInput = self.lockPanel+'/password'
        self.lockConfBtn = self.lockPanel+'/button5'

        self.errPanel = '/errpanel'
        self.errCloseBtn = self.errPanel+'/err_closebtn'
        self.errLabel = self.errPanel+'/errlabel'

        self.confPanel = '/confirmpanel'
        self.confLabel = self.confPanel+'/labelconfirm'
        self.confOkBtn = self.confPanel+'/button7'
        self.confCancelBtn = self.confPanel+'/button6'

    def Create(self):
        print '==== %s ====' % 'adminScreen Create'

        self.AddTouchEventHandler(self.closeBtn, self.ExitUi, {"isSwallow": True})
        self.AddTouchEventHandler(self.errCloseBtn, self.ExitMessage, {"isSwallow": True})
        self.AddTouchEventHandler(self.confCancelBtn, self.ExitPrompt, {"isSwallow": True})
        self.AddTouchEventHandler(self.confOkBtn, self.ConfPrompt, {"isSwallow": True})
        self.AddTouchEventHandler(self.helpBtn, self.ShowHelp, {"isSwallow": True})
        self.AddTouchEventHandler(self.viewPrev, self.Prev, {"isSwallow": True})
        self.AddTouchEventHandler(self.changePrev, self.Prev, {"isSwallow": True})
        self.AddTouchEventHandler(self.lockPrev, self.Prev, {"isSwallow": True})

        self.AddTouchEventHandler(self.viewBtn, self.EnterView, {"isSwallow": True})
        self.AddTouchEventHandler(self.changeBtn, self.EnterChange, {"isSwallow": True})
        self.AddTouchEventHandler(self.lockBtn, self.EnterLock, {"isSwallow": True})

        self.AddTouchEventHandler(self.changeConfBtn, self.ConfChange, {"isSwallow": True})
        self.AddTouchEventHandler(self.lockConfBtn, self.ConfLock, {"isSwallow": True})

    def InitScreen(self):
        print '==== %s ====' % 'adminScreen Init'

        # self.SetVisible('/panel0', False)
        self.SetVisible("", False)
        self.SetVisible(self.mainPanel, False)
        self.SetVisible(self.viewPanel, False)
        self.SetVisible(self.lockPanel, False)
        self.SetVisible(self.changePanel, False)
        self.SetVisible(self.errPanel, False)
        self.SetVisible(self.confPanel, False)

    def ShowMessage(self, msg):
        self.disableUi = True
        self.SetVisible(self.errPanel, True)
        self.SetText(self.errLabel, "§8"+msg)

    def ExitMessage(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.disableUi = False
            self.SetVisible(self.errPanel, False)

    def ShowPrompt(self, msg):
        self.disableUi = True
        self.SetVisible(self.confPanel, True)
        self.SetText(self.confLabel, "§8" + msg)

    def ExitPrompt(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.disableUi = False
            self.SetVisible(self.confPanel, False)

    def ConfPrompt(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            if self.page == 2:
                self.ChangeSubmit()
            elif self.page == 3:
                self.LockSubmit()
            self.disableUi = False
            self.SetVisible(self.confPanel, False)
            self.page = 0

    def ShowHelp(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and not self.disableUi:
            self.ShowMessage("使用/sudo -h查看如何使用命令")

    def EnterView(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            if not self.disableUi:
                self.SetVisible(self.mainPanel, False)
                self.SetVisible(self.viewPanel, True)

                if self.playerPwdStatus == 'ok':
                    self.SetText(self.statusLabel, "§a§l正常")
                elif self.playerPwdStatus == 'unset':
                    self.SetText(self.statusLabel, "§c§l未设置")
                elif self.playerPwdStatus == 'unsafe':
                    self.SetText(self.statusLabel, "§g§l不安全")
                self.SetText(self.lastAccessLabel, "§9§l"+time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(int(self.playerLastAccess+0))))
                self.SetText(self.uidLabel, "§9§l#"+str(self.playerUid))

    def EnterChange(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            if not self.disableUi:
                self.uiNode.GetBaseUIControl(self.changekeyInput).asTextEditBox().SetEditText("")
                self.uiNode.GetBaseUIControl(self.newpasswordInput).asTextEditBox().SetEditText("")
                self.SetVisible(self.mainPanel, False)
                self.SetVisible(self.changePanel, True)

    def EnterLock(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            if not self.disableUi:
                self.uiNode.GetBaseUIControl(self.newpasswordInput).asTextEditBox().SetEditText("")
                self.SetVisible(self.mainPanel, False)
                self.SetVisible(self.lockPanel, True)

    def ConfChange(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and not self.disableUi:
            self.page = 2
            self.ShowPrompt("您即将更改密码\n请您务必牢记密码！")

    def ConfLock(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and not self.disableUi:
            self.page = 3
            self.ShowPrompt("您即将开启账号安全锁\n希望您知道您自己在做什么！")

    def ChangeSubmit(self):
        self.changekey = self.uiNode.GetBaseUIControl(self.changekeyInput).asTextEditBox().GetEditText()
        self.newpassword = self.uiNode.GetBaseUIControl(self.newpasswordInput).asTextEditBox().GetEditText()
        self.uiNode.GetBaseUIControl(self.changekeyInput).asTextEditBox().SetEditText("")
        self.uiNode.GetBaseUIControl(self.newpasswordInput).asTextEditBox().SetEditText("")

        # error filter
        if len(self.newpassword) < 7 or len(self.newpassword) > 24 or "§" in self.newpassword:
            self.ShowMessage("密码长度必须在7~24，并且不包含颜色代码符§")
            return
        # elif self.playerPwdStatus == 'unsafe':
        #     self.ShowMessage("操作失败:\nOperation not permitted\n\n请检查账号状态是否允许设置密码")
        #     return
        elif self.playerPwd != '0' and (self.changekey != self.playerChangekey or self.changekey == '0'):
            self.ShowMessage("操作失败:\nSorry, try again\n\n请检查密码与授权码是否正确")
            return

        response = {
            'mode': 'change',
            'password': self.newpassword,
            'playerId': clientApi.GetLocalPlayerId()
        }
        ClientSystem = clientApi.GetSystem("eco", "ecoClient")
        ClientSystem.ReturnToServer(response)
        self.close()

    def LockSubmit(self):
        self.newpassword = self.uiNode.GetBaseUIControl(self.lockPasswordInput).asTextEditBox().GetEditText()
        self.uiNode.GetBaseUIControl(self.lockPasswordInput).asTextEditBox().SetEditText("")

        # error filter
        if self.playerPwdStatus != 'ok':
            self.ShowMessage("操作失败:\nOperation not permitted\n\n请检查账号状态是否允许该操作")
            return
        elif self.newpassword != self.playerPwd:
            self.ShowMessage("操作失败:\nSorry, try again\n\n请检查密码是否正确")
            return


        response = {
            'mode': 'lock',
            'playerId': clientApi.GetLocalPlayerId()
        }
        ClientSystem = clientApi.GetSystem("eco", "ecoClient")
        ClientSystem.ReturnToServer(response)
        self.close()

    def Prev(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            if not self.disableUi:
                self.page = 0
                self.section = 0
                self.SetVisible(self.mainPanel, True)
                self.SetVisible(self.viewPanel, False)
                self.SetVisible(self.changePanel, False)
                self.SetVisible(self.lockPanel, False)

    def ShowUi(self, uiNode, args=None):
        print 'UISCRIPT CALL ShowUi'
        self.uiNode = uiNode
        self.SetVisible("", True)
        self.SetVisible(self.bg, True)
        self.SetVisible(self.mainPanel, True)
        clientApi.SetInputMode(1)
        clientApi.HideSlotBarGui(True)

        if args:
            self.playerUid = args['uid']
            self.playerLastAccess = args['lastAccess']
            if args['password'] == '0':
                self.playerPwd = '0'
                self.playerPwdStatus = 'unset'
            elif args['unsafe']:
                self.playerPwd = args['password']
                self.playerPwdStatus = 'unsafe'
            else:
                self.playerPwd = args['password']
                self.playerPwdStatus = 'ok'
            self.playerChangekey = args['changekey']

    def ExitUi(self, args):
        print 'UISCRIPT CALL ExitUi args=%s' % (args,)
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.close()

    def close(self):
        self.SetVisible("", False)
        self.SetVisible(self.bg, False)
        self.SetVisible(self.mainPanel, False)
        self.SetVisible(self.viewPanel, False)
        self.SetVisible(self.changePanel, False)
        self.SetVisible(self.lockPanel, False)
        self.SetVisible(self.errPanel, False)
        self.SetVisible(self.confPanel, False)
        self.page = 0
        self.section = 0
        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)
        pass