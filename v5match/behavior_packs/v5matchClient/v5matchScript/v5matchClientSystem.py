# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi
from mod.client.ui.screenNode import ScreenNode
from mod.client.ui.screenController import ViewBinder, ViewRequest

# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()


# 在modMain中注册的Client System类
class v5matchClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        print '###__init__ v5matchClient'
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent('v5match', 'v5matchSystem', 'StartMatchmakeEvent', self, self.OnStartMatchmake)
        self.ListenForEvent('v5match', 'v5matchSystem', 'ExitMatchmakeEvent', self, self.OnExitMatchmake)
        self.ListenForEvent('v5match', 'v5matchSystem', 'UpdateInfoEvent', self, self.OnUpdateInfo)

    def OnUIInitFinished(self, args):
        uiRegisterSuccess = clientApi.RegisterUI('v5match', 'v5matchUI', 'v5matchScript.v5matchClientUI.v5matchScreen', 'v5matchUI.main')
        print 'v5matchUI Register UI success=%s' % (uiRegisterSuccess,)
        clientApi.CreateUI('v5match', 'v5matchUI', {'isHud': 1})
        self.v5matchUINode = clientApi.GetUI('v5match', 'v5matchUI')
        if self.v5matchUINode:
            self.v5matchUINode.InitScreen()
            print 'v5matchUINODE.InitScreen node=', str(self.v5matchUINode)
        else:
            print 'FAILED TO v5matchUINODE.InitScreen!!! v5matchUINODE=', str(self.v5matchUINode)

    def OnStartMatchmake(self, data):
        self.v5matchUINode.StartMatchmake()

    def OnExitMatchmake(self, data):
        self.v5matchUINode.ExitMatchmake()

    def OnShowv5match(self, data):
        self.v5matchUINode.ShowUi(data['title'], data['content'], data['time'])
        print 'OnShowv5match content = %s' % (data['content'],)

    def OnUpdateInfo(self, data):
        self.v5matchUINode.UpdateInfo(data)

    def ReturnToServer(self, args):
        response = args
        response['playerId'] = clientApi.GetLocalPlayerId()
        self.NotifyToServer("ActionEvent", args)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
