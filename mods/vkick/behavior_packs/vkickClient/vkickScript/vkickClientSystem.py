# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi
from mod.client.ui.screenNode import ScreenNode
from mod.client.ui.screenController import ViewBinder, ViewRequest

# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()


# 在modMain中注册的Client System类
class vkickClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        print '###__init__ vkickClient'
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent('vkick', 'vkickSystem', 'StartVote', self, self.OnStartVote)
        self.ListenForEvent('vkick', 'vkickSystem', 'UpdateVote', self, self.OnUpdateVote)
        self.ListenForEvent('vkick', 'vkickSystem', 'EndVote', self, self.OnEndVote)

    def OnUIInitFinished(self, args):
        uiRegisterSuccess = clientApi.RegisterUI('vkick', 'vkickUI', 'vkickScript.vkickClientUI.vkickScreen', 'vkickUI.main')
        print 'vkickUI Register UI success=%s' % (uiRegisterSuccess,)
        clientApi.CreateUI('vkick', 'vkickUI', {'isHud': 1})
        self.vkickUINode = clientApi.GetUI('vkick', 'vkickUI')
        if self.vkickUINode:
            self.vkickUINode.InitScreen()
            print 'vkickUINODE.InitScreen node=', str(self.vkickUINode)
        else:
            print 'FAILED TO vkickUINODE.InitScreen!!! vkickUINODE=', str(self.vkickUINode)

    def OnStartVote(self, data):
        print 'voting started'
        # TODO Remove debug section
        self.vkickUINode.StartVote(data['nickname'], bool(data['playerId'] == data['source'] or data['playerId'] == data['target']))

    def OnUpdateVote(self, data):
        self.vkickUINode.UpdateVote(data['aye'], data['nay'])

    def OnEndVote(self, suc):
        self.vkickUINode.EndVote(suc)

    def ReturnToServer(self, args):
        response = args
        response['playerId'] = clientApi.GetLocalPlayerId()
        self.NotifyToServer("ActionEvent", args)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
