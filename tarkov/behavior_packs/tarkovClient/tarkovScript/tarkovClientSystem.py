# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi
from mod.client.ui.screenNode import ScreenNode
from mod.client.ui.screenController import ViewBinder, ViewRequest

# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()


# 在modMain中注册的Client System类
class tarkovClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        print '###__init__ tarkovClient'
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.OnUIInitFinished)
        # self.ListenForEvent('tarkov', 'tarkovSystem', 'ShowPrepSelectionScreenEvent', self, self.OnShowPrepSelectionScreen)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'OnScriptTickClient', self, self.tick)
        self.tarkovUINode = None

    def OnUIInitFinished(self, args):
        uiRegisterSuccess = clientApi.RegisterUI('tarkov', 'tarkovUI', 'tarkovScript.tarkovClientUI.tarkovScreen', 'tarkovUI.main')
        print 'tarkovUI Register UI success=%s' % (uiRegisterSuccess,)
        clientApi.CreateUI('tarkov', 'tarkovUI', {'istarkov': 1})
        self.tarkovUINode = clientApi.GetUI('tarkov', 'tarkovUI')
        if self.tarkovUINode:
            self.tarkovUINode.InitScreen()
            print 'tarkovUINODE.InitScreen node=', str(self.tarkovUINode)
        else:
            print 'FAILED TO tarkovUINODE.InitScreen!!! tarkovUINODE=', str(self.tarkovUINode)

    def ReturnToServer(self, args):
        response = args
        response['playerId'] = clientApi.GetLocalPlayerId()
        self.NotifyToServer("ActionEvent", args)

    def OnTimerUpdate(self, timerText):
        self.tarkovUINode.timerText = timerText

    def tick(self):
        pass

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
