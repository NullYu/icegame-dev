# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import apolloCommon.commonNetgameApi as commonNetgameApi
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.mysqlPool as mysqlPool

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

# 在modMain中注册的Server System类
class matchSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        self.matching = []

    ##############UTILS##############

    def sendCmd(self, cmd, playerId):
        comp = serverApi.GetEngineCompFactory().CreateCommand(serverApi.GetLevelId())
        comp.SetCommand(cmd, playerId)

    def sendTitle(self, title, type, playerId):
        if (type == 1):
            self.sendCmd("/title @s title " + title, playerId)
        elif (type == 2):
            self.sendCmd("/title @s subtitle " + title, playerId)
        elif (type == 3):
            self.sendCmd("/title @s actionbar " + title, playerId)
        else:
            print 'invalid params for call/sendTitle(): type'

    def forceSelect(self, slot, playerId):
        comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
        comp.ChangeSelectSlot(slot)

    def sendMsg(self, msg, playerId):
        comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
        comp.NotifyOneMessage(playerId, msg, "§f")
    #################################

    def ListenEvents(self):
        pass
        # self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self,
        #                     self.OnCommand)
        self.ListenForEvent('unrankedService', 'unrankedService', 'UpdateMatchEvent', self, self.UpdateMatch)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self, self.OnDelServerPlayer)

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        if playerId in self.matching:
            self.matching.pop(self.matching.index(playerId))

    def UpdateMatch(self, args):
        print 'CALL OnCallback args=' + str(args)
        player2Id = 0
        try:
            event = args["event"]
        except TypeError:
            event = "error"
        playerId = lobbyGameApi.GetPlayerIdByUid(args["playerId"])
        try:
            server = args['server']
        except KeyError:
            pass

        if event == "RequestMatchmakingEvent":
            value = args['value']
            if value == 'waiting':
                self.sendTitle("§e正在匹配...", 1, playerId)
                self.sendTitle("§l匹配进度：§r§b等待玩家§7》等待可用的房间》开始比赛", 3, playerId)
            elif value == 'queue':
                self.sendTitle("§e正在等待空闲房间...", 1, playerId)
                self.sendTitle("我们的比赛服务器爆满，因此可能需要一些等待。", 2, playerId)
                self.sendTitle("§l匹配进度：§r§b等待玩家》等待可用的房间§7》开始比赛", 3, playerId)
            elif value == 'ready':
                self.sendTitle("§a匹配成功 即将开始", 1, playerId)
                self.sendTitle("§a匹配成功 即将开始", 1, playerId)
                self.sendMsg("§3已找到对手，即将将您连接到比赛服务器%s，请稍作等待" % (args['server'],),playerId)

                # args = {
                #     "playerId": playerId,
                #     "uid": lobbyGameApi.GetPlayerUid(playerId),
                #     "mode": args['mode'],
                #     "server": server
                # }
                # self.RequestToService("matchmaking", "NotifyStartGameEvent", args, self.OnCallback)
                print 'send matchmaking/NotifyStartGameEvent args=' + str(args)
                lobbyGameApi.TransferToOtherServerById(playerId, server)
                lobbyGameApi.TransferToOtherServerById(lobbyGameApi.GetPlayerIdByUid(args['rivalId']), server)
    def UnrankedMatch(self, playerId, mode):

        if playerId in self.matching:
            self.sendMsg("§7您已经在匹配中了", playerId)
            return
        else:
            self.matching.append(playerId)

        self.sendTitle('§3正在与匹配服通讯...', 1, playerId)
        args = {
            "playerId": lobbyGameApi.GetPlayerUid(playerId),
            "mode": mode,
            "operation": "pre_start"
        }
        self.RequestToService("matchmaking", "RequestMatchmakingEvent", args)
