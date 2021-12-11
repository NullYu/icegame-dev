# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi
from mod.client.ui.screenNode import ScreenNode
from mod.client.ui.screenController import ViewBinder, ViewRequest

# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()


# 在modMain中注册的Client System类
class hgClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        print '###__init__ hgClient'
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent('hg', 'hgSystem', 'PlayAnthemEvent', self, self.OnPlayeAnthem)
        self.ListenForEvent('hg', 'hgSystem', 'ShowCountdownEvent', self, self.OnShowCountdown)

    def OnUIInitFinished(self, args):
        uiRegisterSuccess = clientApi.RegisterUI('hg', 'hgUI', 'hgScript.hgClientUI.hgScreen', 'hgUI.main')
        print 'hgUI Register UI success=%s' % (uiRegisterSuccess,)
        clientApi.CreateUI('hg', 'hgUI', {'isHud': 1})
        self.hgUINode = clientApi.GetUI('hg', 'hgUI')
        if self.hgUINode:
            self.hgUINode.InitScreen()
            print 'hgUINODE.InitScreen node=', str(self.hgUINode)
        else:
            print 'FAILED TO hgUINODE.InitScreen!!! hgUINODE=', str(self.hgUINode)

    def OnPlayeAnthem(self, li):
        self.hgUINode.PlayAnthem(dict(sorted(li.items(), key=lambda item: item[1])))

    def OnShowCountdown(self, time):
        self.hgUINode.ShowCountdown(time)

    def ReturnToServer(self, args):
        response = args
        response['playerId'] = clientApi.GetLocalPlayerId()
        self.NotifyToServer("ActionEvent", args)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
