# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi
from mod.client.ui.screenNode import ScreenNode
from mod.client.ui.screenController import ViewBinder, ViewRequest

# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()


# 在modMain中注册的Client System类
class megaClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        print '###__init__ megaClient'
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent('mega', 'megaSystem', 'UpdateContainerStatusEvent', self, self.OnUpdateContainerStatus)
        self.ListenForEvent('mega', 'megaSystem', 'StartNoMoveEvent', self, self.OnStartNoMove)

    def OnUIInitFinished(self, args):
        uiRegisterSuccess = clientApi.RegisterUI('mega', 'megaUI', 'megaScript.megaClientUI.megaScreen', 'megaUI.main')
        print 'megaUI Register UI success=%s' % (uiRegisterSuccess,)
        clientApi.CreateUI('mega', 'megaUI', {'isHud': 1})
        self.megaUINode = clientApi.GetUI('mega', 'megaUI')
        if self.megaUINode:
            self.megaUINode.InitScreen()
            print 'megaUINODE.InitScreen node=', str(self.megaUINode)
        else:
            print 'FAILED TO megaUINODE.InitScreen!!! megaUINODE=', str(self.megaUINode)

    def OnUpdateContainerStatus(self, data):
        self.megaUINode.UpdateContainerStatus(data)

    def OnStartNoMove(self, duration):
        comp = clientApi.GetEngineCompFactory().CreateOperation(clientApi.GetLevelId())
        comp.SetCanMove(False)
        def a():
            comp = clientApi.GetEngineCompFactory().CreateOperation(clientApi.GetLevelId())
            comp.SetCanMove(True)

        comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        comp.AddTimer(duration, a)

    def ReturnToServer(self, args):
        response = args
        response['playerId'] = clientApi.GetLocalPlayerId()
        self.NotifyToServer("ActionEvent", args)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
