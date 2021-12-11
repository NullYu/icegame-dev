# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi
from mod.client.ui.screenNode import ScreenNode
from mod.client.ui.screenController import ViewBinder, ViewRequest

# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()


# 在modMain中注册的Client System类
class hudClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        print '###__init__ hudClient'
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent('hud', 'hudSystem', 'SetEnableHudEvent', self, self.OnSetEnableHud)
        self.ListenForEvent('hud', 'hudSystem', 'UpdateHudEvent', self, self.OnUpdateHud)
        self.ListenForEvent('hud', 'hudSystem', 'DisplayKillIndicatorEvent', self, self.OnDisplayKillIndicator)
        self.ListenForEvent('hud', 'hudSystem', 'DisplayDeathEvent', self, self.OnDisplayDeath)
        self.ListenForEvent('hud', 'hudSystem', 'ResetHudEvent', self, self.OnResetHud)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'OnScriptTickClient', self,
                            self.tick)
        self.hudUINode = None

        self.hp = 100
        self.postHp = 100

        self.isDead = False

    def OnUIInitFinished(self, args):
        uiRegisterSuccess = clientApi.RegisterUI('hud', 'hudUI', 'hudScript.hudClientUI.hudScreen', 'hudUI.main')
        print 'hudUI Register UI success=%s' % (uiRegisterSuccess,)
        clientApi.CreateUI('hud', 'hudUI', {'isHud': 1})
        self.hudUINode = clientApi.GetUI('hud', 'hudUI')
        if self.hudUINode:
            self.hudUINode.InitScreen()
            print 'hudUINODE.InitScreen node=', str(self.hudUINode)
        else:
            print 'FAILED TO hudUINODE.InitScreen!!! hudUINODE=', str(self.hudUINode)

    def tick(self):
        if self.hp != self.postHp and not self.isDead:
            comp = clientApi.GetEngineCompFactory().CreatePostProcess(clientApi.GetLevelId())
            if self.hp > 30:
                comp.SetColorAdjustmentSaturation(1)
            else:
                comp.SetColorAdjustmentSaturation(self.hp*0.025)
            self.postHp = self.hp
        elif self.isDead:
            comp = clientApi.GetEngineCompFactory().CreatePostProcess(clientApi.GetLevelId())
            comp.SetColorAdjustmentSaturation(0)

    def UpdateHp(self, hp):
        self.hp = hp

    def OnResetHud(self, args):
        print '----RESET----'
        self.hudUINode.ResetHud()
        self.isDead = False

        clientApi.GetEngineCompFactory().CreatePlayerView(clientApi.GetLocalPlayerId()).SetPerspective(0)

        timerComp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())

        camComp = clientApi.GetEngineCompFactory().CreateCamera(clientApi.GetLevelId())
        camComp.UnDepartCamera()
        camComp.SetCameraBindActorId(clientApi.GetLocalPlayerId())

        comp = clientApi.GetEngineCompFactory().CreateOperation(clientApi.GetLevelId())
        comp.SetCanDrag(True)
        comp.SetCanJump(True)
        comp.SetCanMove(True)
        comp.SetCanOpenInv(True)
        comp.SetCanPause(True)
        comp.SetCanPerspective(True)
        clientApi.HideHudGUI(False)
        clientApi.HideInteractGui(False)

        timerComp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        timerComp.SetRenderLocalPlayer(True)

        def a():
            postComp = clientApi.GetEngineCompFactory().CreatePostProcess(clientApi.GetLevelId())
            postComp.SetColorAdjustmentSaturation(1)
        timerComp.AddTimer(0.5, a)

    def OnSetEnableHud(self, isEnable):
        self.hudUINode.ShowUi(True)
        comp = clientApi.GetEngineCompFactory().CreatePostProcess(clientApi.GetLevelId())
        comp.SetEnableColorAdjustment(True)
        print 'OnShowHud content = %s' % isEnable

        enableMode = isEnable
        clientApi.HideHealthGui(enableMode)
        clientApi.HideArmorGui(enableMode)
        clientApi.HideChangePersonGui(enableMode)
        clientApi.HideHungerGui(enableMode)

    def OnDisplayKillIndicator(self, data):
        if data['isSuicide'] or data['killerId'] == clientApi.GetLocalPlayerId():
            self.hudUINode.DisplayKillIndicator(data['isSuicide'])
        if data['isSuicide'] or data['victimId'] == clientApi.GetLocalPlayerId():
            self.hudUINode.DisplayDeath(data)

        print 'display death client'

    def OnDisplayDeath(self, data):
        self.isDead = True

        clientApi.GetEngineCompFactory().CreatePlayerView(clientApi.GetLocalPlayerId()).SetPerspective(1)

        timerComp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        timerComp.SetRenderLocalPlayer(False)

        camComp = clientApi.GetEngineCompFactory().CreateCamera(clientApi.GetLevelId())
        camComp.DepartCamera()

        comp = clientApi.GetEngineCompFactory().CreateOperation(clientApi.GetLevelId())
        comp.SetCanDrag(False)
        comp.SetCanJump(False)
        comp.SetCanMove(False)
        comp.SetCanOpenInv(False)
        comp.SetCanPause(False)
        comp.SetCanPerspective(False)

        clientApi.HideHudGUI(True)
        clientApi.HideInteractGui(True)

        def a():
            if 'killerId' in data:
                camComp.SetCameraBindActorId(data['killerId'])
        timerComp.AddTimer(4.0, a)

        def b():
            self.NotifyToServer('DisplayDeathDoneEvent', clientApi.GetLocalPlayerId())
        timerComp.AddTimer(14.0, b)

    def OnUpdateHud(self, data):
        if self.hudUINode:
            self.hudUINode.UpdateData(data)

    def ReturnToServer(self, args):
        response = args
        response['playerId'] = clientApi.GetLocalPlayerId()
        self.NotifyToServer("ActionEvent", args)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
