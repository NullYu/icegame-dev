# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi
from mod.client.ui.screenNode import ScreenNode
from mod.client.ui.screenController import ViewBinder, ViewRequest

# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()


# 在modMain中注册的Client System类
class fbClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        print '###__init__ fbClient'
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent('fb', 'fbSystem', 'ShowStartScreen', self, self.OnShowStartScreen)
        self.ListenForEvent('fb', 'fbSystem', 'StartVotingEvent', self, self.OnStartVoting)

    def OnUIInitFinished(self, args):
        uiRegisterSuccess = clientApi.RegisterUI('fb', 'fbUI', 'fbScript.fbClientUI.fbScreen', 'fbUI.main')
        print 'fbUI Register UI success=%s' % (uiRegisterSuccess,)
        clientApi.CreateUI('fb', 'fbUI', {'isHud': 0})
        self.fbUINode = clientApi.GetUI('fb', 'fbUI')
        if self.fbUINode:
            self.fbUINode.InitScreen()
            print 'fbUINODE.InitScreen node=', str(self.fbUINode)
        else:
            print 'FAILED TO fbUINODE.InitScreen!!! fbUINODE=', str(self.fbUINode)

    def OnShowStartScreen(self, data):
        self.fbUINode.ShowStartScreen(data['theme'], data['time'])

    def OnStartVoting(self, data=None):
        self.fbUINode.StartVoting()

    def ReturnToServer(self, args):
        response = args
        response['playerId'] = clientApi.GetLocalPlayerId()
        self.NotifyToServer("VoteEvent", args)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
