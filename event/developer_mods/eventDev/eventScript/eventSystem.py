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
import eventScript.eventConsts as c

mysqlPool.InitDB(30)

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()


##

# 在modMain中注册的Server System类
class eventSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        self.consts = c
        self.timeStamp = c.originalTimestamp
        self.enableMusic = False

    def ListenEvents(self):
        self.ListenForEvent('event', 'eventClient', 'ActionEvent', self, self.OnClientAction)

        commonNetgameApi.AddRepeatedTimer(1.0, self.tick)

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

    def OnClientAction(self, data):
        pass

    def tick(self):
        t = int(time.time() - self.timeStamp)
        shoutSystem = serverApi.GetSystem('shout', 'shoutSystem')

        # TODO Remove debug TRUE statement
        if commonNetgameApi.GetServerType() == 'lobby' or True:

            print t

            if -3600 <= t <= 0:
                for player in serverApi.GetPlayerList():
                    self.NotifyToClient(player, 'UpdateTimerEvent', t)

            if t == -3600:
                self.enableMusic = True
                shoutSystem.sendGlobalMsg("§l§c元旦§f庆典 §e将在§660§e分钟后开始！！！")
            elif t == -1800:
                shoutSystem.sendGlobalMsg("§l§c元旦§f庆典 §e将在§630§e分钟后开始！！！")
            elif t == -600:
                shoutSystem.sendGlobalMsg("§l§c元旦§f庆典 §e将在§610§e分钟后开始！！！")
            elif t == -180:
                shoutSystem.sendGlobalMsg("§l§c元旦§f庆典 §e将在§63§e分钟后开始！！！请尽快进入大厅服！")
            elif t == -60:
                shoutSystem.sendGlobalMsg("§l§c元旦§f庆典 §6将在§c60§6秒后开始！！！请尽快进入大厅服！")
            elif t == -10:
                shoutSystem.sendGlobalMsg("§l§c元旦§f庆典 §6将在§c10§6秒后开始！！！")
                shoutSystem.sendGlobalMsg("§l§c§o新年倒计时 10 秒")
            elif t == 0:
                self.startCelebration()

            if t >= -10:
                for player in serverApi.GetPlayerList():
                    self.sendMsg("§l§c§o%s" % -t, player)
                    self.sendTitle("§l§6§o%s" % -t, 1, player)
                    self.sendTitle("§l§c§o新年倒计时 %s 秒" % -t, 3, player)
                    self.sendTitle("§l新年倒计时" % -t, 2, player)

        else:
            pass

    def startCelebration(self):
        # visuals - fireworks, game time, etc..
        t = time.time() - self.timeStamp
        self.sendCmd('/time set 18000', serverApi.GetPlayerList()[0])
        if t % 2 == 0:
            for player in serverApi.GetPlayerList():
                self.sendCmd('/time set 18000', player )

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("lobbyutils", "lobbyutilsClient", 'TestRequest', self, self.OnTestRequest)
