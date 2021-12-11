# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi
from mod.client.ui.screenNode import ScreenNode
from mod.client.ui.screenController import ViewBinder, ViewRequest

# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()


# 在modMain中注册的Client System类
class adminClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        print '###__init__ adminClient'
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent('admin', 'adminSystem', 'ShowAdminEvent', self, self.OnShowAdmin)
        self.ListenForEvent('admin', 'adminSystem', 'SearchResultEvent', self, self.OnSearchResult)

    def OnUIInitFinished(self, args):
        uiRegisterSuccess = clientApi.RegisterUI('admin', 'adminUI', 'adminScript.adminClientUI.adminScreen', 'adminUI.main')
        print 'adminUI Register UI success=%s' % (uiRegisterSuccess,)
        clientApi.CreateUI('admin', 'adminUI', {'isHud': 1})
        self.adminUINode = clientApi.GetUI('admin', 'adminUI')
        if self.adminUINode:
            self.adminUINode.InitScreen()
            print 'adminUINODE.InitScreen node=', str(self.adminUINode)
        else:
            print 'FAILED TO adminUINODE.InitScreen!!! adminUINODE=', str(self.adminUINode)

    def OnSearchResult(self, data):
        suc = data['suc']
        if not suc:
            self.adminUINode.DispSearchResult(False)
        else:

            nickname = data['nickname']
            uid = data['uid']
            self.adminUINode.DispSearchResult(True, nickname, uid)

    def OnShowAdmin(self, data=None):
        self.adminUINode.ShowUi()

    def ReturnToServer(self, args):
        response = args
        response['playerId'] = clientApi.GetLocalPlayerId()
        self.NotifyToServer("ActionEvent", args)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
