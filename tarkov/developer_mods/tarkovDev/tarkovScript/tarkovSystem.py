# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import json
import random
import datetime
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.redisPool as redisPool
import apolloCommon.commonNetgameApi as commonNetgameApi
import apolloCommon.mysqlPool as mysqlPool
import v5Script.v5Consts as c

mysqlPool.InitDB(30)

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()


# ## ! ## #
u"""
    Special development instructions for this mod:
    Complete UI interfaces and test before moving on to main mod logics.
    Client content (especially UI) must be complete before testing of more complex server logics.
"""

##

# 在modMain中注册的Server System类
class tarkovSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()
        self.consts = c
        
        self.timer = 0
        self.countdown = 60

        # 0=t, 1=ct

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self, self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self, self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(),"PlayerInventoryOpenScriptServerEvent", self, self.OnPlayerInventoryOpenScriptServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self, self.OnCommand)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DamageEvent", self, self.OnDamage)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnCarriedNewItemChangedServerEvent", self, self.OnOnCarriedNewItemChangedServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerAttackEntityEvent", self, self.OnPlayerAttackEntity)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerEntityTryPlaceBlockEvent", self, self.OnServerEntityTryPlaceBlock)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ExplosionServerEvent", self, self.OnExplosionServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerRespawnFinishServerEvent", self, self.OnPlayerRespawnFinishServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ActorUseItemServerEvent", self, self.OnActorUseItemServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerChatEvent", self, self.OnServerChat)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerBlockUseEvent", self, self.OnServerBlockUse)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerInteractServerEvent", self, self.OnPlayerInteractServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnScriptTickServer", self, self.OnScriptTickServer)

        # self.ListenForEvent('hud', 'hudClient', "DisplayDeathDoneEvent", self, self.OnDisplayDeathDone)
        # self.ListenForEvent('music', 'musicSystem', 'CreateMusicIdEvent', self, self.OnCreateMusicId)

        self.ListenForEvent('tarkov', 'tarkovClient', 'ActionEvent', self, self.OnClientAction)

        self.ListenForEvent('hud', 'hudSystem', 'PlayerDeathEvent', self, self.HudPlayerDeathEvent)

        commonNetgameApi.AddRepeatedTimer(1.0, self.tick)

        comp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        ruleDict = {
            'option_info': {
                'natural_regeneration': False,  # 自然生命恢复
                'show_death_messages': False,
                'immediate_respawn': True
            },
            'cheat_info': {
                'always_day': True,  # 终为白日
                'mob_griefing': False,  # 生物破坏方块
                'keep_inventory': False,  # 保留物品栏
                'weather_cycle': False,  # 天气更替
                'mob_spawn': False,  # 生物生成
            }
        }
        comp.SetGameRulesInfoServer(ruleDict)

        def a():
            self.updateServerStatus(self.status, True)
        commonNetgameApi.AddTimer(10.0, a)

        comp = serverApi.GetEngineCompFactory().CreateBlockUseEventWhiteList(serverApi.GetLevelId())
        comp.AddBlockItemListenForUseEvent("minecraft:furnace")
        comp.AddBlockItemListenForUseEvent("minecraft:crafting_table")
        comp.AddBlockItemListenForUseEvent("minecraft:barrel")
        comp.AddBlockItemListenForUseEvent("minecraft:brewing_stand")
        comp.AddBlockItemListenForUseEvent("minecraft:chest")

    ##############UTILS##############

    def sendCmd(self, cmd, playerId):
        comp = serverApi.GetEngineCompFactory().CreateCommand(serverApi.GetLevelId())
        comp.SetCommand(cmd, playerId)

    def sendMsgToAll(self, msg):
        for player in serverApi.GetPlayerList():
            self.sendMsg(msg, player)

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

    def setPos(self, playerId, pos):
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        re = comp.SetFootPos(pos)
        return re

    def rank(self, d):
        mComp = 0
        for item in d:
            if (not mComp in d or d[item] > d[mComp]) and item in self.teams:
                mComp = item
        return mComp

    def updateServerStatus(self, status, isOverride=False):
        args = {
            'sid': lobbyGameApi.GetServerId(),
            'value': status,
            'override': isOverride
        }
        serverId = lobbyGameApi.GetServerId()
        print 'init recordsid'
        self.RequestToServiceMod("service_tarkov", "RecordSidEvent", args)

    def getCountInDict(self, key, dic):
        ret = 0
        for item in dic:
            if dic[item] == key:
                ret += 1
        return ret

    def dist(self, x1, y1, z1, x2, y2, z2):
        """
        运算3维空间距离，返回float
        """
        p = ((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) ** 0.5
        re = float('%.1f' % p)
        return re

    def reset_selectionData(self):
        self.selectionData = {
            0: {},
            1: {}
        }

    def OnClientAction(self, data):
        operation = data['operation']
        playerId = data['playerId']

        print 'clientaction rcv, operation=', operation

    # ################## UI INTERFACES #####################
    u"""
        This section contains UI interface functions.
        Complete development of this section before moving on to server code.
    """

    # ################# SERVER CODE ###############
    u"""
        Starting in this section are the server codes
    """

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        self.playerEquips[playerId] = 0
        self.playerIsFixing[playerId] = False
        self.playerNearSite[playerId] = False
        self.pts[playerId] = 0
        self.kd[playerId] = None

        if self.status == 0:
            self.waiting.append(playerId)
            self.setPos(playerId, c.lobbyPos)
        elif self.status == 1:
            lobbyGameApi.TryToKickoutPlayer(playerId, "§eMatch already started")

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        if self.status == 0:
            self.waiting.pop(self.waiting.index(playerId))
        elif self.status == 1:
            pass


        self.playerEquips.pop(playerId)
        self.playerIsFixing.pop(playerId)
        self.playerNearSite.pop(playerId)
        self.pts.pop(playerId)
        self.kd.pop(playerId)

        if playerId in self.alive:
            self.alive.pop(playerId)
        if playerId in self.rff:
            self.rff.pop(playerId)

    def tick(self):
        count = len(serverApi.GetPlayerList())

        if self.status == 0:
            print 'countdown=%s' % self.countdown
            enough = c.enoughPlayers
            if count < c.startCountdown:
                pass
            elif c.startCountdown <= count <= enough:
                self.countdown -= 1
            if count == enough and self.countdown > 15:
                self.countdown = 15
            if self.countdown < 60 and count < c.startCountdown:
                self.countdown = 60

                def a():
                    self.updateServerStatus(0, True)
                    rebootSystem = serverApi.GetSystem('reboot', 'rebootSystem')
                    rebootSystem.DoReboot(False)

                commonNetgameApi.AddTimer(2.0, a)
                self.sendMsgToAll("§c§l人数不够，战局取消。保留所有物品。")

            if self.countdown == 0:
                print 'starting!'
                self.start()
                self.status = 1

        if self.status == 1:
            self.timer += 1

            pass

        self.updateServerStatus(self.status)

    def start(self):
        pass