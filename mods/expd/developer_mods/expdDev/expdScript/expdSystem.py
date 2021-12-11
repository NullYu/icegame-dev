# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import json
import datetime
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.redisPool as redisPool
import apolloCommon.commonNetgameApi as commonNetgameApi
import apolloCommon.mysqlPool as mysqlPool

mysqlPool.InitDB(30)

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()


##

# 在modMain中注册的Server System类
class expdSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        self.players = {}
        self.whitelist = [
            'lobby',
            'queue',
            'auth',
            'surv'
        ]

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self, self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self, self.OnDelServerPlayer)
        pass
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

    def epoch2Datetime(self, epoch):
        ts = datetime.datetime.fromtimestamp(int(epoch))
        return ts.strftime('%Y-%m-%d %H:%M:%S')

    def sendMsg(self, msg, playerId):
        comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
        comp.NotifyOneMessage(playerId, msg, "§f")

    def IsValidServer(self):
        serverType = commonNetgameApi.GetServerType()
        isValid = False
        for item in self.whitelist:
            if item in serverType:
                isValid = True
                break

        return isValid

    # #############UTILS##############

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        uid = lobbyGameApi.GetPlayerUid(playerId)

        sql = 'SELECT id,endDate FROM expdData WHERE uid=%s AND valid=1 AND (endDate=-1 OR endDate>%s);'
        def Cb(args):
            if args:
                if not self.IsValidServer():
                    lobbyGameApi.TryToKickoutPlayer(playerId, "§e§l无法登录\n§f§l为什么？§r您不被允许以此方式登录该子服务器。尝试从主城登录。")
                    return

                data = args[0]
                id = data[0]
                endDate = data[1]
                self.players[playerId] = [id, endDate]

                response = {
                    "id": id,
                    "endDate": endDate,
                    "playerId": playerId
                }
                self.NotifyToClient(playerId, "ShowCdEvent", response)
            else:
                self.players[playerId] = False

        mysqlPool.AsyncQueryWithOrderKey('czs89d719082', sql, (uid, time.time()), Cb)

    def OnDelServerPlayer(self, data):
        playerId = data['playerId']
        if playerId in self.players and self.players[playerId]:
            self.players.pop(playerId)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("lobbyutils", "lobbyutilsClient", 'TestRequest', self, self.OnTestRequest)
