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

# TODO debug add server type here
if False:
    pass
else:
    import tarkovScript.tarkovConsts.exampleMap as c

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
        
        self.timer = c.evacTime
        self.status = 0
        self.countdown = 60
        self.alive = {}

        self.uid = {}
        self.spawnChoiceIndex = 0

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self, self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self, self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DamageEvent", self, self.OnDamage)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerAttackEntityEvent", self, self.OnPlayerAttackEntity)

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
                'always_day': False,  # 终为白日
                'mob_griefing': True,  # 生物破坏方块
                'keep_inventory': False,  # 保留物品栏
                'weather_cycle': True,  # 天气更替
                'mob_spawn': True,  # 生物生成
            }
        }
        comp.SetGameRulesInfoServer(ruleDict)

        def a():
            self.updateServerStatus(self.status, True)
        commonNetgameApi.AddTimer(10.0, a)

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

    def OnClientAction(self, data):
        operation = data['operation']
        playerId = data['playerId']

        if operation == 'showEvacPoints':
            utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')

            msg = ''
            for name in c.evacPointNames:
                msg += '§f§l%s : --§r\n' % name
                utilsSystem.TextBoard(playerId, True, msg)

            def a(p):
                utilsSystem.TextBoard(p, False, '')
            commonNetgameApi.AddTimer(5.0, a, playerId)

    def SpawnPlayer(self, playerId):
        spawnPoses = c.spawnPos
        self.setPos(playerId, spawnPoses[self.spawnChoiceIndex])

        if self.spawnChoiceIndex > len(spawnPoses) - 1:
            self.spawnChoiceIndex = 0
        else:
            self.spawnChoiceIndex += 1

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
        self.uid[playerId] = lobbyGameApi.GetPlayerUid(playerId)
        self.alive[playerId] = True

        self.SpawnPlayer(playerId)

    def OnDelServerPlayer(self, data):
        playerId = data['id']

        self.uid.pop(playerId)

    def OnDamage(self, data):
        playerId = data['victimId']
        srcId = data['srcId']

        if self.status != 1:
            data['knock'] = False
            data['damage'] = 0
            return

        if not self.alive[playerId] or not self.alive[srcId]:
            data['knock'] = False
            data['damage'] = 0
            return

        cause = data['cause']

        if cause == 'fall':
            dmg = data['damage']

            if dmg >= 4.5:
                self.sendCmd('/kill', playerId)
            else:
                data['damage'] = 0

    def OnPlayerAttackEntity(self, data):
        playerId = data['playerId']
        victimId = data['victimId']

        if self.status != 1 or not self.alive[playerId] or not self.alive[victimId]:
            data['cancel'] = True

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
            self.timer -= 1

            for player in serverApi.GetPlayerList():
                self.NotifyToClient(player, 'UpdateEvacTimerEvent', self.timer)

        self.updateServerStatus(self.status)

    def start(self):
        for player in serverApi.GetPlayerList():
            self.NotifyToClient(player, 'StartDeployEvent', None)

        def a():
            self.status = 1
        commonNetgameApi.AddTimer(17.0, a)