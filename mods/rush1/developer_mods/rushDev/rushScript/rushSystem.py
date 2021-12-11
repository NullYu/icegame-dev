# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import random
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.commonNetgameApi as commonNetgameApi
import apolloCommon.mysqlPool as mysqlPool

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()
ecoSystem = serverApi.GetSystem("eco", "ecoSystem")

initScoreboard = False

queue = []
playing = []

p1 = []
p2 = []

blocks = []
scoreboard = {}

# 在modMain中注册的Server System类
class rushServerSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()
        lobbyGameApi.ShieldPlayerJoinText(True)

        self.p1 = 0
        self.p2 = 0

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

    def RedoBeds(self, p1=None, p2=None, teleport=True):
        self.sendCmd("/setblock 0 181 25 cake", serverApi.GetPlayerList()[0])
        self.sendCmd("/setblock 0 181 -25 cake", serverApi.GetPlayerList()[0])
        if p1 and p2 and teleport:
            self.sendCmd('/tp 0 185 25', p1)
            self.sendCmd('/tp 0 185 -25', p2)

    def GiveKit(self, p1, p2):
        for player in playing:
            comp = serverApi.GetEngineCompFactory().CreateItem(player)
            self.sendCmd('/clear', player)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:wooden_sword',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(12, 2), (17, 3)]
            }, player, 0)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:sandstone',
                'count': 64,
                'auxValue': 0
            }, player, 1)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:diamond_pickaxe',
                'count': 1,
                'auxValue': 0
            }, player, 2)
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
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerDieEvent",
                            self,
                            self.OnPlayerDie)


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

        commonNetgameApi.AddRepeatedTimer(10.0, self.NotifyPositionInQueue)


    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("gameutils", "gameutilsClient", 'TestRequest', self, self.OnTestRequest)

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        uid = data['uid']
        if playerId in queue:
            queue.pop(queue.index(playerId))
        if playerId in playing:
            self.EndGame(True, playing[0])

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        self.sendCmd("/clear", playerId)
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        comp.SetFootPos((0, 201, 0))
        self.sendCmd('/clear', playerId)
        serverId = lobbyGameApi.GetServerId()
        if not initScoreboard:
            print '=====initScoreboard====='
            self.sendCmd("/gamerule sendcommandfeedback false", playerId)
            self.sendCmd("/scoreboard objectives add main dummy §b§lRUSH", playerId)
            self.sendCmd("/scoreboard players reset * main", playerId)
            self.sendCmd("/scoreboard players set test_item -1 main", playerId)
            self.sendCmd("/scoreboard objectives setdisplay sidebar main ascending", playerId)
            self.scoreboard(1, 1, "§3游戏中：")
            self.scoreboard(1, 4, '""')
            self.scoreboard(1, 6, "踩在钻石块上跳一下以进入队伍")
            self.scoreboard(1, 7, '""')
            self.scoreboard(1, 8, "§7ICE-RUSH-%s" % (serverId,))
            initScoreboard = True
            global initScoreboard
        else:
            print 'scorboard already init'

        comp = serverApi.GetEngineCompFactory().CreateGame(playerId)
        comp.SetDisableHunger(True)
        comp = serverApi.GetEngineCompFactory().CreateGame(playerId)
        comp.SetDisableDropItem(True)

    def EndGame(self, disconnect, winner=None, loser=None):
        print 'CALL EndGame disconnect=%s winner=%s loser=%s' % (disconnect, winner, loser)

        neteaseRankSystem = serverApi.GetSystem("neteaseRank", "neteaseRankDev")
        playing.pop(0)
        playing.pop(0)
        for block in blocks:
            blockDict = {
                'name': 'minecraft:air',
                'aux': 0
            }
            comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
            comp.SetBlockNew(block, blockDict, 0, 0)
        self.sendCmd('/clear @a', winner)

        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        utilsSystem.ShowWinBanner(winner)

        if disconnect:
            self.RedoBeds(serverApi.GetPlayerList()[0], serverApi.GetPlayerList()[0], False)
        if loser:
            self.sendMsgToAll("§3%s 获得胜利，奖励§e4 NEKO§3。对比赛有异议？使用/r举报玩家！" % (lobbyGameApi.GetPlayerNickname(winner),))
            uid = lobbyGameApi.GetPlayerUid(winner)
            response = ecoSystem.GivePlayerEco(uid, 4, 'rush win', False)

            self.RedoBeds(winner, loser, False)
            comp = serverApi.GetEngineCompFactory().CreatePos(winner)
            comp.SetFootPos((0, 201, 0))
            comp = serverApi.GetEngineCompFactory().CreatePos(loser)
            comp.SetFootPos((0, 201, 0))
            self.sendCmd('/clear @a', winner)
            self.sendCmd('/effect @a instant_health 1 255 true', winner)
            self.sendCmd('/scoreboard players reset * main', winner)

            self.scoreboard(1, 1, "§3游戏中：")
            self.scoreboard(1, 4, '""')
            self.scoreboard(1, 6, "踩在钻石块上跳一下以进入队伍")
            self.scoreboard(1, 7, '""')
            self.scoreboard(1, 8, "§7ICE-RUSH-%s" % (lobbyGameApi.GetServerId(),))

            self.sendMsg("§6§l玩腻了？§f点击回城按钮返回主城。（所有小游戏都不会自动回城，请使用右上方的回城按钮。）", winner)
            self.sendMsg("§6§l玩腻了？§f点击回城按钮返回主城。（所有小游戏都不会自动回城，请使用右上方的回城按钮。）", loser)

            if not disconnect:
                sql = 'INSERT INTO rush (p1, p2, winner, time) VALUES (%s, %s, %s, %s);'
                mysqlPool.AsyncExecuteWithOrderKey('EndGame/RecordGame', sql, (winner, loser, winner, time.time()))
                # neteaseRankSystem.OutCommitRankData(winner, )
            else:
                sql = 'INSERT INTO rush (p1, p2, winner, time, byDisconnection) VALUES (%s, %s, %s, %s, 1);'
                mysqlPool.AsyncExecuteWithOrderKey('EndGame/RecordGame', sql, (winner, loser, winner, time.time()))

            global p1, p2
            p1 = []
            p2 = []
            self.p1 = None
            self.p2 = None

    def OnDestroyBlock(self, data):
        pos = (data['x'], data['y'], data['z'])
        playerId = data['playerId']
        name = data['fullName']
        aux = data['auxData']
        blockDict = {
            'name': name,
            'aux': aux
        }

        if playerId not in playing:
            comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId)
            comp.SetBlockNew(pos, blockDict, 0, 0)
            print 'player tried to break map! player glitched playerId=', str(playerId)
            return

        if name not in ['minecraft:sandstone', 'minecraft:cake']:
            comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId)
            comp.SetBlockNew(pos, blockDict, 0, 0)
            print 'player tried to break map! playerId=%s name=%s' % (playerId, name)
            return
        if name == 'minecraft:cake' and (pos == (0, 181, -25)):
            # player 1 win
            print 'player 1 win playerid=%s' % (p1,)
            if playerId == self.p2:
                self.sendTitle("§l§c警告", 1, playerId)
                self.sendTitle("不要破坏自己的床！", 2, playerId)
            p1[1] += 1
            for player in serverApi.GetPlayerList():
                self.sendCmd('/playsound random.levelup', self.p1)
            if p1[1] >= 3:
                self.EndGame(False, self.p1, self.p2)
            self.scoreboard(1, 2,  '"%s: §l§3%s"' % (lobbyGameApi.GetPlayerNickname(self.p1), p1[1]))
            self.RedoBeds(self.p1, self.p2, True)
        elif name == 'minecraft:cake' and (pos == (0, 181, 25)):
            # player 2 win
            print 'player 1 win playerid=%s' % (p1,)
            if playerId == self.p1:
                self.sendTitle("§l§c警告", 1, playerId)
                self.sendTitle("不要破坏自己的床！", 2, playerId)
            print 'p2=%s' % (p2,)
            p2[1] += 1
            for player in serverApi.GetPlayerList():
                self.sendTitle("§a§l%s得分!" % (self.p2,), 3, player)
            self.sendCmd('/playsound random.levelup', self.p2)
            if p2[1] >= 3:
                self.EndGame(False, self.p2, self.p1)
            self.scoreboard(1, 3, '"%s: §l§3%s"' % (lobbyGameApi.GetPlayerNickname(self.p2), p2[1]))
            self.RedoBeds(self.p1, self.p2, True)

    def OnPlayerDie(self, args):
        playerId = args['id']
        attackerId = args['attacker']

        if playerId in playing:
            self.GiveKit(playerId, attackerId)

    def PlayerFell(self, playerId):

        if playerId == self.p1:
            self.sendCmd('/tp 0 185 25', playerId)
        else:
            self.sendCmd('/tp 0 185 -25', playerId)

    def OnServerEntityTryPlaceBlock(self, data):
        x = data['x']
        y = data['y']
        z = data['z']
        playerId = data['entityId']

        if y >= 200 or y < 165 or abs(z)>30 or abs(x)>10:
            data['cancel'] = True
            self.sendTitle("§l§c这里不能放方块哦", 3, playerId)
        else:
            blocks.append((x, y, z))

    def OnActuallyHurtServer(self, data):
        playerId = data['entityId']
        data['damage'] = 0
    def NotifyPositionInQueue(self):
        for player in serverApi.GetPlayerList():
            if player in queue:
                self.sendMsg("§6您在队伍中的位置：§l%s" % ((queue.index(player)+1)), player)

    def StartMatch(self, mp1, mp2):
        queue.pop(queue.index((mp1)))
        queue.pop(queue.index((mp2)))
        p1 = [mp1, 0]
        p2 = [mp2, 0]
        global p1, p2
        playing.append(mp1)
        playing.append(mp2)

        self.p1 = p1[0]
        self.p2 = p2[0]

        print 'p1List=%s p2list=%s' % (p1, p2)

        p1Name = lobbyGameApi.GetPlayerNickname(self.p1)
        p2Name = lobbyGameApi.GetPlayerNickname(self.p2)
        self.sendMsgToAll("§3一轮新的游戏即将开始！\n§f%s §bVS §f%s"% (p1Name, p2Name))

        self.RedoBeds()
        for block in blocks:
            blockDict = {
                'name': 'minecraft:air',
                'aux': 0
            }
            comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
            comp.SetBlockNew(block, blockDict, 0, 0)

        resComp = self.CreateComponent(self.p1, "Minecraft", "player")
        resComp.SetPlayerRespawnPos((0, 185, 25))
        resComp = self.CreateComponent(self.p2, "Minecraft", "player")
        resComp.SetPlayerRespawnPos((0, 185, -25))

        self.sendCmd('/tp 0 185 25', self.p1)
        self.sendCmd('/tp 0 185 -25', self.p2)

        self.GiveKit(self.p1, self.p2)

        self.scoreboard(1, 2, '"%s: §l§30"' % (lobbyGameApi.GetPlayerNickname(self.p1),))
        self.scoreboard(1, 3, '"%s: §l§30"' % (lobbyGameApi.GetPlayerNickname(self.p2),))

    def TryMatchmaking(self):
        if len(queue)>1 and len(playing) == 0:
            self.StartMatch(queue[0], queue[1])

        for player in serverApi.GetPlayerList():
            resComp = self.CreateComponent(player, "Minecraft", "player")
            resComp.SetPlayerRespawnPos((0, 201, 0))

    def OnScriptTickServer(self):
        self.scoreboard(1, 5, "§e%s§f人排队中" % (len(queue),))
        for player in serverApi.GetPlayerList():
            self.sendTitle(str(playing), 3, player)
            self.sendCmd("/kill @e[type=item]", player)
            comp = serverApi.GetEngineCompFactory().CreatePos(player)
            pos = comp.GetFootPos()
            if pos[1] >= 201:
                self.sendCmd("/effect @s weakness 1 255 true", player)
            elif pos[1] <= 175 and player in playing:
                self.PlayerFell(player)
            elif pos[1] <= 195 and not(player in playing):
                self.sendCmd("/tp 0 201 0", player)
            if not(player in queue) and abs(pos[0]) <= 1 and pos[1]>201 and abs(pos[2]) <= 1:
                queue.append(player)
                self.sendMsg("§6已开始排队", player)
                self.sendCmd("/playsound random.orb", player)
                self.TryMatchmaking()

            if playing:
                msg = "§l§b%s: §f%s%s%s%s  §f|  §g%s: §f%s%s%s%s" % (
                    lobbyGameApi.GetPlayerNickname(self.p1),
                    '⍉'*int(p1[1]==0),
                    '#'*int(p1[1]>0),
                    '#'*int(p1[1]>1),
                    '#'*int(p1[1]>2),
                    lobbyGameApi.GetPlayerNickname(self.p2),
                    '⍉'*int(p2[1]==0),
                    '#'*int(p2[1]>0),
                    '#'*int(p2[1]>1),
                    '#'*int(p2[1]>2)
                )
                self.sendTitle(msg, 3, player)