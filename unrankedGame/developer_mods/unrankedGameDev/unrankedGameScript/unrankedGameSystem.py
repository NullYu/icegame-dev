# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import json
import apolloCommon.commonNetgameApi as commonNetgameApi
import lobbyGame.netgameApi as lobbyGameApi
import unrankedGameScript.timemngr as timemngr
players = 0
warmup = 1
canhit = {}

mmode = ''

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()


# 在modMain中注册的Server System类
class unrankedGameSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()
        self.gameTime = -5
        self.peace = False

        self.mode = None
        self.matchId = None
        self.p1 = None
        self.p2 = None

        self.mTimer = None

    ##############UTILS##############

    def Reset(self):
        self.gameTime = -30
        self.peace = False

        self.mode = None
        self.matchId = None
        self.p1 = None
        self.p2 = None


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

    def broadcastMsg(self, msg):
        for player in serverApi.GetPlayerList():
            comp = serverApi.GetEngineCompFactory().CreateMsg(player)
            comp.NotifyOneMessage(player, msg, "§f")

    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent",
                            self,
                            self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent",
                            self,
                            self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerDieEvent",
                            self,
                            self.OnPlayerDie)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerAttackEntityEvent",
                            self,
                            self.OnPlayerAttackEntity)
        self.ListenForEvent('unrankedService', 'unrankedService', 'ServiceStartOk', self, self.OnServiceStartOk)

        def a():
            args = {
                'sid': lobbyGameApi.GetServerId()
            }
            serverId = lobbyGameApi.GetServerId()
            def Cb(a, b):
                print 'ResponseFromServer module=matchmaking event=RecordSidEvent a='+str(a)+' b='+str(b)
            self.RequestToService("matchmaking", "RecordSidEvent", args, Cb)
            print 'ListenEvents/RequestToService module=matchmaking event=RecordSidEvent serverId='+str(serverId)
        commonNetgameApi.AddTimer(3.0, a)
        
        def b():
            self.tick()
        self.mTickTimer = commonNetgameApi.AddRepeatedTimer(1.0, b)
        
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnScriptTickServer",
                            self,
                            self.OnScriptTickServer)
        gameComp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        gameComp.SetCanBlockSetOnFireByLightning(False)
        gameComp.SetCanActorSetOnFireByLightning(False)

    def OnScriptTickServer(self):
        for player in serverApi.GetPlayerList():
            comp = serverApi.GetEngineCompFactory().CreateName(player)
            comp.SetPlayerPrefixAndSuffixName("", serverApi.GenerateColor('RED'), '§l§cHP %s' % int(serverApi.GetEngineCompFactory().CreateAttr(player).GetAttrValue(serverApi.GetMinecraftEnum().AttrType.HEALTH)),
                                              serverApi.GenerateColor('RED'))

    def OnPlayerAttackEntity(self, data):
        playerId = data['playerId']
        itemComp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        item = itemComp.GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0)
        if playerId not in canhit:
            canhit[playerId] = 1
        if self.gameTime < 0 or (not canhit[playerId]) or self.peace:
            data['cancel'] = True
            print 'OnPlayerAttackEntity self.gameTime='+str(self.gameTime)+' warmup='+str(warmup)
            return
        victimId = data['victimId']
        if self.mode == "totem" and item['itemName'] == 'minecraft:diamond_sword':
            self.sendCmd("/clear @s diamond_sword", playerId)
            def a():
                comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
                comp.SpawnItemToPlayerInv({
                    'itemName': 'minecraft:diamond_sword',
                    'count': 1,
                    'auxValue': 0,
                    'enchantData': [(9, 5), (17, 3)],
                    'extraId': 'legal32k'
                }, playerId, 0)
                canhit[playerId] = 1


            if item['itemName'] == 'minecraft:diamond_sword':
                comp = serverApi.GetEngineCompFactory().CreateHurt(victimId)
                comp.Hurt(20, serverApi.GetMinecraftEnum().ActorDamageCause.EntityAttack, playerId, None, False)
                self.sendTitle("§l§6等待重发", 3, playerId)
                canhit[playerId] = 0
                commonNetgameApi.AddTimer(1.5, a)
            else:
                data['cancel'] = True
        if self.mode == 'sumo':
            data['damage'] = 0

    def OnAddServerPlayer(self, data):
        p = data['id']

        def a(playerId):
            utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
            if len(serverApi.GetPlayerList()) > 2 and playerId not in utilsSystem.spectating:
                msg = 'Server closed: §cNo synapse server'
                lobbyGameApi.TryToKickoutPlayer(playerId, msg)

                for player in serverApi.GetPlayerList():
                    lobbyGameApi.TryToKickoutPlayer(player, '§eServer restarting')

                rebootSystem = serverApi.GetSystem('reboot', 'rebootSystem')
                rebootSystem.DoReboot()
        commonNetgameApi.AddTimer(0.1, a, p)

    def OnDelServerPlayer(self, data):
        online = serverApi.GetPlayerList()
        player = data['id']
        if online:
            playerId = online[0]
        comp = serverApi.GetEngineCompFactory().CreateCommand(serverApi.GetLevelId())

        if lobbyGameApi.GetOnlinePlayerNum() > 1:
            comp.SetCommand("/summon fireworks_rocket")

            def c():
                pass
            self.peace = True
            self.sendTitle("§6§l胜利", 1, playerId)
            self.sendMsg("§3您赢得了比赛。正在结算，稍后将您传送回主城...", playerId)

            args = {
                "winner": lobbyGameApi.GetPlayerUid(self.p2),
                "loser": lobbyGameApi.GetPlayerUid(self.p1),
                "nickname": lobbyGameApi.GetPlayerNickname(self.p2),
                "matchId": self.matchId
            }
            self.RequestToService("matchmaking", "GameEndByDisconnectionEvent", args)

            def d():
                rebootSystem = serverApi.GetSystem('reboot', 'rebootSystem')
                rebootSystem.DoReboot()
            commonNetgameApi.AddTimer(5.0, d)

        else:
            self.RequestToService("matchmaking", "ForceReset", 0)
            self.Reset()
            rebootSystem = serverApi.GetSystem('reboot', 'rebootSystem')
            rebootSystem.DoReboot()


    def OnServiceStartOk(self, args):

        self.peace = True
        self.gameTime = -30
        self.startGameArgs = args
        self.mode = args['mode']

        print 'CALL OnServiceStartOk args='+str(args)

        self.Reset()
        self.gameTime = -30

    def tick(self):

        if self.p1 and self.p2:
            utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
            utilsSystem.TextBoard(self.p1, True, """
§e§lICE§a_§bGAME§r§l -> §3Duels§r[%s]§r

§3您: §b%s HP
§3%s: §b%s HP

§3使用/kill重开

""" % (self.mode,
           serverApi.GetEngineCompFactory().CreateAttr(self.p1).GetAttrValue(
               serverApi.GetMinecraftEnum().AttrType.HEALTH),
       lobbyGameApi.GetPlayerNickname(self.p2),
       serverApi.GetEngineCompFactory().CreateAttr(self.p2).GetAttrValue(
           serverApi.GetMinecraftEnum().AttrType.HEALTH)
       ))

            utilsSystem.TextBoard(self.p2, True, """
§e§lICE§a_§bGAME§r§l -> §3Duels§r[%s]§r

§3您: §b%s HP
§3%s: §b%s HP

§3使用/kill重开

""" % (self.mode,
                   serverApi.GetEngineCompFactory().CreateAttr(self.p2).GetAttrValue(
                       serverApi.GetMinecraftEnum().AttrType.HEALTH),
                   lobbyGameApi.GetPlayerNickname(self.p1),
                   serverApi.GetEngineCompFactory().CreateAttr(self.p1).GetAttrValue(
                       serverApi.GetMinecraftEnum().AttrType.HEALTH)
                   ))

        print 'tick p1=%s p2=%s peac=%s mode=%s ticktimer=%s timer=%s gametime=%s args=%s' % (self.p1, self.p2, self.peace, self.mode, self.mTickTimer, self.mTimer, self.gameTime, self.startGameArgs)
        if len(serverApi.GetPlayerList()) > 0 and self.gameTime < 0:
            self.gameTime += 1
            for player in serverApi.GetPlayerList():
                utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
                utilsSystem.SetPlayerSpectate(player, False)
                self.sendTitle("§l§e热身时间%s秒" % (-self.gameTime,), 3, player)
                self.sendCmd("/effect @s instant_health 1 255 true", player)
                self.sendCmd("/effect @s invisibility 2 2 true", player)
                comp = serverApi.GetEngineCompFactory().CreateItem(player)
                for i in range(36):
                    comp.SpawnItemToPlayerInv({
                        "itemName": "minecraft:iron_sword",
                        "count": 0,
                        "auxValue": 0,
                        "customTips": "§l§3休闲模式匹配",
                        "extraId": "solo_unranked"
                    }, player, i)
                comp.SpawnItemToArmor({
                    'itemName': 'minecraft:diamond_helmet',
                    'count': 0,
                    'auxValue': 0
                }, player, serverApi.GetMinecraftEnum().ArmorSlotType.HEAD)
                comp.SpawnItemToArmor({
                    'itemName': 'minecraft:diamond_chestplate',
                    'count': 0,
                    'auxValue': 0
                }, player, serverApi.GetMinecraftEnum().ArmorSlotType.BODY)
                comp.SpawnItemToArmor({
                    'itemName': 'minecraft:diamond_leggings',
                    'count': 0,
                    'auxValue': 0
                }, player, serverApi.GetMinecraftEnum().ArmorSlotType.LEG)
                comp.SpawnItemToArmor({
                    'itemName': 'minecraft:diamond_boots',
                    'count': 0,
                    'auxValue': 0
                }, player, serverApi.GetMinecraftEnum().ArmorSlotType.FOOT)
            if self.gameTime == 0:
                self.OnStartgame(self.startGameArgs)
                self.startGameArgs = None
                self.peace = False

    def OnStartgame(self, args):

        if len(serverApi.GetPlayerList()) < 2:
            def a():
                rebootSystem = serverApi.GetSystem('reboot', 'rebootSystem')
                rebootSystem.DoReboot()
            commonNetgameApi.AddTimer(2.0, a)
            self.sendMsg('§6您的对手逃逸了。正在将您传送回主城', serverApi.GetPlayerList()[0])
            self.Reset()
            return

        warmup = 0
        print 'CALL OnStartGame args='+str(args)
        startOK = 0
        self.p1 = serverApi.GetPlayerList()[0]
        self.p2 = serverApi.GetPlayerList()[1]

        self.mode = args["mode"]
        if 'matchId' in args:
            self.matchId = args["matchId"]
        else:
            self.matchId = 0

        for player in serverApi.GetPlayerList():
            comp = serverApi.GetEngineCompFactory().CreateGame(player)
            comp.SetHurtCD(10)
            if self.mode == 'combo':
                comp.SetHurtCD(0)

        if self.mode == 'sumo':
            comp = serverApi.GetEngineCompFactory().CreatePos(self.p1)
            comp.SetFootPos((4, 201, -4))
            comp = serverApi.GetEngineCompFactory().CreatePos(self.p2)
            comp.SetFootPos((-4, 201, 4))
        else:
            comp = serverApi.GetEngineCompFactory().CreatePos(self.p1)
            comp.SetFootPos((45, 201, 0))
            comp = serverApi.GetEngineCompFactory().CreatePos(self.p2)
            comp.SetFootPos((-45, 201, 0))

        self.sendCmd("/effect @a clear", self.p1)

        self.giveKit(self.mode, self.p1)
        self.giveKit(self.mode, self.p2)

        self.broadcastMsg("比赛"+str(self.matchId)+"（休闲模式）即将开始！请做好准备！")

        self.broadcastMsg("§e比赛开始")

        self.sendCmd("/playsound note.harp", self.p1)
        self.sendCmd("/playsound note.harp", self.p2)

        def c():
            self.broadcastMsg("我们不建议您使用§l§c蝴蝶点§r。如果您因为该原因被封禁，活该")
        commonNetgameApi.AddTimer(5.0, c)



    def OnPlayerDie(self, data):
        comp = serverApi.GetEngineCompFactory().CreateCommand(serverApi.GetLevelId())
        playerId = data['id']
        attackerId = data['attacker']

        self.peace = True
        comp.SetCommand("/summon lightning_bolt", playerId)
        self.sendCmd("/clear @a", playerId)
        if attackerId:
            comp.SetCommand("/summon fireworks_rocket", attackerId)
        def c():
            pass

        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        if attackerId:
            utilsSystem.ShowWinBanner(attackerId)
        else:
            mPlayerList = [self.p1, self.p2]
            mPlayerList.pop(mPlayerList.index(playerId))
            utilsSystem.ShowWinBanner(mPlayerList[0])

        utilsSystem.SetPlayerSpectate(playerId, True)

        if playerId == self.p1:
            self.sendMsg("§3您输掉了比赛，不要气馁，再接再厉！正在结算，稍后将您传送回主城...", self.p1)
            self.sendMsg("§3您赢得了比赛。正在结算，稍后将您传送回主城...", self.p2)

            args = {
                "winner": lobbyGameApi.GetPlayerUid(self.p2),
                "loser": lobbyGameApi.GetPlayerUid(self.p1),
                "nickname": lobbyGameApi.GetPlayerNickname(self.p2),
                "matchId": self.matchId
            }
            self.RequestToService("matchmaking", "GameEndByKillEvent", args)
        elif playerId == self.p2:
            self.sendMsg("§3您输掉了比赛，不要气馁，再接再厉！正在结算，稍后将您传送回主城...", self.p2)
            self.sendMsg("§3您赢得了比赛。正在结算，稍后将您传送回主城...", self.p1)

            args = {
                "winner": lobbyGameApi.GetPlayerUid(self.p1),
                "loser": lobbyGameApi.GetPlayerUid(self.p2),
                "nickname": lobbyGameApi.GetPlayerNickname(self.p1),
                "matchId": self.matchId
            }
            self.RequestToService("matchmaking", "GameEndByKillEvent", args)


        def d():
            self.Reset()
            rebootSystem = serverApi.GetSystem('reboot', 'rebootSystem')
            rebootSystem.DoReboot()

        commonNetgameApi.AddTimer(12.0, d)

    def sendToLobby(self, p1, p2=None):
        transData = {'position': [107, 188, 105]}
        lobbyGameApi.TransferToOtherServer(p1, 'lobby', json.dumps(transData))
        if p2:
            lobbyGameApi.TransferToOtherServer(p2, 'lobby', json.dumps(transData))

        self.gameTime = 0

    def giveKit(self, mode, playerId):
        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        for i in range(36):
            comp.SpawnItemToPlayerInv({
                "itemName": "minecraft:iron_sword",
                "count": 0,
                "auxValue": 0,
                "customTips": "§l§3休闲模式匹配",
                "extraId": "solo_unranked"
            }, playerId, i)
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
        print 'CALL giveKit self.mode='+mode+' playerId='+str(playerId)
        if mode == "s2p2":
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:diamond_sword',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(9, 2), (13, 2), (17, 3)]
            }, playerId, 0)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:ender_pearl',
                'count': 16,
                'auxValue': 0
            }, playerId, 1)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:potion',
                'count': 1,
                'auxValue': 15
            }, playerId, 2)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:potion',
                'count': 1,
                'auxValue': 13
            }, playerId, 3)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:golden_apple',
                'count': 64,
                'auxValue': 0
            }, playerId, 4)
            for i in range(32):
                comp.SpawnItemToPlayerInv({
                    'itemName': 'minecraft:splash_potion',
                    'count': 1,
                    'auxValue': 22
                }, playerId, i + 5)
            comp.SpawnItemToArmor({
                'itemName': 'minecraft:diamond_helmet',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(0, 3), (17, 3)]
            }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.HEAD)
            comp.SpawnItemToArmor({
                'itemName': 'minecraft:diamond_chestplate',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(0, 3), (17, 3)]
            }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.BODY)
            comp.SpawnItemToArmor({
                'itemName': 'minecraft:diamond_leggings',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(0, 3), (17, 3)]
            }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.LEG)
            comp.SpawnItemToArmor({
                'itemName': 'minecraft:diamond_boots',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(0, 3), (17, 3)]
            }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.FOOT)

        elif mode == "totem":
            self.sendMsg("§l§a小提示：§r图腾不光可以放在副手，也可以放在物品栏中使用！", self.p1)
            self.sendMsg("§l§a小提示：§r图腾不光可以放在副手，也可以放在物品栏中使用！", self.p2)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:diamond_sword',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(9, 5), (17, 3)]
            }, playerId, 0)
            for i in range(35):
                comp.SpawnItemToPlayerInv({
                    'itemName': 'minecraft:totem',
                    'count': 1,
                    'auxValue': 0
                }, playerId, i+1)

        elif mode == "combo":
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:iron_sword',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(9, 1), (13, 2), (17, 3)]
            }, playerId, 0)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:ender_pearl',
                'count': 16,
                'auxValue': 0
            }, playerId, 1)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:potion',
                'count': 1,
                'auxValue': 15
            }, playerId, 2)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:potion',
                'count': 1,
                'auxValue': 13
            }, playerId, 3)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:golden_apple',
                'count': 64,
                'auxValue': 0
            }, playerId, 4)
            for i in range(32):
                comp.SpawnItemToPlayerInv({
                    'itemName': 'minecraft:splash_potion',
                    'count': 1,
                    'auxValue': 22
                }, playerId, i + 5)
            comp.SpawnItemToArmor({
                'itemName': 'minecraft:diamond_helmet',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(0, 3), (17, 3)]
            }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.HEAD)
            comp.SpawnItemToArmor({
                'itemName': 'minecraft:diamond_chestplate',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(0, 3), (17, 3)]
            }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.BODY)
            comp.SpawnItemToArmor({
                'itemName': 'minecraft:diamond_leggings',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(0, 3), (17, 3)]
            }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.LEG)
            comp.SpawnItemToArmor({
                'itemName': 'minecraft:diamond_boots',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(0, 3), (17, 3)]
            }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.FOOT)
        elif mode == "nor":
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:iron_sword',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(9, 2),(17, 3)]
            }, playerId, 0)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:cooked_beef',
                'count': 64,
                'auxValue': 0
            }, playerId, 1)
            comp.SpawnItemToArmor({
                'itemName': 'minecraft:iron_helmet',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(0, 3), (17, 3)]
            }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.HEAD)
            comp.SpawnItemToArmor({
                'itemName': 'minecraft:iron_chestplate',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(0, 3), (17, 3)]
            }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.BODY)
            comp.SpawnItemToArmor({
                'itemName': 'minecraft:iron_leggings',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(0, 3), (17, 3)]
            }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.LEG)
            comp.SpawnItemToArmor({
                'itemName': 'minecraft:iron_boots',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(0, 3), (17, 3)]
            }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.FOOT)
        elif mode == "archer":
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:bow',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(17, 3)]
            }, playerId, 0)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:arrow',
                'count': 64,
                'auxValue': 0
            }, playerId, 1)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:arrow',
                'count': 64,
                'auxValue': 0
            }, playerId, 2)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:arrow',
                'count': 64,
                'auxValue': 0
            }, playerId, 3)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:golden_apple',
                'count': 8,
                'auxValue': 0
            }, playerId, 4)

            comp.SpawnItemToArmor({
                'itemName': 'minecraft:chainmail_helmet',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(0, 3), (17, 3)]
            }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.HEAD)
            comp.SpawnItemToArmor({
                'itemName': 'minecraft:chainmail_chestplate',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(0, 3), (17, 3)]
            }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.BODY)
            comp.SpawnItemToArmor({
                'itemName': 'minecraft:chainmail_leggings',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(0, 3), (17, 3)]
            }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.LEG)
            comp.SpawnItemToArmor({
                'itemName': 'minecraft:chainmail_boots',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(0, 3), (17, 3)]
            }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.FOOT)