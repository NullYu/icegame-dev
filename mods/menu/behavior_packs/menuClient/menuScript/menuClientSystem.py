# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi
from mod.client.ui.screenNode import ScreenNode
from mod.client.ui.screenController import ViewBinder, ViewRequest
# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()


# 在modMain中注册的Client System类
class menuClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        # self.ListenForEvent('test', 'testSystem', 'ShowTestUiEvent', self, self.OnShowTestUi)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent('menu', 'menuSystem', 'OpenMenuEvent', self, self.OnShowTestUi)
        self.ListenForEvent('menu', 'menuSystem', 'OpenMailEvent', self, self.OnOpenMail)



    def OnUIInitFinished(self, args):
        uiRegisterSuccess = clientApi.RegisterUI('menu', 'menuUI', 'menuScript.menuClientUI.menuScreen', 'menuUI.main')
        print 'Register UI success=%s' % (uiRegisterSuccess,)
        clientApi.CreateUI('menu', 'menuUI', {'isHud': 1})
        self.mChillUINode = clientApi.GetUI('menu', 'menuUI')
        if self.mChillUINode:
            self.mChillUINode.InitScreen()
            print 'menuUINODE.InitScreen node=', str(self.mChillUINode)
        else:
            print 'FAILED TO menuUINODE.InitScreen!!! menuUINODE=', str(self.mChillUINode)

    def OnOpenMail(self, args):
        system = clientApi.GetSystem("neteaseAnnounce", "neteaseAnnounceBeh")
        # 打开邮件主界面
        system.OpenMainUI()

    def OnShowTestUi(self, args):
        print 'CALL OnShowTestUi', str(args)
        if self.mChillUINode:
            self.mChillUINode.ShowUi(args)

    def ReturnToServer(self, args):
        response = args
        response['playerId'] = clientApi.GetLocalPlayerId()
        self.NotifyToServer("MenuActionEvent", args)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
