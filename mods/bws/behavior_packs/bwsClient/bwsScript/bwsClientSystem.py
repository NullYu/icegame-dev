# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi
from mod.client.ui.screenNode import ScreenNode
from mod.client.ui.screenController import ViewBinder, ViewRequest

# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()


# 在modMain中注册的Client System类
class bwsClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        print '###__init__ bwsClient'
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent('bws', 'bwsSystem', 'ShowbwsEvent', self, self.OnShowbws)

    def OnUIInitFinished(self, args):
        uiRegisterSuccess = clientApi.RegisterUI('bws', 'bwsUI', 'bwsScript.bwsClientUI.bwsScreen', 'bwsUI.main')
        print 'bwsUI Register UI success=%s' % (uiRegisterSuccess,)
        clientApi.CreateUI('bws', 'bwsUI', {'isHud': 1})
        self.bwsUINode = clientApi.GetUI('bws', 'bwsUI')
        if self.bwsUINode:
            self.bwsUINode.InitScreen()
            print 'bwsUINODE.InitScreen node=', str(self.bwsUINode)
        else:
            print 'FAILED TO bwsUINODE.InitScreen!!! bwsUINODE=', str(self.bwsUINode)

    def OnShowbws(self, money=0):
        self.bwsUINode.ShowUi(money)

    def ReturnToServer(self, args):
        response = args
        response['playerId'] = clientApi.GetLocalPlayerId()
        self.NotifyToServer("ActionEvent", args)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
