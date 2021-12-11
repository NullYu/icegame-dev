# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import math
import random
import datetime
import json
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.commonNetgameApi as commonNetgameApi
import swScript.swConsts as c
import apolloCommon.mysqlPool as mysqlPool

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

initScoreboard = False

scoreboard = {}


# 在modMain中注册的Server System类
class brCircleSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()
        self.consts = c

        self.circleStage = 0
        self.timer = c.circleTimes[0]

        # setting a initial circle
        # fixed value - range=900
        ref = random.randint(0, 100)
        self.pos1 = [ref, ref]
        self.pos2 = [ref + 900, ref + 900]
        self.goal = None

        self.gasDmgBuildup = {}
        self.gasMoving = 4

    ##############UTILS##############

    def rank(self, d):
        mComp = 0
        for item in d:
            if (not mComp in d or d[item] > d[mComp]) and item in self.teams:
                mComp = item
        return mComp

    def getIfLegalBreak(self, pos):
        for player in self.blocks:
            if pos in self.blocks[player]:
                return True
        return False

    def getCountInList(self, key, li):
        count = 0
        for item in li:
            if key == li[item]:
                count += 1
        return count

    def getMatchingList(self, key, object):
        ret = []
        for item in object:
            if key == object[item]:
                ret.append(item)
        return ret

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

    def sendMsgToAll(self, msg):
        for player in serverApi.GetPlayerList():
            self.sendMsg(msg, player)

    def sendCmdToAll(self, msg):
        for player in serverApi.GetPlayerList():
            self.sendCmd(msg, player)

    def board(self, player, msg):
        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        utilsSystem.TextBoard(player, True, msg)

    def setPos(self, playerId, pos):
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        re = comp.SetFootPos(pos)
        return re

    def dist(self, x1, y1, z1, x2, y2, z2):
        """
        运算3维空间距离，返回float
        """
        p = ((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) ** 0.5
        re = float('%.1f' % p)
        return re

    def epoch2Datetime(self, epoch):
        ts = datetime.datetime.fromtimestamp(int(epoch) + 0)
        return ts.strftime('%Y-%m-%d %H:%M:%S')

    #################################

    def ListenEvents(self):
        commonNetgameApi.AddRepeatedTimer(1.0, self.tick)

    def StartGas(self):
        self.gasMoving = 4
        ref = (
            random.randint(
                self.pos1[0], self.pos1[0] + (self.pos2[0] - c.circleSize[self.circleStage])
            ),
            random.randint(
                self.pos1[1], self.pos1[1] + (self.pos2[1] - c.circleSize[self.circleStage])
            )
        )
        self.goal = (
            (ref[0], ref[1]),
            (ref[0] + c.circleSize, ref[1] + c.circleSize)
        )

    def tick(self):
        if self.timer <= 0:
            self.StartGas()

        if self.gasMoving > 0:
            if self.pos1[0] < self.goal[0][0]:
                self.pos1[0] += 6
                if self.pos1[0] >= self.goal[0][0]:
                    self.pos1[0] = self.goal[0][0]
                    self.gasMoving -= 1

            if self.pos1[1] < self.goal[0][1]:
                self.pos1[1] += 6
                if self.pos1[1] >= self.goal[0][1]:
                    self.pos1[1] = self.goal[0][1]
                    self.gasMoving -= 1

            if self.pos2[0] > self.goal[1][0]:
                self.pos2[0] -= 6
                if self.pos2[0] <= self.goal[1][0]:
                    self.pos2[0] = self.goal[1][0]
                    self.gasMoving -= 1

            if self.pos2[1] > self.goal[1][1]:
                self.pos2[1] -= 6
                if self.pos2[1] <= self.goal[1][1]:
                    self.pos2[1] = self.goal[1][1]
                    self.gasMoving -= 1

        # player logics
        playerList = serverApi.GetSystem('br', 'brSystem').playing
        for player in playerList:
            comp = serverApi.GetEngineCompFactory().CreatePos(player)
            pos = comp.GetPos()

            if pos[0] not in range(self.pos1[0], self.pos2[0]) or pos[2] not in range(self.pos1[1], self.pos2[1]):
                gasMasked = serverApi.GetSystem('br', 'brSystem').GetGasMask(player)  # <---HERE
                if gasMasked:
                    serverApi.GetSystem('br', 'brSystem').GasMaskLogic(player)
                else:
                    comp = serverApi.GetEngineCompFactory().CreateHurt(player)
                    if self.gasMoving:
                        comp.Hurt(1, serverApi.GetMinecraftEnum().ActorDamageCause.Suffocation, None, None, False)
                        self.gasDmgBuildup[player] = 0
                    else:
                        comp.Hurt(2 + int(math.floor(self.gasDmgBuildup[player])),
                                  serverApi.GetMinecraftEnum().ActorDamageCause.Suffocation, None, None, False)
                        self.gasDmgBuildup[player] += 0.5
            else:
                self.gasDmgBuildup[player] = 0
