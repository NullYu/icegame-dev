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
class brGulagSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()
        self.consts = c
        lobbyGameApi.ShieldPlayerJoinText(True)

        self.queue = []
        self.playing = ()

        self.timer = 90

    ##############UTILS##############

    def playStartAnimation(self):
        for player in serverApi.GetPlayerList():
            commonNetgameApi.AddTimer(0.2, lambda p: self.sendTitle('§c§l开      战', 1, p), player)
            commonNetgameApi.AddTimer(0.4, lambda p: self.sendTitle('§c§l开     战', 1, p), player)
            commonNetgameApi.AddTimer(0.6, lambda p: self.sendTitle('§c§l开    战', 1, p), player)
            commonNetgameApi.AddTimer(0.8, lambda p: self.sendTitle('§c§l开   战', 1, p), player)
            commonNetgameApi.AddTimer(1.0, lambda p: self.sendTitle('§c§l开  战', 1, p), player)
            commonNetgameApi.AddTimer(1.2, lambda p: self.sendTitle('§c§l开 战', 1, p), player)
            commonNetgameApi.AddTimer(1.4, lambda p: self.sendTitle('§c§l开战', 1, p), player)
            commonNetgameApi.AddTimer(1.4, lambda p: self.sendTitle('§b§l获胜以重新部署', 2, p), player)

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

    def InitArena(self):
        print 'ARENA INIT!!!'
        lobbyGameApi.ResetServer()

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
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent",
                            self, self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerAttackEntityEvent",
                            self, self.OnPlayerAttackEntity)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent",
                            self, self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerDieEvent", self,
                            self.OnPlayerDie)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerRespawnEvent", self,
                            self.OnPlayerRespawn)

    def SendToGulag(self, playerId):
        self.queue.append(playerId)

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        if playerId in self.queue:
            self.queue.pop(self.queue.index(playerId))
        if playerId in self.playing:
            self.GulagWin(list(self.playing).pop(self.playing.index(playerId)))

    def OnPlayerAttackEntity(self, data):
        victimId = data['victimId']
        if not victimId in self.playing:
            data['cancel'] = True

    def OnPlayerDie(self, data):
        playerId = data['id']
        attackerId = serverApi.GetEngineCompFactory().CreateAction(playerId).GetHurtBy()

        if attackerId in self.playing and playerId in self.playing:
            self.GulagWin(attackerId)

    def GulagWin(self, playerId):
        self.sendTitle('§l§b古拉格胜利者', 1, playerId)
        self.sendTitle('正在将您送回战场', 2, playerId)
        main = serverApi.GetSystem('br', 'brSystem')
        main.PlayerRedeploy(playerId)

        self.playing = ()

    def BwMatchmakingCallback(self, suc, data):
        if not suc:
            print 'OnCallback timeout'
            return
        value = data['value']
        playerId = data['playerId']

        if value == 0:
            self.sendMsg("§c§l无法分配房间：§r没有开放的房间可供您加入。稍后将您传送回主城。", playerId)

            def a():
                transData = {'position': [1, 2, 3]}
                lobbyGameApi.TransferToOtherServer(playerId, 'lobby', json.dumps(transData))

            commonNetgameApi.AddTimer(3.0, a)
            return
        elif value == 1:
            sid = data['sid']
            self.sendMsg("§3即将将您传送至%s-%s，请稍等片刻" % (commonNetgameApi.GetServerType(), sid), playerId)

            def a():
                transData = {'position': [1, 2, 3]}
                lobbyGameApi.TransferToOtherServerById(playerId, sid, json.dumps(transData))

            commonNetgameApi.AddTimer(1.0, a)

    def tick(self):
        textboard = serverApi.GetSystem('utils', 'utilsSystem').Textboard
        for player in self.queue:
            if len(self.queue) >= 2 and (len(self.queue) % 2 == 0 or player != self.queue[-1]):
                self.timer = c.gulagTimeout
                textboard(player, True, """
§l§b%s §r§f场比赛后将轮到您

§l§e当前：
§f%s §r§3VS §l§f%s
""" % (self.queue.index(player)/2+1, lobbyGameApi.GetPlayerNickname(self.playing[0]), lobbyGameApi.GetPlayerNickname(self.playing[1])))
            elif len(self.queue) < 2 or (len(self.queue) % 2 == 1 and player == self.queue[-1]):
                self.timer -= 1
                textboard(player, True, """
§l§b正在寻找对手...

§l§e若寻找不到对手，将在
§f%s §e后自动重新部署
""" % (datetime.timedelta(seconds=self.timer),))

        if len(self.queue) % 2 == 0:
            self.timer = c.gulagTimeout
        else:
            self.timer -= 1
            if self.timer <= 0:
                textboard(self.queue[-1], False)
                self.sendTitle('§l§b古拉格胜利者', 1, self.queue[-1])
                self.sendTitle('正在将您送回战场', 2, self.queue[-1])
                main = serverApi.GetSystem('br', 'brSystem')
                main.PlayerRedeploy(self.queue[-1])

                self.queue.pop(-1)

        if not self.playing and len(self.queue) >= 2:
            commonNetgameApi.AddTimer(3.0, lambda a: self.startFight(self.queue[0], self.queue[1]))


    def startFight(self, p1, p2):
        self.queue.pop(0)
        self.queue.pop(1)
        self.setPos(p1, c.gulagPos1)
        self.setPos(p2, c.gulagPos2)
        musicSystem = serverApi.GetSystem('music', 'musicSystem')
        musicSystem.PlayMusicToPlayer(p1, 'sfx.br.gulagBeeper')
        musicSystem.PlayMusicToPlayer(p2, 'sfx.br.gulagBeeper')
        def a():
            musicSystem.PlayMusicToPlayer(p1, 'sfx.br.gulagStart')
            musicSystem.PlayMusicToPlayer(p2, 'sfx.br.gulagStart')
        commonNetgameApi.AddTimer(1.0, a)
