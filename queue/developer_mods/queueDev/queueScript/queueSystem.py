# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import random
import datetime, math
import json
import queueScript.queueConsts as c
import apolloCommon.commonNetgameApi as commonNetgameApi
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.mysqlPool as mysqlPool

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

# 在modMain中注册的Server System类
class queueSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        # self.queue[0],[1] normal,prio respectively
        self.queue = [[], []]
        self.targetPlayers = 30
        self.playerLeaveBuffer = 0

        self.maxSlots = c.slots

        self.countUnlocked = True
        self.countLockBuffer = None

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

    def setPos(self, playerId, pos):
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        re = comp.SetFootPos(pos)
        return re
    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self, self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self, self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self, self.DirectCancel)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerChatEvent", self, self.DirectCancel)
        self.ListenForEvent('queue', 'queueMasterSystem', 'GetServerStat', self, self.GetServerStatRet)

        # return
        # aTODO Remove debug section

        lobbyGameApi.ChangeAllPerformanceSwitch(False)
        commonNetgameApi.AddRepeatedTimer(10.0, self.tick)
        commonNetgameApi.AddRepeatedTimer(5.0, self.halfTick)

    def DirectCancel(self, data):
        data['cancel'] = True

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        uid = lobbyGameApi.GetPlayerUid(playerId)

        sql = 'SELECT * FROM prioq WHERE uid=%s AND (expire < 0 OR expire > %s);'
        def Cb(args):
            if args:
                self.queue[1].append(playerId)
            else:
                self.queue[0].append(playerId)
        mysqlPool.AsyncQueryWithOrderKey('checkQueuePriority', sql, (uid, time.time()), Cb)


        commonNetgameApi.AddTimer(7.0, lambda p: self.sendMsg('§6这个服务器满了', p), playerId)

        comp = serverApi.GetEngineCompFactory().CreateName(playerId)
        comp.SetName(" ")

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        if playerId in self.queue[0]:
            self.queue[0].pop(self.queue[0].index(playerId))
        else:
            self.queue[1].pop(self.queue[1].index(playerId))
        if self.playerLeaveBuffer > 0:
            self.playerLeaveBuffer -= 1

    def tick(self):
        for queue in self.queue:
            for player in queue:
                self.sendCmd('/effect @s instant_health 21 255 true', player)
                pos = queue.index(player)+1
                self.sendMsg('§6您在队伍中的位置: §l%s' % pos, player)
                msg = """§l§7§oFACK
CRAFT

§r§6生存服满了
§r§6您在队伍中的位置: §l%s
§r§6预计排队时长: §l%s

§r§6您可以选择捐赠以获得优先队列状态。点击左上角商店按钮了解更多。
""" % (pos, datetime.timedelta(seconds=int(math.floor(pos*90))))
                comp = serverApi.GetEngineCompFactory().CreateGame(player)
                comp.SetOneTipMessage(player, msg)

    def halfTick(self):
        data = {
            'sid': lobbyGameApi.GetServerId(),
            'type': 'sc'
        }
        self.NotifyToMaster("GetServerStat", data)

        for queue in self.queue:
            for player in queue:
                self.setPos(player, (0.5, 4, 0.5))
                self.sendCmd('/effect @s invisibility 999 1 true', player)

    def GetServerStatRet(self, count):

        print 'GetServerStatRet count=%s' % count

        if self.countLockBuffer == None:
            self.countLockBuffer = count
            self.countUnlocked = True
        else:
            if count != self.countLockBuffer:
                self.countUnlocked = True
                self.countLockBuffer = count
            else:
                self.countUnlocked = False

        print 'COUNTLOCK = %s' % self.countUnlocked

        if count < self.targetPlayers and self.countUnlocked:
            print 'trying to send player from queue'
            allocate = self.targetPlayers-count
            if random.randint(0, 100) < 65:
                for i in range(allocate):
                    try:
                        transData = {'position': [1, 2, 3]}
                        lobbyGameApi.TransferToOtherServer(self.queue[1][i], 'sc', json.dumps(transData))
                    except IndexError:
                        break
            else:
                for i in range(allocate):
                    try:
                        transData = {'position': [1, 2, 3]}
                        lobbyGameApi.TransferToOtherServer(self.queue[0][i], 'sc', json.dumps(transData))
                    except IndexError:
                        break
