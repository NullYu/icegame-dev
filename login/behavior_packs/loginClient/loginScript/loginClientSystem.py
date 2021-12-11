# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi

# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()


# 在modMain中注册的Client System类
class loginClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        print "====loginClientSystem Init ===="

    def ListenEvents(self):
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), "OnLocalPlayerStopLoading", self, self.OnLocalPlayerStopLoading)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), "OnClientPlayerStartMove", self, self.OnClientPlayerStartMove)

    def OnLocalPlayerStopLoading(self):
        comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId)
        comp.SetRenderLocalPlayer(False)

        self.NotifyToServer("DoneLoading", clientApi.GetLocalPlayerId())

    def OnClientPlayerStartMove(self):
        self.NotifyToServer("LoginEvent", clientApi.GetLocalPlayerId())
