# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import json
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.commonNetgameApi as commonNetgameApi

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

selectProt = {}
page = {}

import apolloCommon.redisPool as redisPool

# 在modMain中注册的Server System类
class menuServerSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()
        redisPool.InitDB(30)
        self.uids = {}

    ##############UTILS##############

    def sendCmd(self, cmd, playerId):
        comp = serverApi.GetEngineCompFactory().CreateCommand(serverApi.GetLevelId())
        comp.SetCommand(cmd, playerId)

    def sendTitle(self, title, type, playerId):
        if (type == 1):
            self.sendCmd("/title @s title "+title, playerId)
        elif (type == 2):
            self.sendCmd("/title @s subtitle " + title, playerId)
        elif (type == 3):
            self.sendCmd("/title @s actionbar " + title, playerId)
        else:
            print 'invalid params for call/sendTitle(): type'

    def forceSelect(self, slot, playerId):
        #print 'forceSelect called slot='+slot+' playerId='+playerId
        comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
        comp.ChangeSelectSlot(slot)

    def sendMsg(self, msg, playerId):
        comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
        comp.NotifyOneMessage(playerId, msg, "§f")

    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self,
                            self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent",
                            self,
                            self.OnDelServerPlayerEvent)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerDieEvent",
                            self,
                            self.OnPlayerDie)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnCarriedNewItemChangedServerEvent",
                            self,
                            self.OnCarriedNewItemChangedServer)
        self.ListenForEvent('unrankedService', 'unrankedService', 'CheckMatchmakingEvent', self, self.OnCheckMatchmaking)
        self.ListenForEvent('menu', 'menuClient', 'MenuActionEvent', self,
                            self.OnMenuAction)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("lobbyutils", "lobbyutilsClient", 'TestRequest', self, self.OnTestRequest)

    def OnAddServerPlayer(self, data):
        playerId = data['id']

        args = {
            "playerId": lobbyGameApi.GetPlayerUid(playerId)
        }
        self.RequestToService("matchmaking", "CancelMatchmakingEvent", args, self.OnCallback)

        self.uids[playerId] = lobbyGameApi.GetPlayerUid(playerId)

        if not(playerId in page):
            page[playerId] = 1
        if not(playerId in selectProt):
            selectProt[playerId] = 0
        print('OnAddServerPlayer playerId='+playerId)
        self.giveMenu(1, playerId)
        comp = serverApi.GetEngineCompFactory().CreateEffect(playerId)
        comp.AddEffectToEntity("instant_health", 1, 255, False)

    def OnDelServerPlayerEvent(self, data):
        playerId = data['id']
        print 'ondelserveplayer uid=%s (1)' % (playerId,)
        print 'ondelserveplayer uid=%s (2)' % (self.uids[playerId],)


        args = {
            "playerId": lobbyGameApi.GetPlayerUid(self.uids[playerId],)
        }
        self.RequestToService("matchmaking", "CancelMatchmakingEvent", args, self.OnCallback)

        def a(id):
            self.uids.pop(id)
        commonNetgameApi.AddTimer(0.5, a, playerId)

        if playerId in page:
            page.pop(playerId)
        if playerId in selectProt:
            selectProt.pop(playerId)

    def OnMenuAction(self, data):
        print 'CALL OnMenuAction data=%s' % (data,)
        choice = data['choice']
        playerId = data['playerId']

        if choice == 'unranked':

            # self.sendMsg("§e模式出现重大bug，正在紧急修复", playerId)
            # return

            mode = data['mode']
            matchSystem = serverApi.GetSystem('match', 'matchSystem')
            matchSystem.UnrankedMatch(playerId, mode)
            self.giveMenu(0, playerId)
            return
        elif choice == 'rush':
            # self.sendMsg("§e模式出现重大bug，正在紧急修复", playerId)
            # return

            transData = {'position': [0, 201, 4]}
            lobbyGameApi.TransferToOtherServer(playerId, 'game_rush', json.dumps(transData))
            return
        elif choice == 'bts':
            transData = {'position': [0, 242, 0]}
            lobbyGameApi.TransferToOtherServer(playerId, 'game_bts', json.dumps(transData))
            return
        elif choice == 'bridge':
            transData = {'position': [0, 201, 0]}
            lobbyGameApi.TransferToOtherServer(playerId, 'game_practice', json.dumps(transData))
            return
        elif choice == 'cparty':
            transData = {'position': [0, 22, 0]}
            lobbyGameApi.TransferToOtherServer(playerId, 'game_cparty', json.dumps(transData))
            return

    def OnCarriedNewItemChangedServer(self, data):

        new = data['newItemDict']
        playerId = data['playerId']
        print 'OnCarriedNewItemChangedServer playerId='+playerId+' dict='+str(new)+' selecProt='+str(selectProt[playerId])
        newTag = 'air'

        if new:
            if new['extraId']:
                 newTag = new['extraId']
            print 'OnCarriedNewItemChangedServer newTag='+newTag+' page='+str(page[playerId])


        # equipStats = redisPool.AsyncGet(playerId)

        # if equipStats['ffaStats'] == 0:
        if True:
            if newTag:
                def a():
                    selectProt[playerId] = 0
                if page[playerId] == 0:
                    if newTag == "exitqueue":
                        print 'do exitquee'
                        if selectProt[playerId] == 1 or 'noMenu' in data:
                            if 'noMenu' not in data:
                                print 'giving menu'
                                self.giveMenu(1, playerId)
                            args = {
                                "playerId": lobbyGameApi.GetPlayerUid(playerId)
                            }
                            self.RequestToService("matchmaking", "CancelMatchmakingEvent", args, self.OnCallback)
                            menuSystem = serverApi.GetSystem('match', 'matchSystem')
                            if playerId in menuSystem.matching:
                                menuSystem.matching.pop(menuSystem.matching.index(playerId))
                            return
                        self.forceSelect(0, playerId)
                        selectProt[playerId] = 1
                        self.sendTitle("§7再次点击§c§l退出匹配", 3, playerId)

                elif page[playerId] == 1:
                    if "notdone" in newTag:
                        self.forceSelect(0, playerId)
                        self.sendTitle("§l§c该功能开发中，敬请期待", 3, playerId)
                    elif newTag == "mainmenu":
                        self.giveMenu(1, playerId)
                    elif newTag == "menu":
                        if selectProt[playerId] == 1:
                            self.NotifyToClient(playerId, "OpenMenuEvent", 0)
                            return
                        self.forceSelect(0, playerId)
                        selectProt[playerId] = 1
                        self.sendTitle("§7再次点击§b§l打开菜单", 3, playerId)
                    elif newTag == "sign":
                        if selectProt[playerId] == 1:
                            signSystem = serverApi.GetSystem('sign', 'signSystem')
                            signSystem.TrySign(playerId)
                            return
                        self.forceSelect(0, playerId)
                        selectProt[playerId] = 1
                        self.sendTitle("§7再次点击§b§l每日签到", 3, playerId)
                    elif newTag == "mail":
                        if selectProt[playerId] == 1:
                            self.NotifyToClient(playerId, "OpenMailEvent", None)
                            return
                        self.forceSelect(0, playerId)
                        selectProt[playerId] = 1
                        self.sendTitle("§7再次点击进入§b§l邮件", 3, playerId)
                    elif newTag == "draw":
                        if selectProt[playerId] == 1:
                            drawSystem = serverApi.GetSystem('draw', 'drawSystem')
                            drawSystem.OpenDrawUi(playerId)
                            return
                        self.forceSelect(0, playerId)
                        selectProt[playerId] = 1
                        self.sendTitle("§7再次点击§b§l抽奖", 3, playerId)
                    elif newTag == "cos":
                        if selectProt[playerId] == 1:
                            cosSystem = serverApi.GetSystem('cos', 'cosSystem')
                            cosSystem.EnterCosMgr(playerId)
                            return
                        self.forceSelect(0, playerId)
                        selectProt[playerId] = 1
                        self.sendTitle("§7再次点击§b§l管理库存&购买商品", 3, playerId)
                    elif newTag == "trending_bw":
                        if selectProt[playerId] == 1:
                            self.ApiRequestBwMatchmaking(playerId)
                            return
                        self.forceSelect(0, playerId)
                        selectProt[playerId] = 1
                        self.sendTitle("§7再次点击快速游玩§c§l起床战争", 3, playerId)
                    elif newTag == "solo_unranked":
                        if selectProt[playerId] == 1:
                            self.giveMenu(2, playerId)
                            return
                        self.forceSelect(0, playerId)
                        selectProt[playerId] = 1
                        self.sendTitle("§7再次点击加入§b§l休闲模式匹配队列", 3, playerId)
                    elif newTag == "practice":
                        if selectProt[playerId] == 1:
                            print 'player select practice playerId='+playerId
                            self.giveMenu(1, playerId)
                            transData = {'position': [1, 2, 3]}
                            lobbyGameApi.TransferToOtherServer(playerId, 'game_practice', json.dumps(transData))
                            return
                        self.forceSelect(0, playerId)
                        selectProt[playerId] = 1
                        self.sendTitle("§7再次点击进入§3§l搭路区", 3, playerId)
                    elif newTag == "rush":
                        if selectProt[playerId] == 1:
                            print 'player select practice playerId='+playerId
                            self.giveMenu(1, playerId)
                            transData = {'position': [0, 201, 4]}
                            lobbyGameApi.TransferToOtherServer(playerId, 'game_rush', json.dumps(transData))
                            return
                        self.forceSelect(0, playerId)
                        selectProt[playerId] = 1
                        self.sendTitle("§7再次点击进入§3§lMLGRush", 3, playerId)

                elif page[playerId] == 2:
                    if "notdone" in newTag:
                        self.giveMenu(1, playerId)
                        self.sendTitle("§l§c该模式开发中，敬请期待", 3, playerId)
                        self.forceSelect(0, playerId)
                    elif newTag == "unranked.s2p2":
                        if selectProt[playerId] == 1:
                            args = {
                                "playerId": playerId,
                                "mode": "s2p2",
                                "operation": "pre_start"
                            }
                            self.RequestToService("matchmaking", "RequestMatchmakingEvent", args, self.OnCallback)
                            self.giveMenu(0, playerId)
                            return
                        self.forceSelect(0, playerId)
                        selectProt[playerId] = 1
                        self.sendTitle("§7再次开始匹配§b§lSharp2Prot2", 3, playerId)
                    elif newTag == "unranked.totem":
                        if selectProt[playerId] == 1:
                            args = {
                                "playerId": playerId,
                                "mode": "totem",
                                "operation": "pre_start"
                            }
                            self.RequestToService("matchmaking", "RequestMatchmakingEvent", args, self.OnCallback)
                            self.giveMenu(0, playerId)
                            return
                        self.forceSelect(0, playerId)
                        selectProt[playerId] = 1
                        self.sendTitle("§7再次开始匹配§b§l32k", 3, playerId)
                    elif newTag == "mainmenu":
                        if selectProt[playerId] == 1:
                            self.giveMenu(1, playerId)
                            return
                        self.forceSelect(0, playerId)
                        selectProt[playerId] = 1
                        self.sendTitle("§7再次点击§e§l返回主菜单", 3, playerId)

                commonNetgameApi.AddTimer(4.5, a)

    def OnCheckMatchmaking(self, args):
        redirect = args
        print 'CALL OnCheckMatchmaking args='+str(redirect)
        self.OnCallback(True, redirect)

    def ManhuntMatchmakingCallback(self, suc, data):
        if not suc:
            print 'OnCallback timeout'
            return
        value = data['value']
        playerId = data['playerId']

        if value == 0:
            self.sendMsg("§c§l无法加入房间：§r没有开放的房间可供您加入。", playerId)
            return
        elif value == 1:
            sid = data['sid']
            self.sendMsg("§3即将将您传送至game_manhunt-%s，请稍等片刻" % (sid,), playerId)
            def a():
                transData = {'position': [1, 2, 3]}
                lobbyGameApi.TransferToOtherServerById(playerId, sid, json.dumps(transData))
            commonNetgameApi.AddTimer(2.0, a)

    def BwMatchmakingCallback(self, suc, data):
        if not suc:
            print 'OnCallback timeout'
            return
        value = data['value']
        playerId = data['playerId']

        if value == 0:
            self.sendMsg("§c§l无法加入房间：§r没有开放的房间可供您加入。", playerId)
            return
        elif value == 1:
            sid = data['sid']
            self.sendMsg("§3即将将您传送至game_bw-%s，请稍等片刻" % (sid,), playerId)
            def a():
                transData = {'position': [1, 2, 3]}
                lobbyGameApi.TransferToOtherServerById(playerId, sid, json.dumps(transData))
            commonNetgameApi.AddTimer(1.0, a)
            commonNetgameApi.AddTimer(2.0, lambda p: self.sendMsg('§c分配房间失败！请再试一次!', p), playerId)

    def ApiRequestManhuntMatchmaking(self, playerId):
        self.RequestToServiceMod("manhunt", "RequestMatchmakingEvent", playerId, self.ManhuntMatchmakingCallback, 2)

    def ApiRequestBwMatchmaking(self, playerId, mode):
        expdSystem = serverApi.GetSystem('expd', 'expdSystem')
        expdDict = expdSystem.players
        if playerId not in expdDict:
            self.sendMsg('§e正在验证您的冷却状态，请稍后...', playerId)
            return
        elif expdDict[playerId]:
            self.sendMsg('Operation not permitted', playerId)
            return

        self.RequestToServiceMod("bw", "RequestMatchmakingEvent", {
            'playerId': playerId,
            'mode': mode
        }, self.BwMatchmakingCallback, 2)

    def OnCallback(self, suc, args):
        if not suc:
            print 'OnCallback timeout'
            return

        print 'CALL OnCallback args='+str(args)
        player2Id = 0
        try:
            event = args["event"]
        except TypeError:
            event = "error"
        playerId = lobbyGameApi.GetPlayerIdByUid(args["playerId"])
        try:
            server = args['server']
        except KeyError:
            pass
        try:
            player2Id = args["rivalId"]
        except KeyError:
            player2Id = 0
        if event == "RequestMatchmakingEvent":
            if args["value"] == "waiting":
                self.sendTitle("§e正在匹配...", 1, playerId)
                self.sendTitle("§l匹配进度：§r§b等待玩家§7》等待可用的房间》开始比赛", 3, playerId)
            elif args["value"] == "queue":
                self.sendTitle("§e正在等待空闲的房间...", 1, playerId)
                self.sendTitle("我们的比赛服务器爆满，因此可能需要一些等待。", 2, playerId)
                self.sendTitle("§l匹配进度：§r§b等待玩家》等待可用的房间§7》开始比赛", 3, playerId)
            elif args["value"] == "ready":
                self.sendTitle("§a匹配成功 即将开始", 1, playerId)
                self.sendTitle("§a匹配成功 即将开始", 1, player2Id)
                comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
                comp.NotifyOneMessage(playerId, "§e§l已找到对手：§r"+lobbyGameApi.GetPlayerNickname(playerId)+"§e§l! §b游戏即将开始!","§f")
                comp = serverApi.GetEngineCompFactory().CreateMsg(player2Id)
                comp.NotifyOneMessage(player2Id, "§e§l已找到对手：§r" + lobbyGameApi.GetPlayerNickname(args['playerId']) + "§e§l! §b游戏即将开始!", "§f")

                args = {
                    "p1": playerId,
                    "p1uid": lobbyGameApi.GetPlayerUid(playerId),
                    "p2": player2Id,
                    "p2uid": lobbyGameApi.GetPlayerUid(player2Id),
                    "mode": args['mode'],
                    "server": server
                }
                self.RequestToService("matchmaking", "NotifyStartGameEvent", args, self.OnCallback)
                print 'send matchmaking/NotifyStartGameEvent args='+str(args)
                transData = {'position': [45, 200, 0]}
                lobbyGameApi.TransferToOtherServerById(playerId, server, json.dumps(transData))
                transData = {'position': [-45, 200, 0]}
                lobbyGameApi.TransferToOtherServerById(player2Id, server, json.dumps(transData))
        elif event == "NotifyStartGameEvent":
            transData = {'position': [45, 200, 0]}
            lobbyGameApi.TransferToOtherServerById(playerId, server, json.dumps(transData))
            transData = {'position': [-45, 200, 0]}
            lobbyGameApi.TransferToOtherServerById(player2Id, server, json.dumps(transData))
        elif event == "CancelMatchmakingEvent":
            if args["value"] == "ok":
                self.sendTitle("§c已取消匹配", 1, playerId)
                if serverApi.GetEngineCompFactory().CreatePos(playerId).GetPos()[1] > 177:
                    self.giveMenu(1, playerId)
            elif args["value"] == 1:
                self.sendTitle("玩家不在匹配中！", 1, playerId)
                self.giveMenu(1, playerId)

    def giveMenu(self, pageId, playerId):
        page[playerId] = pageId
        # for i in range(4):
        #     if not comp.GetEntityItem("ARMOR", i)["itemName"] == "minecraft:air":
        #         comp.SetInvItemNum(i, 0)
        comp = serverApi.GetEngineCompFactory().CreateCommand(serverApi.GetLevelId())
        comp.SetCommand("/clear @s", playerId)  # 传送指令
        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)

        print 'giving menu'

        self.forceSelect(0, playerId)
        selectProt[playerId] = 0

        for i in range(36):
            comp.SpawnItemToPlayerInv({
                "itemName": "minecraft:iron_sword",
                "count": 0,
                "auxValue": 0,
                "customTips": "§l§3休闲模式匹配",
                "extraId": "solo_unranked"
            }, playerId, i)

        if pageId == 1:
            for i in range(28):
                comp.SpawnItemToPlayerInv({
                    "itemName": "minecraft:iron_sword",
                    "count": 0,
                    "auxValue": 0,
                    "customTips": "§l§3休闲模式匹配",
                    "extraId": "solo_unranked"
                }, playerId, i+9)

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
            comp.SpawnItemToPlayerInv({
                "itemName": "minecraft:emerald",
                "count": 1,
                "auxValue": 0,
                "customTips": "§l§d每日签到",
                "extraId": "sign"
            }, playerId, 2)
            comp.SpawnItemToPlayerInv({
                "itemName": "minecraft:sign",
                "count": 1,
                "auxValue": 0,
                "customTips": "§l§e邮件",
                "extraId": "mail"
            }, playerId, 3)
            comp.SpawnItemToPlayerInv({
                "itemName": "minecraft:ender_chest",
                "count": 1,
                "auxValue": 0,
                "customTips": "§l§c抽奖",
                "extraId": "draw"
            }, playerId, 4)
            comp.SpawnItemToPlayerInv({
                "itemName": "minecraft:chest",
                "count": 1,
                "auxValue": 0,
                "customTips": "§l§6库存&商店",
                "extraId": "cos"
            }, playerId, 5)
            comp.SpawnItemToPlayerInv({
                "itemName": "minecraft:bed",
                "count": 1,
                "auxValue": 14,
                "customTips": "§d快速游玩§l§c起床§f战争",
                "extraId": "trending_bw"
            }, playerId, 8)
            # comp.SpawnItemToPlayerInv({
            #     "itemName": "minecraft:diamond_sword",
            #     "count": 1,
            #     "auxValue": 0,
            #     "customTips": "§l§3竞技模式匹配",
            #     "extraId": "notdone.solo_ranked"
            # }, playerId, 2)
            # comp.SpawnItemToPlayerInv({
            #     "itemName": "minecraft:golden_sword",
            #     "count": 1,
            #     "auxValue": 0,
            #     "customTips": "§l§35人团队竞技匹配",
            #     "extraId": "notdone.5v_ranked"
            # }, playerId, 3)
            # comp.SpawnItemToPlayerInv({
            #     "itemName": "minecraft:wool",
            #     "count": 1,
            #     "auxValue": 0,
            #     "customTips": "§l§b搭路区",
            #     "extraId": "notdone.practice"
            # }, playerId, 4)
            # comp.SpawnItemToPlayerInv({
            #     "itemName": "minecraft:stick",
            #     "count": 1,
            #     "auxValue": 0,
            #     "enchantData": [(12, 2)],
            #     "customTips": "§l§bMLGRush",
            #     "extraId": "rush"
            # }, playerId, 5)
            # comp.SpawnItemToPlayerInv({
            #     "itemName": "minecraft:book",
            #     "count": 1,
            #     "auxValue": 0,
            #     "customTips": "§l§a玩家互交功能",
            #     "extraId": "notdone.interact"
            # }, playerId, 6)
            # comp.SpawnItemToPlayerInv({
            #     "itemName": "minecraft:fishing_rod",
            #     "count": 1,
            #     "auxValue": 0,
            #     "customTips": "§l§e赛事",
            #     "extraId": "notdone.tournaments"
            # }, playerId, 7)
            # comp.SpawnItemToPlayerInv({
            #     "itemName": "minecraft:redstone",
            #     "count": 1,
            #     "auxValue": 0,
            #     "customTips": "§l§c设置",
            #     "extraId": "notdone.settings"
            # }, playerId, 8)
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

        elif pageId == 2:
            print 'start to give item page=2'
            comp.SpawnItemToPlayerInv({
                "itemName": "minecraft:diamond_sword",
                "count": 1,
                "auxValue": 0,
                "customTips": "§b锋利2保护(SHARP2PROT2)",
                "extraId": "unranked.s2p2"
            }, playerId, 1)
            comp.SpawnItemToPlayerInv({
                "itemName": "minecraft:stick",
                "count": 1,
                "auxValue": 0,
                "customTips": "§b相扑(SUMO)",
                "extraId": "notdone.unranked.sumo"
            }, playerId, 2)
            comp.SpawnItemToPlayerInv({
                "itemName": "minecraft:iron_sword",
                "count": 1,
                "auxValue": 0,
                "customTips": "§b单刀赴会(ONLYSWORD)",
                "extraId": "notdone.unranked.onlysword"
            }, playerId, 3)
            comp.SpawnItemToPlayerInv({
                "itemName": "minecraft:golden_apple",
                "count": 1,
                "auxValue": 0,
                "customTips": "§bBuild UHC",
                "extraId": "notdone.unranked.buhc"
            }, playerId, 4)
            comp.SpawnItemToPlayerInv({
                "itemName": "minecraft:bow",
                "count": 1,
                "auxValue": 0,
                "customTips": "§b弓箭战(ARCHER)",
                "extraId": "notdone.unranked.archer"
            }, playerId, 5)
            comp.SpawnItemToPlayerInv({
                "itemName": "minecraft:golden_sword",
                "count": 1,
                "auxValue": 0,
                "customTips": "§b无限连击(COMBO)",
                "extraId": "notdone.unranked.combo"
            }, playerId, 6)
            comp.SpawnItemToPlayerInv({
                "itemName": "minecraft:totem",
                "count": 1,
                "auxValue": 0,
                "customTips": "§b32k拼刀(32K)",
                "extraId": "unranked.totem"
            }, playerId, 7)
            comp.SpawnItemToPlayerInv({
                "itemName": "minecraft:redstone",
                "count": 1,
                "auxValue": 0,
                "customTips": "§c§l返回上级菜单",
                "extraId": "mainmenu"
            }, playerId, 8)

        elif pageId == 0:
            print 'CALL giveMenu pageId=0'
            for i in range(27):
                comp.SpawnItemToPlayerInv({
                    "itemName": "minecraft:iron_sword",
                    "count": 0,
                    "auxValue": 0,
                    "customTips": "§l§3休闲模式匹配",
                    "extraId": "solo_unranked"
                }, playerId, i+9)

            comp.SpawnItemToPlayerInv({
                "itemName": "minecraft:iron_sword",
                "count": 0,
                "auxValue": 0,
                "customTips": "§l§3休闲模式匹配",
                "extraId": "solo_unranked"
            }, playerId, 0)
            comp.SpawnItemToPlayerInv({
                "itemName": "minecraft:redstone",
                "count": 1,
                "auxValue": 0,
                "customTips": "§c§l退出匹配",
                "extraId": "exitqueue"
            }, playerId, 4)

    def OnPlayerDie(self, data):
        playerId = data['id']
        self.giveMenu(1, playerId)