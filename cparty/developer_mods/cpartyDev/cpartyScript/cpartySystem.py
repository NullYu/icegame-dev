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

scoreboard = {}

# 在modMain中注册的Server System类
class cpartyServerSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()
        lobbyGameApi.ShieldPlayerJoinText(True)

        self.countdown = 0
        self.timer = 0
        self.interval = 10
        self.rounds = 0
        self.ticker = 0
        self.halftime = 0
        self.block = 0
        self.randomBlockGen = 0

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

    def sendCmdToAll(self, msg):
        for player in serverApi.GetPlayerList():
            self.sendCmd(msg, player)

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
        self.sendCmd("/fill 23 8 23 -23 8 -23 concrete", serverApi.GetPlayerList()[0])
        self.sendCmd("/fill 23 10 23 -23 10 -23 air", serverApi.GetPlayerList()[0])

    def InitArena(self):
        self.block = random.randint(0, 15)
        for width in range(-23, 24):
            for length in range(-23, 24):
                if random.randint(0, self.randomBlockGen) <= 2:
                    self.sendCmd('/setblock %s 8 %s concrete %s' % (width, length, random.randint(0, 15)), random.choice(self.playing))
                elif random.randint(0, 1) == 1:
                    self.sendCmd('/setblock %s 8 %s concrete %s' % (width, length, random.randint(0, self.block-1)),
                                 random.choice(self.playing))
                elif random.randint(0, 1) == 2:
                    self.sendCmd('/setblock %s 8 %s concrete %s' % (width, length, random.randint(self.block+1, 15)),
                                 random.choice(self.playing))
        self.sendCmd("/setblock %s 8 %s concrete %s" % (random.randint(-23, 23), random.randint(-23, 23), self.block), random.choice(self.playing))

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
        lobbyGameApi.ShieldPlayerJoinText(True)
        commonNetgameApi.AddRepeatedTimer(1.0, self.ClockTick)
        commonNetgameApi.AddRepeatedTimer(1.0, self.GameTick)


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
        comp = serverApi.GetEngineCompFactory().CreateGame(playerId)
        comp.SetDisableHunger(True)
        self.sendCmd("/clear", playerId)
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        comp.SetFootPos((0, 18, 0))
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
            self.sendCmd("/scoreboard objectives add main dummy §c§l色§e盲§a派§b对", playerId)
            self.sendCmd("/scoreboard players reset * main", playerId)
            self.sendCmd("/scoreboard players set test_item -1 main", playerId)
            self.sendCmd("/scoreboard objectives setdisplay sidebar main ascending", playerId)
            self.scoreboard(1, 1, "§3等待玩家中...")
            self.scoreboard(1, 4, '" "')
            self.scoreboard(1, 5, "§e将在倒计时结束后自动开始")
            self.scoreboard(1, 6, "§c180§f秒")
            self.scoreboard(1, 7, '""')
            self.scoreboard(1, 8, "§7ICE-CPARTY-%s" % (serverId,))
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
        data['cancel'] = True

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


        elif len(self.playing) == 1:
            player = self.playing[0]
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
                comp.SetFootPos((0, 18, 0))

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
        self.rounds = 1
        self.interval = 10
        self.ticker = -10
        self.halftime = 6
        self.block = 0
        self.playing = self.waiting
        self.waiting = []
        self.randomBlockGen = 4

        self.InitArena()

        print 'players list is now %s' % (self.playing,)
        for player in self.playing:
            comp = serverApi.GetEngineCompFactory().CreatePos(player)
            comp.SetFootPos((random.randint(-20, 20), 9, random.randint(-20, 20)))
            self.sendTitle("§c§l色§e盲§a派§b对", 1, player)
            self.sendTitle("除了手中颜色的方块，其他的都会消失！活下去！", 2, player)

        self.scoreboard(1, 1, '§e游戏进行中')
        self.scoreboard(1, 5, '请等待本场游戏结束')

    def GameTick(self):
        if len(self.playing) > 1:
            self.ticker += 1
            if self.rounds <= 5:
                self.halftime = int(math.ceil(self.interval/2))
            elif self.rounds <= 9:
                self.halftime = int(math.ceil(self.interval / 2+1))
            else:
                self.halftime = 1
            print 'haltime is now %s' % (self.halftime)

            if self.ticker < 0:
                self.sendCmdToAll('/xp -32767L')
                self.sendCmdToAll('/xp %sL' % (abs(self.ticker),))
                self.sendCmdToAll('/title @s actionbar §b方块还有§e%s§b秒消失' % (-(self.ticker),))
                if -self.ticker == self.halftime:
                    print '===HALF TIME! GIVE BLOCKS!'
                    for player in self.playing:
                        self.sendCmd('/give @s concrete 1 %s' % (self.block,), player)
            if self.ticker == 0:
                self.sendCmdToAll('/xp -32767L')
                self.sendCmdToAll('/title @s actionbar §6方块正在消失，小心！')
                self.sendCmdToAll('/playsound random.anvil_land')
                print 'random block is %s' % (self.block,)
                for i in range(16):
                    if not i == self.block:
                        print 'cleared block i=%s' % (i,)
                        self.sendCmd('/fill 23 8 23 -23 8 -23 air 0 replace concrete %s' % (i,), self.playing[0])
            if self.ticker > 6:
                self.InitArena()

                self.rounds += 1
                if self.rounds < 5:
                    self.interval -= 1
                self.ticker = -self.interval
                self.sendCmdToAll('/clear')
                self.sendCmdToAll('/title @s title §b§l第 §e%s §b局' % (self.rounds,))

                if self.rounds >= 10:
                    if self.rounds == 10:
                        self.sendCmdToAll('/title @s subtitle 即将开始随机生成障碍物')
                    for i in range(random.randint(3, 10)):
                        self.sendCmd("/setblock %s 10 %s stained_glass" % (random.randint(-23, 23), random.randint(-23, 23)), serverApi.GetPlayerList()[0])

    def Eliminate(self, playerId, disconnect=False):
        self.sendMsgToAll("§4%s§3被淘汰了！剩余§6%s§3名玩家" % (lobbyGameApi.GetPlayerNickname(playerId), len(self.playing)-1))

        if not disconnect:
            comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
            for i in range(36):
                comp.SpawnItemToPlayerInv({
                    'itemName': 'minecraft:dirt',
                    'count': 0
                }, playerId, i)
            comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
            comp.SetFootPos((0, 18, 0))
            self.sendTitle("§4§l您已被淘汰", 1, playerId)
            self.sendTitle("别气馁！阳光总在风雨后。", 2, playerId)

            self.waiting.append(playerId)
        self.playing.pop(self.playing.index(playerId))
        print 'ELIMINATION playerId=%s playing=%s' % (playerId, self.playing)

    def OnScriptTickServer(self):
        if len(self.playing) > 0:
            for player in self.playing:
                comp = serverApi.GetEngineCompFactory().CreatePos(player)
                pos = comp.GetFootPos()

                if pos[1] == 5 and len(self.playing) > 1:
                    self.Eliminate(player)

        for player in self.waiting:
            comp = serverApi.GetEngineCompFactory().CreatePos(player)
            pos = comp.GetPos()
            if 18 > pos[1] > 21:
                self.sendCmd("/tp @s ~ 18 ~", player)

        if serverApi.GetPlayerList():
            # self.sendCmd('/execute @e[type=armor_stand, name=reset] ~~~ fill 29 ~ 29 -29 ~ -29 air 0 replace water', serverApi.GetPlayerList()[0])
            # self.sendCmd('/execute @e[type=armor_stand, name=reset] ~~~ tp @s ~~1~', serverApi.GetPlayerList()[0])
            # self.sendCmd('/kill @e[type=armor_stand, name=reset, x=31, y=242, z=31, dx=0, dy=10, dz=0', serverApi.GetPlayerList()[0])
            pass
    def FastStart(self):
        if len(self.playing) == 0 and self.countdown > 15:
            self.countdown = 15