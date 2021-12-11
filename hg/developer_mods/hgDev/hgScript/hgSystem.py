# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import datetime
import apolloCommon.commonNetgameApi as commonNetgameApi
import math
import megaScript.megaConsts as c
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.mysqlPool as mysqlPool
cooldown = {}

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

# 在modMain中注册的Server System类
class hgSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        self.status = 0
        self.countdown = 180

        self.consts = c
        lobbyGameApi.ShieldPlayerJoinText(True)

        self.players = {}

        self.waiting = []
        self.timer = 0

        self.kills = {}
        self.deceased = {}

        self.timeBuffer = None
        self.pastMidnight = False

    ##############UTILS##############

    def playStartAnimation(self):
        for player in serverApi.GetPlayerList():
            commonNetgameApi.AddTimer(0.2, lambda p: self.sendTitle('§c§l30      秒', 1, p), player)
            commonNetgameApi.AddTimer(0.4, lambda p: self.sendTitle('§c§l30     秒', 1, p), player)
            commonNetgameApi.AddTimer(0.6, lambda p: self.sendTitle('§c§l30    秒', 1, p), player)
            commonNetgameApi.AddTimer(0.8, lambda p: self.sendTitle('§c§l30   秒', 1, p), player)
            commonNetgameApi.AddTimer(1.0, lambda p: self.sendTitle('§c§l30  秒', 1, p), player)
            commonNetgameApi.AddTimer(1.2, lambda p: self.sendTitle('§c§l30 秒', 1, p), player)
            commonNetgameApi.AddTimer(1.4, lambda p: self.sendTitle('§c§l30秒', 1, p), player)
            commonNetgameApi.AddTimer(1.4, lambda p: self.sendTitle('请在出发台上等待30秒', 2, p), player)

    def sendCmd(self, cmd, playerId):
        comp = serverApi.GetEngineCompFactory().CreateCommand(serverApi.getLevelId())
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

    def updateServerStatus(self, status):
        args = {
            'sid': lobbyGameApi.GetServerId(),
            'value': status,
            'count': len(serverApi.GetPlayerList())
        }
        serverId = lobbyGameApi.GetServerId()
        print 'init recordsid'
        self.RequestToServiceMod("service_bw", "RecordSidEvent", args)

    def getCountInList(self, key, li):
        count = 0
        for item in li:
            if key == li[item]:
                count += 1
        return count

    def WallsCollapse(self):
        for player in self.teams:
            self.sendTitle('§l§c墙塌了', 1, player)
            self.sendTitle('进入战场吧！', 2, player)

        self.gracePeriod = False

    def rank(self, d):
        mComp = 0
        for item in d:
            if (not mComp in d or d[item] > d[mComp]) and item in self.teams:
                mComp = item
        return mComp

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

    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self, self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self, self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerDieEvent", self, self.OnPlayerDie)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerRespawnFinishServerEvent", self, self.OnPlayerRespawnFinishServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerChatEvent", self, self.OnServerChat)

        commonNetgameApi.AddTimer(1.0, self.tick)
        commonNetgameApi.AddTimer(1.0, self.boardTick)

    def OnAddServerPlayer(self, data):
        playerId = data['id']

        self.updateServerStatus(self.status)

        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        comp.SpawnItemToArmor({
            'itemName': 'minecraft:diamond_helmet',
            'count': 0,
            'auxValue': 0
        }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.HEAD)
        comp.SpawnItemToArmor({
            'itemName': 'minecraft:diamond_chestplate',
            'count': 0,
            'auxValue': 0
        }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.BODY)
        comp.SpawnItemToArmor({
            'itemName': 'minecraft:diamond_leggings',
            'count': 0,
            'auxValue': 0
        }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.LEG)
        comp.SpawnItemToArmor({
            'itemName': 'minecraft:diamond_boots',
            'count': 0,
            'auxValue': 0
        }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.FOOT)

        comp = serverApi.GetEngineCompFactory().CreateGame(playerId)
        self.sendCmd("/clear", playerId)
        self.setPos(playerId, c.lobbyPos)
        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        for i in range(36):
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:dirt',
                'count': 0
            }, playerId, i)
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        serverId = lobbyGameApi.GetServerId()

        if self.status == 0:
            def a():
                if self.status == 0:
                    self.sendMsg("§a您来的正是时候！请等待游戏开始。", playerId)

            commonNetgameApi.AddTimer(9.0, a)
            self.waiting.append(playerId)
            utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
            utilsSystem.SetPlayerSpectate(playerId, False)
        elif self.status >= 1:
            utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
            utilsSystem.SetPlayerSpectate(playerId, True)

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        uid = data['uid']
        if playerId in self.waiting:
            self.waiting.pop(self.waiting.index(playerId))
        if playerId in self.players:
            self.players.pop(playerId)

    def OnPlayerDie(self, data):
        playerId = data['id']
        attackerId = data['attacker']

        if self.gracePeriod or self.status != 1:
            return

        self.deceased[playerId] = lobbyGameApi.GetPlayerNickname(self.players[playerId])
        self.players.pop(playerId)
        if attackerId in self.players:
            self.kills[attackerId] += 1

        musicSystem = serverApi.GetSystem('music', 'musicSystem')
        for playerId in serverApi.GetPlayerList():
            musicSystem.PlayMusicToPlayer(playerId, 'sfx.hg.cannon')

    def OnPlayerRespawnFinishServer(self, data):
        playerId = data['playerId']
        self.sendTitle('§c§l您已被淘汰', 1, playerId)
        self.sendTitle('别气馁，您的队伍还有机会', 2, playerId)
        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        utilsSystem.SetPlayerSpectate(playerId, True, True)

        self.NotifyToClient(playerId, 'EliminationEvent', None)


    def OnServerChat(self, data):
        playerId = data['playerId']
        nickname = '？？？'
        msg = data['message']

        data['cancel'] = True

        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        sPos = comp.GetFootPos()

        if not commonNetgameApi.CheckWordsValid(msg):
            self.sendMsg('§3不允许发送该消息，请检查', playerId)
            return

        if self.status == 0:
            msg = "§r§3" + nickname + ": §7" + msg
            self.sendMsgToAll(msg)
        elif self.status >= 1:
            if playerId in self.players:
                isShout = bool(msg[0] == '!' or msg[0] == '！')
                teamName = c.teamNames[self.teams[playerId]]

                if isShout:
                    msg = "§r§3" + nickname + ": §7" + msg
                    for player in self.players:
                        comp = serverApi.GetEngineCompFactory().CreatePos(player)
                        rPos = comp.GetFootPos()

                        dist = self.dist(sPos[0], sPos[1], sPos[2], rPos[0], rPos[1], rPos[2])

                        if dist <= 50:
                            self.sendMsg(msg, player)

                else:
                    msg = "§r§3" + nickname + ": §7" + msg
                    for player in self.players:
                        comp = serverApi.GetEngineCompFactory().CreatePos(player)
                        rPos = comp.GetFootPos()

                        dist = self.dist(sPos[0], sPos[1], sPos[2], rPos[0], rPos[1], rPos[2])

                        if dist <= 50:
                            self.sendMsg(msg, player)
            else:
                self.sendMsg('观战者不能发言', playerId)
                return

    # main ticking logic
    def tick(self):
        count = len(serverApi.GetPlayerList())

        if self.status == 0:
            print 'countdown=%s' % self.countdown
            max = c.maxPlayers

            self.timer = 0
            self.scoreboard(1, 6, "§c%s§f秒" % self.countdown)
            if count < c.startCountdown:
                pass
            elif c.startCountdown <= count <= max:
                self.countdown -= 1
                for player in serverApi.GetPlayerList():
                    self.sendTitle("§e§l%s" % self.countdown, 1, player)
                    self.sendTitle("游戏即将开始", 2, player)
            if count == max and self.countdown > 15:
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

            if self.timer < c.waitTime:

                for player in serverApi.GetPlayerList():

                    comp = serverApi.GetEngineCompFactory().CreatePos(player)
                    footPos = comp.GetFootPos()

                    if footPos[1] < 73:
                        self.sendCmd('/summon lightning_bolt', player)
                        self.sendCmd('/kill', player)

            if self.timer <= c.waitTime+1:
                for player in serverApi.GetPlayerList():
                    self.NotifyToClient(player, 'ShowCountdownEvent', (30 - self.timer))

            comp = serverApi.GetEngineCompFactory().CreateTime(serverApi.GetLevelId())
            gameTime = comp.GetTime()
            # time logic BELOW

            if gameTime > 15000 and not self.pastMidnight:
                musicSystem = serverApi.GetSystem('music', 'musicSystem')
                musicSystem.PlayMusicToPlayer(player, 'sfx.hg.anthem')
                for player in self.players:
                    self.NotifyToClient(player, 'PlayAnthemEvent', self.deceased)
                self.pastMidnight = True

            if 0 < gameTime < 15000 and self.pastMidnight:
                self.pastMidnight = False

            # time logic ABOVE before buffer is justified
            self.timeBuffer = gameTime

        if len(self.players) == 1:
            pass
            # TODO Win logic here

    def win(self, team):
        teamName = c.teamNames[team]
        self.status = 2

        for player in self.teams:
            if self.teams[player] == team:
                self.sendTitle("§6§l胜利", 1, player)
                self.sendTitle("恭喜您获得胜利！！！", 2, player)
                self.sendMsg("§a+128NEKO +16CREDITS §f获得胜利的奖励", player)

                ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')
                ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(player), 128, 'bw win')
                ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(player), 16, 'bw win', True)

        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        utilsSystem.ShowWinBanner(self.rank(self.kills))

        def a():
            self.status = 0
            self.updateServerStatus(self.status)
            for p in serverApi.GetPlayerList():
                self.RequestToServiceMod("bw", "RequestMatchmakingEvent", {
                    'playerId': p,
                    'mode': commonNetgameApi.GetServerType()
                }, self.BwMatchmakingCallback, 2)

            self.countdown = 180

            rebootSystem = serverApi.GetSystem('reboot', 'rebootSystem')
            rebootSystem.DoReboot(False)

        commonNetgameApi.AddTimer(15.0, a)

        def b():
            self.InitArena()

        commonNetgameApi.AddTimer(17.0, b)


    def start(self):
        mTeamAssign = 1
        self.timer = 0
        self.pastMidnight = False
        self.kills = {}
        self.deceased = {}
        comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
        districts = c.districtsTemplate

        for player in self.waiting:
            self.kills[player] = 0
            self.sendCmd('/gamemode s', player)
            pos = self.waiting.index(player)
            self.players[player] = districts[pos]

            posList = c.pos
            self.setPos(player, posList[pos])

            self.sendMsg('战斗将在30秒后打响\n您发送的消息15格内的玩家可见，使用(!)发送喊叫，50格内玩家可见。', player)

            self.timeBuffer = 1000
            comp = serverApi.GetEngineCompFactory().CreateTime(serverApi.GetLevelId())
            comp.SetTime(1000)

        self.waiting = []

        self.playStartAnimation()


    def boardTick(self):
        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        do = utilsSystem.TextBoard
        if self.status == 0:
            for player in serverApi.GetPlayerList():
                self.sendCmd('/gamerule sendcommandfeedback false', player)
                self.sendCmd('/gamerule showdeathmessages false', player)
                do(player, True, """
§e§lICE§a_§bGAME§r§l -> §e饥饿§6游戏§r

§7满%s人即可开始游戏§r
§l目前人数: §e%s人
§f倒计时: §c%s秒

§r§e在ICE_GAME体验饥饿游戏【电影还原】
§7%s
""" % (c.startCountdown, len(self.waiting), self.countdown, self.epoch2Datetime(time.time())))
        elif self.status == 1:
            for player in serverApi.GetPlayerList():
                do(player, False)

