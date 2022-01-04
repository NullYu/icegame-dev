# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi
from mod.client.ui.screenNode import ScreenNode
from mod.client.ui.screenController import ViewBinder, ViewRequest

# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()


# 在modMain中注册的Client System类
class v5Client(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        print '###__init__ v5Client'
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent('v5', 'v5System', 'ShowPrepSelectionScreenEvent', self, self.OnShowPrepSelectionScreen)
        self.ListenForEvent('v5', 'v5System', 'DebugEvent', self, self.OnDebug)
        self.ListenForEvent('v5', 'v5System', 'StartDefuserProgressEvent', self, self.OnStartDefuserProgress)
        self.ListenForEvent('v5', 'v5System', 'ShowTimerPanelEvent', self, self.OnShowTimerPanel)
        self.ListenForEvent('v5', 'v5System', 'ShowEqpPanelEvent', self, self.OnShowEqpPanel)
        self.ListenForEvent('v5', 'v5System', 'TimerUpdateEvent', self, self.OnTimerUpdate)
        self.ListenForEvent('v5', 'v5System', 'UpdateKitDurabilityEvent', self, self.OnUpdateKitDurability)
        self.ListenForEvent('v5', 'v5System', 'SetEqpDataEvent', self, self.OnSetEqpData)
        self.ListenForEvent('v5', 'v5System', 'UpdateReinfPanelEvent', self, self.OnUpdateReinfPanel)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'ClientPlayerInventoryOpenEvent', self, self.OnClientPlayerInventoryOpen)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'OnScriptTickClient', self, self.tick)
        self.v5UINode = None

    def OnClientPlayerInventoryOpen(self, data):
        return 
        data['cancel'] = True
        self.ReturnToServer({
            'operation': 'kickout'
        })

    def OnUIInitFinished(self, args):
        uiRegisterSuccess = clientApi.RegisterUI('v5', 'v5UI', 'v5Script.v5ClientUI.v5Screen', 'v5UI.main')
        print 'v5UI Register UI success=%s' % (uiRegisterSuccess,)
        clientApi.CreateUI('v5', 'v5UI', {'isv5': 1})
        self.v5UINode = clientApi.GetUI('v5', 'v5UI')
        if self.v5UINode:
            self.v5UINode.InitScreen()
            print 'v5UINODE.InitScreen node=', str(self.v5UINode)
        else:
            print 'FAILED TO v5UINODE.InitScreen!!! v5UINODE=', str(self.v5UINode)

    def OnShowPrepSelectionScreen(self, data):
        self.v5UINode.UpdatePrepSelectionScreen(data)

    def OnShowTimerPanel(self, tup):
        self.v5UINode.ShowTimerPanel(tup[0], tup[1])

    def OnShowEqpPanel(self, tup):
        self.v5UINode.ShowEqpPanel(tup[0], tup[1])

    def OnStartDefuserProgress(self, data):
        self.v5UINode.StartDefuserProgress()

    def OnSetEqpData(self, data):
        self.v5UINode.setEqpData(data)

    def OnUpdateKitDurability(self, data):
        self.v5UINode.UpdateKitDurability(data)

    def OnUpdateReinfPanel(self, data):
        self.v5UINode.UpdateReinfPanel(data)

    def ReturnToServer(self, args):
        response = args
        response['playerId'] = clientApi.GetLocalPlayerId()
        self.NotifyToServer("ActionEvent", args)

    def OnDebug(self, data):
        operation = data['operation']
        if operation == 'uiDebug':
            uiNode = self.v5UINode
            uiObj = self.v5UINode
            uiNode.GetBaseUIControl(uiObj.prepChooseSkillPanel + '/ss5').SetPosition((data['x'], data['y']))

    def OnTimerUpdate(self, timerText):
        self.v5UINode.timerText = timerText

    def tick(self):
        pass

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
