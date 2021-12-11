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
class brServerSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()
        self.consts = c
        lobbyGameApi.ShieldPlayerJoinText(True)

        self.waiting = []
        self.status = 0
        self.playing = []
        self.timer = 0
        self.kills = {}
        self.countdown = 180

        self.initCircle = False
        self.inGulag = []

        self.airlineTimerObj = None
        self.inJumping = []

    ##############UTILS##############

    def playStartAnimation(self):
        for player in serverApi.GetPlayerList():
            commonNetgameApi.AddTimer(0.2, lambda p: self.sendTitle('§e§l开      战', 1, p), player)
            commonNetgameApi.AddTimer(0.4, lambda p: self.sendTitle('§e§l开     战', 1, p), player)
            commonNetgameApi.AddTimer(0.6, lambda p: self.sendTitle('§e§l开    战', 1, p), player)
            commonNetgameApi.AddTimer(0.8, lambda p: self.sendTitle('§e§l开   战', 1, p), player)
            commonNetgameApi.AddTimer(1.0, lambda p: self.sendTitle('§e§l开  战', 1, p), player)
            commonNetgameApi.AddTimer(1.2, lambda p: self.sendTitle('§e§l开 战', 1, p), player)
            commonNetgameApi.AddTimer(1.4, lambda p: self.sendTitle('§e§l开战', 1, p), player)
            commonNetgameApi.AddTimer(1.4, lambda p: self.sendTitle('§c在单人模式中组队可被封禁！', 2, p), player)

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

    def updateServerStatus(self, status):
        args = {
            'sid': lobbyGameApi.GetServerId(),
            'value': status,
            'count': len(serverApi.GetPlayerList())
        }
        serverId = lobbyGameApi.GetServerId()
        print 'init recordsid'
        self.RequestToServiceMod("service_bw", "RecordSidEvent", args)

    def epoch2Datetime(self, epoch):
        ts = datetime.datetime.fromtimestamp(int(epoch) + 0)
        return ts.strftime('%Y-%m-%d %H:%M:%S')

    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent",
                            self, self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent",
                            self, self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerDieEvent", self,
                            self.OnPlayerDie)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerRespawnEvent", self,
                            self.OnPlayerRespawn)

        gameComp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        gameComp.SetCanBlockSetOnFireByLightning(False)
        gameComp.SetCanActorSetOnFireByLightning(False)

        comp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        ruleDict = {
            'option_info': {
                'natural_regeneration': True,  # 自然生命恢复
                'immediate_respawn': True  # 作弊开启
            },
            'cheat_info': {
                'always_day': True,  # 终为白日
                'mob_griefing': True,  # 生物破坏方块
                'keep_inventory': False,  # 保留物品栏
                'weather_cycle': False,  # 天气更替
                'mob_spawn': False,  # 生物生成
            }
        }
        comp.SetGameRulesInfoServer(ruleDict)
        comp.SetGameDifficulty(2)
        lobbyGameApi.ShieldPlayerJoinText(True)
        commonNetgameApi.AddRepeatedTimer(1.0, self.tick)
        commonNetgameApi.AddRepeatedTimer(1.0, self.BoardTick)

        def b():
            args = {
                'sid': lobbyGameApi.GetServerId(),
                'value': 0
            }
            serverId = lobbyGameApi.GetServerId()
            print 'init recordsid'
            self.RequestToServiceMod("service_sw", "RecordSidEvent", args)

        commonNetgameApi.AddTimer(8.0, b)

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        if self.status == 0:
            self.waiting.append(playerId)
            commonNetgameApi.AddTimer(6.0, lambda p: self.sendMsg('§a您来的正是时候！请等待游戏开始', p), playerId)
            self.setPos(playerId, c.lobbyPos)
            utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
            utilsSystem.SetPlayerSpectate(playerId, False)
        elif self.status == 1:
            utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
            utilsSystem.SetPlayerSpectate(playerId, True)

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

    def BoardTick(self):
        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        do = utilsSystem.TextBoard
        if self.status == 0:
            for player in serverApi.GetPlayerList():
                self.sendCmd('/gamerule sendcommandfeedback false', player)
                self.sendCmd('/gamerule showdeathmessages false', player)
                do(player, True, """
§e§lICE§a_§bGAME§r§l -> §6吃鸡大师§r

§7满%s人即可开始游戏§r
§l目前人数: §e%s人
§f倒计时: §c%s秒

§r§e在ICE_GAME体验吃鸡游戏
§7%s
""" % (c.startCountdown, len(self.waiting), self.countdown, self.epoch2Datetime(time.time())))
        elif self.status == 1 and self.timer < 10:
            for player in serverApi.GetPlayerList():
                do(player, True, """
§e§lICE§a_§bGAME§r§l -> §6吃鸡大师§r

§b跳伞中...§r
点击

§r§e在ICE_GAME体验空岛战争
""")
        elif self.status == 1 and self.timer >= 10:
            for player in serverApi.GetPlayerList():
                do(player, True, """
§e§lICE§a_§bGAME§r§l -> §6吃鸡大师§r
§b比赛已进行%s§r

§e§l场上还剩§b%s§e名玩家

§r§e在ICE_GAME体验空岛战争
""" % (datetime.timedelta(seconds=self.timer), len(self.playing)))

    def OnPlayerDie(self, data):
        playerId = data['id']
        attackerId = serverApi.GetEngineCompFactory().CreateAction(playerId).GetHurtBy()

    def OnPlayerRespawn(self, data):
        playerId = data['id']
        if playerId in self.inGulag:
            self.Elimination(playerId)
        else:
            gulag = serverApi.GetSystem('br', 'brGulag')
            gulag.SendToGulag(playerId)
            self.inGulag.append(playerId)

    def Elimination(self, player):
        pass

    def tick(self):
        # per tick updates
        count = len(serverApi.GetPlayerList())

        if self.status == 0:
            print 'countdown=%s' % self.countdown
            self.timer = 0
            if count < c.startCountdown:
                pass
            elif c.startCountdown <= count <= 24:
                self.countdown -= 1
                for player in serverApi.GetPlayerList():
                    self.sendTitle("§e§l%s" % self.countdown, 1, player)
                    self.sendTitle("游戏即将开始", 2, player)
            if count == 64 and self.countdown > 15:
                self.countdown = 15
            if self.countdown < 180 and count < c.startCountdown:
                self.sendMsgToAll("§c§l人数不够，倒计时取消！")
                self.countdown = 180
            if self.countdown == 0:
                print 'starting!'
                self.start()
                self.status = 1
        elif self.status == 1:
            self.timer += 1
            if not self.inJumping and not self.initCircle:
                # TODO Start circle logic
                pass

        elif self.status == 2:
            for player in serverApi.GetPlayerList():
                self.sendCmd('/gamemode a @s', player)

        self.updateServerStatus(self.status)

    def start(self):
        self.timer = 0
        self.inGulag = []
        for player in self.waiting:
            self.playing.append(player)
            self.kills[player] = 0

        self.waiting = []

        for player in self.playing:
            comp = serverApi.GetEngineCompFactory().CreateFly(player)
            comp.ChangePlayerFlyState(True)
            self.setPos(player, c.airlineStart)
            self.inJumping.append(player)
            self.airlineTimerObj = commonNetgameApi.AddRepeatedTimer(0.5, self.AirlineTick)

        self.status = 1

    # Call for a Redeploy using this API.
    def PlayerRedeploy(self, player):
        pass

    def AirlineTick(self):
        if self.airlineTimerObj and self.status == 1:
            for player in self.inJumping:
                comp = serverApi.GetEngineCompFactory().CreatePos(player)
                pos = comp.GetFootPos()
                comp.SetFootPos((pos[0] + 1, 512, pos[0] + 1))

                comp = serverApi.GetEngineCompFactory().CreateFly(player)
                if not comp.IsPlayerFlying():
                    comp.ChangePlayerFlyState(False)
                    comp.ChangePlayerFlyState(True)

    # MISC LOGICS
    def GasMaskLogic(self, playerId):
        pass

    def GetGasMask(self, player):
        pass
        # return pts left
