# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi
from mod.client.ui.screenNode import ScreenNode
from mod.client.ui.screenController import ViewBinder, ViewRequest

# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()


# 在modMain中注册的Client System类
class drawClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        print '###__init__ drawClient'
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent('draw', 'drawSystem', 'OpenDrawUiEvent', self, self.OnOpenDrawUi)
        self.ListenForEvent('draw', 'drawSystem', 'DrawEvent', self, self.OnDraw)

    def OnUIInitFinished(self, args):
        uiRegisterSuccess = clientApi.RegisterUI('draw', 'drawUI', 'drawScript.drawClientUI.drawScreen', 'drawUI.main')
        print 'drawUI Register UI success=%s' % (uiRegisterSuccess,)
        clientApi.CreateUI('draw', 'drawUI', {'isHud': 1})
        self.drawUINode = clientApi.GetUI('draw', 'drawUI')
        if self.drawUINode:
            self.drawUINode.InitScreen()
            print 'drawUINODE.InitScreen node=', str(self.drawUINode)
        else:
            print 'FAILED TO drawUINODE.InitScreen!!! drawUINODE=', str(self.drawUINode)

    def OnOpenDrawUi(self, data):
        credits = data['credits']
        self.drawUINode.ShowUi(credits)

    def OnDraw(self, data):
        print 'ONDRAW'
        self.drawUINode.Draw(data)

    def ReturnToServer(self, args):
        response = args
        response['playerId'] = clientApi.GetLocalPlayerId()
        self.NotifyToServer("ActionEvent", args)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
