# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import math
import random
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.commonNetgameApi as commonNetgameApi
import apolloCommon.mysqlPool as mysqlPool

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

initScoreboard = False

blocks = []

scoreboard = {}

# 在modMain中注册的Server System类
class btsServerSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()
        lobbyGameApi.ShieldPlayerJoinText(True)

        self.countdown = 0
        self.timer = 0
        self.waterLevel = 0
        self.safe = []
        self.playing = []
        self.waiting = []

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

    def RedoArena(self):
        comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
        blockDict = {
            'name': 'minecraft:air',
            'aux': 0
        }
        for blockPos in blocks:
            comp.SetBlockNew(blockPos, blockDict, 0, 0)

        # for i in range(21, 238):
        #     self.sendCmd("/fill 29 %s 29 -29 %s -29 air 0" % (i, i),
        #                  serverApi.GetPlayerList()[0])
        for i in range(238):
            self.sendCmd("/fill 29 %s 29 -29 %s -29 air 0 replace water" % (i, i),
                         serverApi.GetPlayerList()[0])
            self.sendCmd("/fill 29 %s 29 -29 %s -29 air 0 replace flowing_water" % (i, i),
                         serverApi.GetPlayerList()[0])

    def GiveItems(self):
        for player in serverApi.GetPlayerList():
            self.sendCmd('/clear', player)
            for i in range(8):
                self.sendCmd("/replaceitem entity @s slot.hotbar %s concretepowder 64 %s" % (i, serverApi.GetPlayerList().index(player)), player)
    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnScriptTickServer", self,
                            self.OnScriptTickServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self,
                            self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent",
                            self,
                            self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerEntityTryPlaceBlockEvent",
                            self,
                            self.OnServerEntityTryPlaceBlock)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ActuallyHurtServerEvent",
                            self,
                            self.OnActuallyHurtServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DestroyBlockEvent",
                            self,
                            self.OnDestroyBlock)


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
                'mob_griefing': False,  # 生物破坏方块
                'keep_inventory': False,  # 保留物品栏
                'weather_cycle': False,  # 天气更替
                'mob_spawn': False,  # 生物生成
            }
        }
        comp.SetGameRulesInfoServer(ruleDict)
        comp.SetGameDifficulty(2)

        commonNetgameApi.AddRepeatedTimer(1.0, self.ClockTick)
        commonNetgameApi.AddRepeatedTimer(60.0, self.SnowballClock)


    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("gameutils", "gameutilsClient", 'TestRequest', self, self.OnTestRequest)

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        uid = data['uid']
        if playerId in self.waiting:
            self.waiting.pop(self.waiting.index(playerId))
        if playerId in self.playing:
            self.Eliminate(playerId, True)


    def OnAddServerPlayer(self, data):
        playerId = data['id']
        self.sendCmd("/clear", playerId)
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        comp.SetFootPos((0, 242, 0))
        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        for i in range(36):
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:dirt',
                'count': 0
            }, playerId, i)
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        serverId = lobbyGameApi.GetServerId()

        def a():
            if len(self.playing) == 0:
                self.sendMsg("§a您来的正是时候！请等待游戏开始。", playerId)
        commonNetgameApi.AddTimer(9.0, a)
        self.waiting.append(playerId)

        if not initScoreboard:
            print '=====initScoreboard====='
            self.sendCmd("/gamerule sendcommandfeedback false", playerId)
            self.sendCmd("/scoreboard objectives add main dummy §d§l爬塔§a求生", playerId)
            self.sendCmd("/scoreboard players reset * main", playerId)
            self.sendCmd("/scoreboard players set test_item -1 main", playerId)
            self.sendCmd("/scoreboard objectives setdisplay sidebar main ascending", playerId)
            self.scoreboard(1, 1, "§3等待玩家中...")
            self.scoreboard(1, 4, '" "')
            self.scoreboard(1, 5, "§e将在倒计时结束后自动开始")
            self.scoreboard(1, 6, "§c180§f秒")
            self.scoreboard(1, 7, '""')
            self.scoreboard(1, 8, "§7ICE-BTS-%s" % (serverId,))
            initScoreboard = True
            global initScoreboard
            self.sendCmd("/tickingarea add 50 0 50 -50 255 -50", playerId)
        else:
            print 'scorboard already init'


    def OnDestroyBlock(self, data):
        pos = (data['x'], data['y'], data['z'])
        playerId = data['playerId']
        name = data['fullName']
        aux = data['auxData']
        blockDict = {
            'name': name,
            'aux': aux
        }

        comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId)
        comp.SetBlockNew(pos, blockDict, 0, 0)

    def OnServerEntityTryPlaceBlock(self, data):
        x = data['x']
        y = data['y']
        z = data['z']
        playerId = data['entityId']

        blocks.append((x, y, z))

    def OnActuallyHurtServer(self, data):
        playerId = data['entityId']
        data['damage'] = 0

    def ClockTick(self):
        for player in self.waiting:
            self.sendCmd("/effect @s weakness 2 255 true", player)
        if len(self.playing) == 0:
            if len(self.waiting) > 1:
                if not self.countdown:
                    self.countdown = 180
                if self.countdown > 120 and len(self.waiting) >= 10:
                    self.countdown = 120
                    self.sendMsgToAll("§e游戏将在2分钟后开始！")
                elif self.countdown > 15 and len(self.waiting) >= 14:
                    self.countdown = 15
                    self.sendMsgToAll("§e游戏将在15秒后开始！")
                self.countdown -= 1
                self.scoreboard(1, 6, "§c%s§f秒" % (self.countdown,))

                if self.countdown <= 0:
                    self.scoreboard(1, 6, "§c0§f秒")
                    self.sendMsgToAll("§6一轮新的游戏即将开始！")
                    self.startgame()

            elif len(self.waiting) <= 1 and self.countdown < 180:
                self.sendMsgToAll("§c人数不够，倒计时被取消！")
                self.countdown = 180
                self.scoreboard(1, 6, "§c%s§f秒" % (self.countdown,))
        elif len(self.playing) > 1:
            self.timer += 1
            self.scoreboard(1, 2, '§b还剩§e%s§b名玩家' % (len(self.playing),))
            self.scoreboard(1, 6, '§b已进行§f%s§b秒' % (self.timer,))
            for player in self.playing:
                comp = serverApi.GetEngineCompFactory().CreatePos(player)
                self.sendTitle("§6§l水距离您§f%s§6格" % (math.floor(comp.GetPos()[1]-self.waterLevel),),3, player)
                if comp.GetPos()[1] >= 239 and player not in self.safe:
                    self.safe.append(player)
                    self.sendMsgToAll("§b一名玩家达到了安全区！")
                    self.sendTitle("§a您安全了", 1, player)
                    self.sendTitle("使用雪球淘汰其他玩家！", 2, player)
                    comp = serverApi.GetEngineCompFactory().CreateItem(player)
                    comp.SpawnItemToPlayerInv({
                        'itemName': 'minecraft:snowball',
                        'count': 16,
                        'auxValue': 0
                    }, player, 8)

            if self.timer >= 0 and self.waterLevel < 237:
                self.waterLevel += 1
                self.sendCmd("/fill 29 %s 29 -29 %s -29 water 0 replace air" % (self.waterLevel, self.waterLevel), serverApi.GetPlayerList()[0])

            if self.timer == 180:
                self.sendMsgToAll("§a§l游戏已进行了3分钟。§r即将开始为到达顶部安全区的玩家发放雪球！")\

        elif len(self.playing) == 1:
            player = self.playing[0]
            self.sendCmd("/summon armor_stand reset 31 5 31", player)
            self.sendTitle("§6§l胜利", 1, player)
            self.sendMsgToAll("§e%s§b获得胜利，奖励§a3NEKO" % (lobbyGameApi.GetPlayerNickname(player),))
            ecoSystem = serverApi.GetSystem("eco", "ecoSystem")
            ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(player), 3, 'bts win')
            self.sendCmd('/playsound firework.launch', player)
            self.playing = []
            self.waiting.append(player)
            self.RedoArena()
            comp = serverApi.GetEngineCompFactory().CreateItem(player)
            for i in range(36):
                comp.SpawnItemToPlayerInv({
                    'itemName': 'minecraft:dirt',
                    'count': 0
                }, player, i)

            def a():

                comp = serverApi.GetEngineCompFactory().CreatePos(player)
                comp.SetFootPos((0, 242, 0))

                self.scoreboard(1, 1, "§3等待玩家中...")
                self.scoreboard(2, 2)
                self.scoreboard(1, 5, "§e将在倒计时结束后自动开始")
                self.scoreboard(1, 6, "§c180§f秒")

                self.countdown = 180
            commonNetgameApi.AddTimer(5.0, a)


    def startgame(self):
        print '============GAME=====START========='
        self.countdown = 180
        self.timer = -5
        self.waterLevel = 5
        self.playing = self.waiting
        self.waiting = []

        print 'players list is now %s' % (self.playing,)
        for player in self.playing:
            comp = serverApi.GetEngineCompFactory().CreatePos(player)
            comp.SetFootPos((random.randint(5, 20), 21, random.randint(5, 20)))
            self.sendTitle("§c§l水位将在5秒后上涨", 1, player)
            self.sendTitle("努力向上搭，不要被水淹没！", 2, player)
            if player in self.safe:
                self.safe.pop(self.safe.index(player))

        self.scoreboard(1, 1, '§e游戏进行中')
        self.scoreboard(1, 5, '请等待本场游戏结束')
        self.GiveItems()

    def SnowballClock(self):
        if len(self.playing) > 0:
            for player in self.playing:
                if player in self.safe:
                    comp = serverApi.GetEngineCompFactory().CreateItem(player)
                    comp.SpawnItemToPlayerInv({
                        'itemName': 'minecraft:snowball',
                        'count': 16,
                        'auxValue': 0
                    }, player, 8)
                    self.sendMsg("§3已为您发放雪球。使用它淘汰其他玩家！", player)

    def Eliminate(self, playerId, disconnect=False):
        self.sendMsgToAll("§4%s§3被水淹没了！剩余§6%s§3名玩家" % (lobbyGameApi.GetPlayerNickname(playerId), len(self.playing)-1))

        if not disconnect:
            comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
            for i in range(36):
                comp.SpawnItemToPlayerInv({
                    'itemName': 'minecraft:dirt',
                    'count': 0
                }, playerId, i)
            comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
            comp.SetFootPos((0, 242, 0))
            self.sendTitle("§4§l您落水了", 1, playerId)
            self.sendTitle("别气馁！阳光总在风雨后。", 2, playerId)

            self.waiting.append(playerId)
        self.playing.pop(self.playing.index(playerId))
        print 'ELIMINATION playerId=%s playing=%s' % (playerId, self.playing)

    def OnScriptTickServer(self):
        if len(self.playing) > 0:
            for player in self.playing:
                comp = serverApi.GetEngineCompFactory().CreatePos(player)
                pos = comp.GetPos()
                comp = serverApi.GetEngineCompFactory().CreateBlockInfo(player)
                blockBelow = comp.GetBlockNew((pos[0], int(math.ceil(pos[1]-1)), pos[2]))
                blockBelow = blockBelow['name']

                if blockBelow == 'minecraft:water' and len(self.playing) > 1:
                    self.Eliminate(player)

        for player in self.waiting:
            comp = serverApi.GetEngineCompFactory().CreatePos(player)
            pos = comp.GetPos()
            if 242 > pos[1] > 100:
                self.sendCmd("/tp @s ~ 242 ~", player)

        if serverApi.GetPlayerList():
            # self.sendCmd('/execute @e[type=armor_stand, name=reset] ~~~ fill 29 ~ 29 -29 ~ -29 air 0 replace water', serverApi.GetPlayerList()[0])
            # self.sendCmd('/execute @e[type=armor_stand, name=reset] ~~~ tp @s ~~1~', serverApi.GetPlayerList()[0])
            # self.sendCmd('/kill @e[type=armor_stand, name=reset, x=31, y=242, z=31, dx=0, dy=10, dz=0', serverApi.GetPlayerList()[0])
            pass
    def FastStart(self):
        if len(self.playing) == 0 and self.countdown > 15:
            self.countdown = 15