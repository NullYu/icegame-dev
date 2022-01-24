# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import random
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.redisPool as redisPool
import apolloCommon.mysqlPool as mysqlPool
import datetime
import apolloCommon.commonNetgameApi as commonNetgameApi

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

# register global variables
equipStats = {}

# 在modMain中注册的Server System类
class ffaSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        self.antilog = {}

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnScriptTickServer", self,
                            self.OnScriptTickServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self,
                            self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self,
                            self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerDieEvent",
                            self,
                            self.OnPlayerDie)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerAttackEntityEvent",
                            self,
                            self.OnPlayerAttackEntity)
        commonNetgameApi.AddRepeatedTimer(1.0, self.tick)
        redisPool.InitDB(30)
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
        # print 'forceSelect called slot='+slot+' playerId='+playerId
        comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
        comp.ChangeSelectSlot(slot)

    def sendMsg(self, msg, playerId):
        comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
        comp.NotifyOneMessage(playerId, msg, "§f")

    def epoch2Datetime(self, epoch):
        ts = datetime.datetime.fromtimestamp(int(epoch)+0)
        return ts.strftime('%H:%M:%S')

    #################################

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("lobbyutils", "lobbyutilsClient", 'TestRequest', self, self.OnTestRequest)

    def tick(self):
        for player in serverApi.GetPlayerList():
            if player in self.antilog:
                self.sendTitle("§l§c您被攻击了，在%s秒内不要退出游戏！"%(int(self.antilog[player]-time.time())+1), 3, player)
                if self.antilog[player] < time.time():
                    self.antilog.pop(player)
                    self.sendTitle("§l§a您已离开战斗", 3, player)

    def OnPlayerDie(self, data):
        playerId = data['id']
        attackedId = data['attacker']
        equipStats[playerId] = 0
        self.giveMenu(playerId)

        if playerId in self.antilog:
            self.antilog[playerId] = 1

        sql = 'UPDATE ffa SET death=death+1 WHERE uid=%s;'
        mysqlPool.AsyncExecuteWithOrderKey('as89d6a0das8u', sql, (lobbyGameApi.GetPlayerUid(playerId),))
        if attackedId in serverApi.GetPlayerList():
            sql = 'UPDATE ffa SET kills=kills+1 WHERE uid=%s;'
            mysqlPool.AsyncExecuteWithOrderKey('as89d6a0das8u', sql, (lobbyGameApi.GetPlayerUid(attackedId),))


    def OnDelServerPlayer(self, data):
        playerId = data['id']

        menuSystem = serverApi.GetSystem('menu', 'menuSystem')
        uid = menuSystem.uids[playerId]

        if playerId in self.antilog:
            if self.antilog[playerId] > time.time():
                redisPool.AsyncSet('ffa-antilog-%s' % (uid,), time.time()+900)

    def OnPlayerAttackEntity(self, data):
        playerId = data['playerId']
        victimId = data['victimId']

        if not playerId in serverApi.GetPlayerList(): return
        if not equipStats[playerId]: return

        if victimId not in self.antilog:
            self.antilog[victimId] = time.time() + 15
        elif abs(self.antilog[victimId]-time.time())<14:
            self.antilog[victimId] += 1

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        uid = lobbyGameApi.GetPlayerUid(playerId)
        equipStats[playerId] = 0
        print 'OnAddServerPlayer playerId='+playerId+' equipStats='+str(equipStats)

        sql = 'SELECT * FROM ffa WHERE uid=%s;'

        def Cb(args):
            if not args:
                sql = 'INSERT INTO ffa (uid, nickname, kills, death) VALUES (%s, %s, 0, 0);'
                mysqlPool.AsyncExecuteWithOrderKey('czxcnfmam871927n0e', sql, (uid, lobbyGameApi.GetPlayerNickname(playerId)))

        mysqlPool.AsyncQueryWithOrderKey("asd7oabns6", sql, (uid,), Cb)

    def OnCallback(self, suc, args):
        playerId = args['playerId']
        if args['value'] == 'ok':
            # self.sendTitle("§l§c匹配已取消", 1, playerId)
            pass

    def giveKit(self, playerId):

        utils = serverApi.GetSystem('utils', 'utilsSystem')
        if utils and playerId in utils.spectating:
            return

        comp = serverApi.GetEngineCompFactory().CreateAction(playerId)
        comp.SetMobKnockback(0.1, 0.1, 0, 0, 1.0)
        menuSystem = serverApi.GetSystem('menu', 'menuSystem')
        menuSystem.OnCarriedNewItemChangedServer({
            'playerId': playerId,
            'newItemDict': {
                'extraId': 'exitqueue'
            },
            'noMenu': True
        })

        def a(player):
            comp = serverApi.GetEngineCompFactory().CreateItem(player)
            for i in range(35):
                comp.SetInvItemNum(i, 0)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:diamond_sword',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(9, 5), (17, 3)]
            }, player, 0)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:ender_pearl',
                'count': 16,
                'auxValue': 0
            }, player, 1)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:arrow',
                'count': 64,
                'auxValue': 0
            }, player, 2)
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:golden_apple',
                'count': 64,
                'auxValue': 0
            }, player, 3)
            for i in range(2):
                comp.SpawnItemToPlayerInv({
                    'itemName': 'minecraft:potion',
                    'count': 1,
                    'auxValue': 15
                }, player, i+4)
            for i in range(11):
                comp.SpawnItemToPlayerInv({
                    'itemName': 'minecraft:splash_potion',
                    'count': 1,
                    'auxValue': 22
                }, player, i+5)

            comp.SpawnItemToArmor({
                'itemName': 'minecraft:diamond_helmet',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(0, 1), (17, 3)]
            }, player, serverApi.GetMinecraftEnum().ArmorSlotType.HEAD)
            comp.SpawnItemToArmor({
                'itemName': 'minecraft:diamond_chestplate',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(0, 1), (17, 3)]
            }, player, serverApi.GetMinecraftEnum().ArmorSlotType.BODY)
            comp.SpawnItemToArmor({
                'itemName': 'minecraft:diamond_leggings',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(0, 1), (17, 3)]
            }, player, serverApi.GetMinecraftEnum().ArmorSlotType.LEG)
            comp.SpawnItemToArmor({
                'itemName': 'minecraft:diamond_boots',
                'count': 1,
                'auxValue': 0,
                'enchantData': [(0, 1), (17, 3)]
            }, player, serverApi.GetMinecraftEnum().ArmorSlotType.FOOT)
        commonNetgameApi.AddTimer(0.2, a, playerId)

    def giveMenu(self, playerId):
        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        print 'giveMenu called playerId='+playerId
        for i in range(35):
            comp.SetInvItemNum(i, 0)
        # 传送指令
        comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
        comp.ChangeSelectSlot(0)
        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        for i in range(28):
            comp.SpawnItemToPlayerInv({
                "itemName": "minecraft:iron_sword",
                "count": 0,
                "auxValue": 0,
                "customTips": "§l§3休闲模式匹配",
                "extraId": "solo_unranked"
            }, playerId, i + 9)
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
        comp.SpawnItemToPlayerInv({
            "itemName": "minecraft:iron_sword",
            "count": 0,
            "auxValue": 0,
            "customTips": "§l§3休闲模式匹配",
            "extraId": "solo_unranked"
        }, playerId, 0)
        for i in range(28):
            comp.SpawnItemToPlayerInv({
                "itemName": "minecraft:iron_sword",
                "count": 0,
                "auxValue": 0,
                "customTips": "§l§3休闲模式匹配",
                "extraId": "solo_unranked"
            }, playerId, i + 9)

        # comp.SpawnItemToPlayerInv({
        #     "itemName": "minecraft:iron_sword",
        #     "count": 0,
        #     "auxValue": 0,
        #     "customTips": "§l§3休闲模式匹配",
        #     "extraId": "solo_unranked"
        # }, playerId, 0)
        comp.SpawnItemToPlayerInv({
            "itemName": "minecraft:compass",
            "count": 1,
            "auxValue": 0,
            "customTips": "§l§3游戏菜单",
            "extraId": "menu"
        }, playerId, 1)


    def OnScriptTickServer(self):
        li = serverApi.GetPlayerList()
        # if li:
        #     comp = serverApi.GetEngineCompFactory().CreateHurt(li[0])
        #     comp.Hurt(9999, serverApi.GetMinecraftEnum().ActorDamageCause.EntityAttack, None, None, False)
        for playerId in li:

            # equip id:
            # 0 = in spawn
            # 1 = in fight
            try:
                value = equipStats[playerId]
            except KeyError:
                print('caught KeyError for OnScriptTickServer: dict=equipStats playerId='+playerId)
                lobbyGameApi.TryToKickoutPlayer(playerId, "出现错误，您被踢出游戏。请将以下内容汇报至管理员:\
                                                \nscript=ffa error=KeyError event=OnScriptTickServer dict=equipStats description=\"missed player key reg on AddServerPlayer\" playerId="+playerId)

            comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
            playerPos = comp.GetFootPos()
            if playerPos[1] <= 175 and equipStats[playerId]==0:
                print 'trig 1'
                uid = lobbyGameApi.GetPlayerUid(playerId)

                def Cb(args):
                    if args:
                        import math
                        date = math.floor(float(args))
                        if date > time.time():
                            self.sendTitle("§c§l禁止加入FFA", 1, playerId)
                            self.sendTitle("您因逃逸被禁止加入至§b%s" % (self.epoch2Datetime(date)), 2, playerId)
                            self.sendMsg('§c§l不妙！你被禁止FFA了！§r等不及了？使用§b/ransom ffa§r支付赎金立刻解除！\n§e需要支付 1024NEKO 或 32CREDITS （优先使用NEKO）。', playerId)
                            comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
                            comp.SetFootPos((107, 188, 105))
                            return

                # redisPool.AsyncGet("ffa-antilog-%s" % (uid,), Cb)

                self.giveKit(playerId)
                equipStats[playerId] = 1

            elif playerPos[1] >= 176 and equipStats[playerId]==1:
                print 'trig 2'
                menuSystem = serverApi.GetSystem('menu', 'menuSystem')
                menuSystem.giveMenu(1, playerId)
                print 'giveMenu pos of ' + playerId + ' is ' + str(playerPos)
                equipStats[playerId] = 0

            if playerPos[1] < 10:
                comp = serverApi.GetEngineCompFactory().CreateHurt(playerId)
                comp.Hurt(9999, serverApi.GetMinecraftEnum().ActorDamageCause.EntityAttack, None, None, False)