# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
from io import open
import io
import random
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.commonNetgameApi as commonNetgameApi

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()


# 在modMain中注册的Server System类
class hintServerSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

    def ListenEvents(self):

        hints = []
        s = \
            """我们不建议您使用§l§c蝴蝶点§r§7。如果您因为该原因被封禁，活该
您知道吗？我们有官方的交流群！您可以搜索群号851702615加入！
扫黄打非，净网2021。ICE_GAME从严处理任何侵犯他人隐私的行为，最高可同时永久封禁账户，设备，与IP地址。严重者我们将上交司法机关处理。
有问题，但又不方便使用QQ？简单！发送邮件至help@icegame.xyz。您的所有问题都会在这里得到答复。
当您选择游玩「竞技模式」时，您必须保证参加整场比赛（最多可持续90分钟）。中途放弃比赛您将受到惩罚。
ICE_GAME全体团队严格遵守「玩家即是上帝」原则，坚决为玩家提供最优质的服务！当然，这不意味着您可以随意作弊。
您知道吗？非法组队可被封禁。
您知道吗？您不知道！
在「5人团队竞技」模式中，友伤是开启的噢！注意不要伤害您的队友！
想加入服务器管理组？投递简历至apply@icegame.xyz。
我们急需§lPython程序员§r§7。若您有Python开发经验，您可以向我们投递简历！
我很可爱，请给我钱
别欺负管理员！你这个怪物！
使用/hub或/lobby返回主城
遇见了可恨的作弊者？在管理员赶到前使用/votekick投票将其踢出！"""

        lines = s.split('\n')
        for line in lines:
            hints.append(line)
        def a():
            playerList = serverApi.GetPlayerList()
            if len(playerList) > 0:
                for i in range(len(playerList)):
                    comp = serverApi.GetEngineCompFactory().CreateMsg(playerList[i])
                    comp.NotifyOneMessage(playerList[i], random.choice(hints), "§7")
        commonNetgameApi.AddRepeatedTimer(240, a)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("lobbyutils", "lobbyutilsClient", 'TestRequest', self, self.OnTestRequest)
