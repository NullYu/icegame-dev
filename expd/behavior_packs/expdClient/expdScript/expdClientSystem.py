# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi
from mod.client.ui.screenNode import ScreenNode
from mod.client.ui.screenController import ViewBinder, ViewRequest

# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()


# 在modMain中注册的Client System类
class expdClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        print '###__init__ expdClient'
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent('expd', 'expdSystem', 'ShowCdEvent', self, self.OnShowCd)

    def OnUIInitFinished(self, args):
        uiRegisterSuccess = clientApi.RegisterUI('expd', 'expdUI', 'expdScript.expdClientUI.expdScreen', 'expdUI.main')
        print 'expdUI Register UI success=%s' % (uiRegisterSuccess,)
        clientApi.CreateUI('expd', 'expdUI', {'isHud': 1})
        self.expdUINode = clientApi.GetUI('expd', 'expdUI')
        if self.expdUINode:
            self.expdUINode.InitScreen()
            print 'expdUINODE.InitScreen node=', str(self.expdUINode)
        else:
            print 'FAILED TO expdUINODE.InitScreen!!! expdUINODE=', str(self.expdUINode)

    def OnShowCd(self, data):
        def a():
            try:
                self.expdUINode.ShowUi(data['id'], data['endDate'])
                print 'OnShowexpd content = %s' % data
            except:
                print 'ui not init! Retry in 1'
                comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
                comp.AddTimer(1.0, a)
        a()

    def ReturnToServer(self, args):
        response = args
        response['playerId'] = clientApi.GetLocalPlayerId()
        self.NotifyToServer("ActionEvent", args)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
