# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
from io import open
import io
import math
import json
import random
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.commonNetgameApi as commonNetgameApi

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

scoreboard = {}

# 在modMain中注册的Server System类
class impbwServerSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()
        self.initScoreboard = False
        self.mServerFull = False
        self.played = False
        self.isRestarting = False

        self.status = 0
        self.players = []
        self.countdown = 180
        self.runner = None
        self.started = False
        self.time = 0

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), 'AddServerPlayerEvent', self,
                            self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), 'DelServerPlayerEvent',
                           self,
                           self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), 'MobDieEvent',
                            self,
                            self.OnMobDie)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), 'PlayerDieEvent',
                            self,
                            self.OnPlayerDie)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), 'PlayerAttackEntityEvent',
                            self,
                            self.OnPlayerAttackEntity)

        comp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        ruleDict = {
            'option_info': {
                'natural_regeneration': True,  # 自然生命恢复
                'immediate_respawn': True,  # 作弊开启
                'show_death_messages': False,
                'show_coordinates': True
            },
        }
        comp.SetGameRulesInfoServer(ruleDict)
        def a():
            args = {
                'sid': lobbyGameApi.GetServerId(),
                'value': 0
            }
            serverId = lobbyGameApi.GetServerId()
            print 'init recordsid'
            self.RequestToService("impbw", "RecordSidEvent", args)
        commonNetgameApi.AddTimer(3.0, a)
        def b():
            self.tick()
        commonNetgameApi.AddRepeatedTimer(1.0, b)
        def c():
            self.halftick()
        commonNetgameApi.AddRepeatedTimer(0.5, c)

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

    def sendMsgToAll(self, msg):
        for player in serverApi.GetPlayerList():
            self.sendMsg(msg, player)

    def scoreboard(self, mode, line, content='none'):
        # 1 = set
        # 2 = delete
        if serverApi.GetPlayerList():
            playerId = serverApi.GetPlayerList()[0]

            if mode == 1:
                if line in scoreboard.keys():
                    self.sendCmd("/scoreboard players reset %s main" % (scoreboard[line],), playerId)
                scoreboard[line] = content
                self.sendCmd("/scoreboard players set %s main %s" % (content, line), playerId)
            elif mode == 2:
                self.sendCmd("/scoreboard players reset %s main" % (scoreboard[line],), playerId)

    #################################

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        if not self.initScoreboard:
            print '=====initScoreboard====='
            self.sendCmd("/gamerule sendcommandfeedback false", playerId)
            self.sendCmd("/scoreboard objectives add main dummy §c§lMANHUNT", playerId)
            self.sendCmd("/scoreboard players reset * main", playerId)
            self.sendCmd("/scoreboard players set test_item -1 main", playerId)
            self.sendCmd("/scoreboard objectives setdisplay sidebar main ascending", playerId)
            self.scoreboard(1, 1, "§3等待玩家中...")
            self.scoreboard(1, 4, '" "')
            self.scoreboard(1, 8, "§7ICE-MANHUNT-%s" % (lobbyGameApi.GetServerId(),))
            self.initScoreboard = True

        if self.status == 0:
            self.players.append(playerId)

            if len(self.players) < 4:
                args = {
                    'sid': lobbyGameApi.GetServerId(),
                    'value': 0,
                    'count': len(self.players)
                }
                self.RequestToService("manhunt", "RecordSidEvent", args)

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        if self.status == 0 and playerId in self.players:
            args = {
                'sid': lobbyGameApi.GetServerId(),
                'value': 0,
                'count': len(self.players-1)
            }
            self.RequestToService("manhunt", "RecordSidEvent", args)
        if playerId in self.players:
            self.players.pop(self.players.index(playerId))

        if self.status == 0:
            if playerId == self.runner:
                self.end(False, True)
            else:
                if len(self.players) < 2:
                    self.end(True, True)

    def FastStart(self):
        if self.status == 0 and self.countdown > 15:
            self.countdown = 15

    def OnMobDie(self, data):
        entityId = data['id']
        comp = serverApi.GetEngineCompFactory().CreateEngineType(entityId)
        entityType = comp.GetEngineTypeStr()

        if entityType == 'minecraft:ender_dragon':
            self.end(True)

    def OnPlayerAttackEntity(self, data):
        playerId = data['playerId']
        victimId = data['victimId']

        if not self.status:
            data['cancel'] = True
            return

        if playerId == self.runner and victimId in self.players and not self.started:
            self.started = True
            self.sendCmd('/gamemode s @a', playerId)

            for player in serverApi.GetPlayerList():
                self.sendTitle("§a§l游戏开始！", 1, player)
                self.sendTitle("有60秒和平时间！", 1, player)
            return

        if playerId != self.runner and not self.started:
            data['cancel'] = True
            self.sendMsg("§c请等待逃跑者开始游戏！", playerId)
            return

        if self.time < 0:
            data['cancel'] = True
            self.sendMsg("§c和平时间！", playerId)
            return

        if self.status != 1:
            data['cancel'] = True
            return

    def OnPlayerDie(self, data):
        playerId = data['id']
        srcId = data['attacker']

        if playerId == self.runner and srcId in self.players:
            self.end(False)

            self.sendMsg("§a+768NEKO §r击杀逃跑者的额外奖励")
            ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')
            ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(self.runner), 768, 'manhunt win extra')

    def halftick(self):
        if self.status == 1 and not self.started:
            self.sendTitle("§l"+"§c"*self.mRedTitle+"击打任意一名玩家以开始游戏", 3, self.runner)
            self.mRedTitle = not(self.mRedTitle)

    def tick(self):
        # before start
        if self.status == 0:
            if len(self.players) < 3 and self.countdown < 180:
                for player in serverApi.GetPlayerList():
                    self.sendTitle("§c§l人数不够，开始取消！", player)
                self.countdown = 180

            if len(self.players) >= 4 and self.countdown > 15:
                self.countdown = 15
            elif len(self.players) >= 3:
                self.scoreboard(1, 1, "§3即将开始...")
                for player in serverApi.GetPlayerList():
                    if self.countdown > 15:
                        self.sendTitle("§e§l%s" % (self.countdown,), 1, player)
                    else:
                        self.sendTitle("§c§l%s" % (self.countdown,), 1, player)
                    self.sendTitle("游戏即将开始", 2, player)
                self.countdown -= 1

            if len(serverApi.GetPlayerList()) > 3 and not self.mServerFull:
                args = {
                    'sid': lobbyGameApi.GetServerId(),
                    'value': 1
                }
                self.mServerFull = True
                self.RequestToService("manhunt", "RecordSidEvent", args)
            elif len(serverApi.GetPlayerList()) < 4 and self.mServerFull:
                args = {
                    'sid': lobbyGameApi.GetServerId(),
                    'value': 0,
                    'count': len(self.players)
                }
                self.mServerFull = False
                self.RequestToService("manhunt", "RecordSidEvent", args)

            if self.countdown <= 0:
                self.start()
        elif self.status == 1:
            self.time += 1
            self.scoreboard(1, 1, "§3已进行%s秒" % (self.time + 30,))

        if self.played and serverApi.GetPlayerList() <= 0 and not self.isRestarting:
            # reboot logic
            lobbyGameApi.ShutdownServer()
            args = {
                'sid': lobbyGameApi.GetServerId(),
                'value': 1
            }
            self.RequestToService("manhunt", "RecordSidEvent", args)

    def end(self, runnerWin, disconnect=False):
        self.status = 2
        self.isRestarting = True
        ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')

        if runnerWin:
            self.sendTitle('§6§l胜利', 1, self.runner)
            if not disconnect:
                ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(self.runner), 1024, 'manhunt win')
                self.sendMsg('§a+1024NEKO §r击杀末影龙获胜的奖励')
            else:
                ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(self.runner), 64, 'manhunt win disconnect')
                self.sendMsg('§a+64NEKO §r因猎人掉线获胜的奖励')

        else:
            self.sendTitle('§c§l惜败', 1, self.runner)
            mWinners = self.players
            mWinners.pop(self.players.index(self.runner))
            for player in mWinners:
                self.sendTitle('§6§l胜利', 1, player)
                if not disconnect:
                    self.sendMsg('§a+256NEKO §r猎人获胜的奖励（平分）', player)
                    ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(player), 256, 'manhunt win')
                else:
                    self.sendMsg('§a+16NEKO §r因逃跑者掉线获胜的奖励（平分）', player)
                    ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(player), 16, 'manhunt win disconnect')

        def a():
            for player in self.players:
                transData = {'position': [107, 153, 105]}
                lobbyGameApi.TransferToOtherServer(player, 'lobby', json.dumps(transData))
        commonNetgameApi.AddTimer(7.0, a)

        # reboot logic
        def b():
            lobbyGameApi.ShutdownServer()
            args = {
                'sid': lobbyGameApi.GetServerId(),
                'value': 1
            }
            self.RequestToService("manhunt", "RecordSidEvent", args)
        commonNetgameApi.AddTimer(5.0, b)

    def start(self):
        self.time = -60
        self.status = 1
        self.countdown = 180
        self.started = False
        self.played = True

        pos = (random.randint(-100, 100), 200, random.randint(-100, 100))
        for i in range(255):
            comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
            blockDict = comp.GetBlockNew(pos, 0)
            if blockDict['name'] != 'minecraft:air':
                pos = (pos[0], pos[1]-1, pos[0])
            else:
                break

        self.runner = random.choice(self.players)

        # comp = serverApi.GetEngineCompFactory().CreatePos(self.players[0])
        # comp.SetFootPos((pos[0]+2, pos[1], pos[2]+2))
        # comp = serverApi.GetEngineCompFactory().CreatePos(self.players[1])
        # comp.SetFootPos((pos[0]-2, pos[1], pos[2]-2))
        # comp = serverApi.GetEngineCompFactory().CreatePos(self.players[2])
        # comp.SetFootPos((pos[0] + 2, pos[1], pos[2] - 2))
        # if len(self.players) > 3:
        #     comp = serverApi.GetEngineCompFactory().CreatePos(self.players[3])
        #     comp.SetFootPos((pos[0] - 2, pos[1], pos[2] + 2))

        self.sendMsgToAll("逃跑者是§e§l%s§r!" % (lobbyGameApi.GetPlayerNickname(self.runner),))
        self.sendMsg("§a§l你是逃跑者！§r你的唯一目标就是§e击败末影龙§r，你只有一条命！", self.runner)

        self.scoreboard(1, 1, "§6等待逃跑者开始游戏...")

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("lobbyutils", "lobbyutilsClient", 'TestRequest', self, self.OnTestRequest)
