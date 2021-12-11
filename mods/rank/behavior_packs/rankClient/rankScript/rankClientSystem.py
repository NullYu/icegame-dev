# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi
from mod.client.ui.screenNode import ScreenNode
from mod.client.ui.screenController import ViewBinder, ViewRequest

# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()


# 在modMain中注册的Client System类
class rankClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        print '###__init__ rankClient'
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent('rank', 'rankSystem', 'ShowRankEvent', self, self.OnShowRank)

    def OnUIInitFinished(self, args):
        uiRegisterSuccess = clientApi.RegisterUI('rank', 'rankUI', 'rankScript.rankClientUI.rankScreen', 'rankUI.main')
        print 'rankUI Register UI success=%s' % (uiRegisterSuccess,)
        clientApi.CreateUI('rank', 'rankUI', {'isHud': 1})
        self.rankUINode = clientApi.GetUI('rank', 'rankUI')
        if self.rankUINode:
            self.rankUINode.InitScreen()
            print 'rankUINODE.InitScreen node=', str(self.rankUINode)
        else:
            print 'FAILED TO rankUINODE.InitScreen!!! rankUINODE=', str(self.rankUINode)

    def OnShowRank(self, data):
        self.rankUINode.ShowUi(data['title'], data['content'], data['time'])
        print 'OnShowRank content = %s' % (data['content'],)

    def ReturnToServer(self, args):
        response = args
        response['playerId'] = clientApi.GetLocalPlayerId()
        self.NotifyToServer("ActionEvent", args)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
