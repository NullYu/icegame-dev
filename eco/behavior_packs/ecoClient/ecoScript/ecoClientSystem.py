# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi

# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()


# 在modMain中注册的Client System类
class ecoClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        print "====ecoClientSystem Init ===="
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent('eco', 'ecoSystem', 'OpenPanelEvent', self, self.OnShowUi)

    def OnUIInitFinished(self, args):
        uiRegisterSuccess = clientApi.RegisterUI('eco', 'ecoUI', 'ecoScript.ecoClientUI.ecoScreen', 'ecoUI.main')
        print 'Register UI success=%s' % (uiRegisterSuccess,)
        clientApi.CreateUI('eco', 'ecoUI', {'isHud': 1})
        self.mChillUINode = clientApi.GetUI('eco', 'ecoUI')
        if self.mChillUINode:
            self.mChillUINode.InitScreen()
            print 'ecoUINODE.InitScreen node=', str(self.mChillUINode)
        else:
            print 'FAILED TO ecoUINODE.InitScreen!!! ecoUINODE=', str(self.mChillUINode)

    def OnShowUi(self, args):
        print 'CALL OnShowTestUi', str(args)
        if self.mChillUINode:
            self.mChillUINode.ShowUi(self.mChillUINode, args)

    def ReturnToServer(self, args):
        self.NotifyToServer("SudoReturnEvent", args)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
