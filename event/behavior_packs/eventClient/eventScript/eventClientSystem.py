# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi
from mod.client.ui.screenNode import ScreenNode
from mod.client.ui.screenController import ViewBinder, ViewRequest

# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()


# 在modMain中注册的Client System类
class eventClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        print '###__init__ eventClient'
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent('event', 'eventSystem', 'ShoweventEvent', self, self.OnShowevent)
        self.ListenForEvent('event', 'eventSystem', 'UpdateTimerEvent', self, self.OnUpdateTimer)

    def OnUIInitFinished(self, args):
        uiRegisterSuccess = clientApi.RegisterUI('event', 'eventUI', 'eventScript.eventClientUI.eventScreen', 'eventUI.main')
        print 'eventUI Register UI success=%s' % (uiRegisterSuccess,)
        clientApi.CreateUI('event', 'eventUI', {'isHud': 1})
        self.eventUINode = clientApi.GetUI('event', 'eventUI')
        if self.eventUINode:
            self.eventUINode.InitScreen()
            print 'eventUINODE.InitScreen node=', str(self.eventUINode)
        else:
            print 'FAILED TO eventUINODE.InitScreen!!! eventUINODE=', str(self.eventUINode)

    def OnShowevent(self, data):
        self.eventUINode.ShowUi(data['title'], data['content'], data['time'])
        print 'OnShowevent content = %s' % (data['content'],)

    def OnUpdateTimer(self, timer):
        self.eventUINode.UpdateTimer(-timer)

    def ReturnToServer(self, args):
        response = args
        response['playerId'] = clientApi.GetLocalPlayerId()
        self.NotifyToServer("ActionEvent", args)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
