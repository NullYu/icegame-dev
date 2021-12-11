# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi
from mod.client.ui.screenNode import ScreenNode
from mod.client.ui.screenController import ViewBinder, ViewRequest
# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()


# 在modMain中注册的Client System类
class signClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        # self.ListenForEvent('test', 'testSystem', 'ShowTestUiEvent', self, self.OnShowTestUi)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent('sign', 'signSystem', 'OpenSignEvent', self, self.OnShowSignUi)

        self.showFirstSign = False

    def OnUIInitFinished(self, args):
        uiRegisterSuccess = clientApi.RegisterUI('sign', 'signUI', 'signScript.signClientUI.signScreen', 'signUI.main')
        self.showFirstSign = True
        print 'Register UI success=%s' % (uiRegisterSuccess,)
        clientApi.CreateUI('sign', 'signUI', {'isHud': 1})
        self.mChillUINode = clientApi.GetUI('sign', 'signUI')
        if self.mChillUINode:
            self.mChillUINode.InitScreen()
            print 'signUINODE.InitScreen node=', str(self.mChillUINode)
        else:
            print 'FAILED TO signUINODE.InitScreen!!! signUINODE=', str(self.mChillUINode)

    def OnShowSignUi(self, args):
        print 'CALL OnShowSignUi', str(args)
        prizes = args['prizes']

        date = args['date']
        lastsign = args['lastsign']
        combo = args['combo']
        total = args['total']
        neko = prizes[0]
        credits = prizes[1]
        extraCredits = prizes[2]
        canSign = args['cansign']

        if self.mChillUINode and self.showFirstSign:
            self.mChillUINode.ShowUi(canSign, date, lastsign, combo, total, neko, credits, extraCredits)
        else:
            print 'Tried to showUI when ui didnt init! Adjust timing!'

    def ReturnToServer(self, args):
        response = args
        response['playerId'] = clientApi.GetLocalPlayerId()
        self.NotifyToServer("SignActionEvent", args)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
