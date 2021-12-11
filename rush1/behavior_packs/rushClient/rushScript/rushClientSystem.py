# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi

# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()

# 在modMain中注册的Client System类
class rushClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        print "====GameUtilsClientSystem Init ===="
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'OnLocalPlayerStopLoading', self, self.OnLocalPlayerStopLoading)
        self.boardId = None

    def OnLocalPlayerStopLoading(self, data):
        playerId = data['playerId']

        print '======createTextBoard======'
        comp = clientApi.GetEngineCompFactory().CreateTextBoard(clientApi.GetLevelId())
        self.boardId = comp.CreateTextBoardInWorld("§b§lMLGRush\n§f非常火爆的小游戏！在游戏的同时练习自救技能！\n§r§7游戏规则：\n努力挖掉对方的床。挖掉3次即可获得胜利。\n使用手中的§e木剑§7将敌人击下桥，使用方块自救\n\n§c警告：不要毁坏自己的床！", (0.5, 0.4, 0.3, 1), (0, 0, 0, 0), True)
        comp.SetBoardPos(self.boardId, (0, 202, 0))

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
