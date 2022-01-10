# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import random
import ujson as json
import apolloCommon.commonNetgameApi as commonNetgameApi
import lobbyGame.netgameApi as lobbyGameApi
import survScript.survConsts as c
import apolloCommon.mysqlPool as mysqlPool
cooldown = {}

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

# 在modMain中注册的Server System类
class survSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        self.cd = {}
        self.reply = {}
        self.last = {}

        self.mIsOnline = False

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

    def overenchantedLogic(self, p, delay):
        def a(playerId):
            comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
            items = comp.GetPlayerAllItems(serverApi.GetMinecraftEnum().ItemPosType.INVENTORY)

            for item in items:
                if item:
                    enchantData = item['enchantData']
                    for enchantItem in enchantData:
                        if enchantItem[1] > 5 or enchantItem[1] < 0:
                            slot = items.index(item)
                            comp.SpawnItemToPlayerInv({
                                'itemName': 'minecraft:dirt',
                                'count': 0,
                                'auxValue': 0
                            }, playerId, slot)
                            commonNetgameApi.AddTimer(2.5, lambda p: lobbyGameApi.TryToKickoutPlayer(p, "§6与服务器断开连接"), playerId)

            items = comp.GetPlayerAllItems(serverApi.GetMinecraftEnum().ItemPosType.ARMOR)

            for item in items:
                if item:
                    enchantData = item['enchantData']
                    for enchantItem in enchantData:
                        if enchantItem[1] > 5 or enchantItem[1] < 0:
                            slot = items.index(item)
                            comp.SpawnItemToPlayerInv({
                                'itemName': 'minecraft:dirt',
                                'count': 0,
                                'auxValue': 0
                            }, playerId, slot)
                            commonNetgameApi.AddTimer(2.5, lambda p: lobbyGameApi.TryToKickoutPlayer(p, "§6与服务器断开连接"), playerId)

        commonNetgameApi.AddTimer(delay, a, p)

    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self, self.OnCommand)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerChatEvent", self, self.OnServerChat)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ActuallyHurtServerEvent", self, self.OnActuallyHurtServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerAttackEntityEvent", self, self.OnPlayerAttackEntity)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerJoinMessageEvent", self, self.OnPlayerJoinMessage)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerRespawnFinishServerEvent", self, self.OnPlayerRespawnFinishServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerLeftMessageServerEvent", self, self.OnPlayerLeftMessageServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CraftItemOutputChangeServerEvent", self, self.OnCraftItemOutputChangeServer)

        commonNetgameApi.AddRepeatedTimer(1.0, self.tick)

    def tick(self):
        for player in serverApi.GetPlayerList():

            self.sendCmd('/kill @e[type=npc]', player)
            self.sendCmd('/kill @e[type=wither]', player)

            if player in self.cd:
                self.cd[player] -= 1
                if self.cd[player] <= 0:
                    self.cd.pop(player)

            comp = serverApi.GetEngineCompFactory().CreateItem(player)
            items = comp.GetPlayerAllItems(serverApi.GetMinecraftEnum().ItemPosType.INVENTORY)

            for item in items:
                if item and 'enchantData' in item:
                    for enchantment in item['enchantData']:
                        if enchantment[1] > 5 or enchantment[1] < 0:
                            self.overenchantedLogic(player, 6.0)

    def OnCraftItemOutputChangeServer(self, args):
        playerId = args['playerId']
        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)

        # todo 铁毡输入位
        anvilInputItem = comp.GetOpenContainerItem(playerId, serverApi.GetMinecraftEnum().OpenContainerId.AnvilInputContainer, True)
        anvilMaterialItem = comp.GetOpenContainerItem(playerId, serverApi.GetMinecraftEnum().OpenContainerId.AnvilMaterialContainer, True)

        # todo 砂轮输入位
        grindstoneInputItem = comp.GetOpenContainerItem(playerId, serverApi.GetMinecraftEnum().OpenContainerId.GrindstoneInputContainer, True)
        grindstoneInput2Item = comp.GetOpenContainerItem(playerId, serverApi.GetMinecraftEnum().OpenContainerId.GrindstoneAdditionalContainer, True)

        # todo 锻造台输入位
        SmithingTableInputContainer = comp.GetOpenContainerItem(playerId, serverApi.GetMinecraftEnum().OpenContainerId.SmithingTableInputContainer, True)
        SmithingTableInput2Container = comp.GetOpenContainerItem(playerId, serverApi.GetMinecraftEnum().OpenContainerId.SmithingTableMaterialContainer, True)

        # todo 切石机输入位
        StonecutterInputContainer = comp.GetOpenContainerItem(playerId, serverApi.GetMinecraftEnum().OpenContainerId.StonecutterInputContainer, True)

        outputName = args['itemDict']['itemName']

        # todo 铁毡作弊
        if anvilInputItem != None and anvilInputItem['itemName'] != outputName:
            args['cancel'] = True
            self.sendCmd('/clear', playerId)
            lobbyGameApi.TryToKickoutPlayer(playerId, "§6与服务器断开连接")
        # todo 砂轮作弊
        if grindstoneInputItem != None and grindstoneInput2Item == None and grindstoneInputItem["itemName"] == "minecraft:enchanted_book" and outputName != "minecraft:book":
            args['cancel'] = True
            self.sendCmd('/clear', playerId)
            lobbyGameApi.TryToKickoutPlayer(playerId, "§6与服务器断开连接")
        elif grindstoneInputItem == None and grindstoneInput2Item != None and grindstoneInput2Item["itemName"] == "minecraft:enchanted_book" and outputName != "minecraft:book":
            args['cancel'] = True
            self.sendCmd('/clear', playerId)
            lobbyGameApi.TryToKickoutPlayer(playerId, "§6与服务器断开连接")
        elif grindstoneInputItem != None and grindstoneInput2Item != None and grindstoneInputItem["itemName"] != grindstoneInput2Item["itemName"] and grindstoneInputItem["itemName"] != outputName:
            args['cancel'] = True
            self.sendCmd('/clear', playerId)
            lobbyGameApi.TryToKickoutPlayer(playerId, "§6与服务器断开连接")

        #todo 锻造台
        items = {
            "minecraft:diamond_sword": "minecraft:netherite_sword",
            "minecraft:diamond_pickaxe": "minecraft:netherite_pickaxe",
            "minecraft:diamond_axe": "minecraft:netherite_axe",
            "minecraft:diamond_shovel": "minecraft:netherite_shovel",
            "minecraft:diamond_hoe": "minecraft:netherite_hoe",

            "minecraft:diamond_helmet": "minecraft:netherite_helmet",
            "minecraft:diamond_chestplate": "minecraft:netherite_chestplate",
            "minecraft:diamond_leggings": "minecraft:netherite_leggings",
            "minecraft:diamond_boots": "minecraft:netherite_boots"
        }
        # todo 锻造台输入1口不包含以上物品
        if SmithingTableInputContainer != None and SmithingTableInputContainer["itemName"] not in items:
            args['cancel'] = True
            self.sendCmd('/clear', playerId)
            lobbyGameApi.TryToKickoutPlayer(playerId, "§6与服务器断开连接")
        elif SmithingTableInputContainer != None and SmithingTableInputContainer["itemName"] in items and SmithingTableInput2Container["itemName"] != "minecraft:netherite_ingot":
            args['cancel'] = True
            self.sendCmd('/clear', playerId)
            lobbyGameApi.TryToKickoutPlayer(playerId, "§6与服务器断开连接")
        elif SmithingTableInputContainer != None and SmithingTableInputContainer["itemName"] in items and SmithingTableInput2Container["itemName"] == "minecraft:netherite_ingot" and outputName != items[SmithingTableInputContainer["itemName"]]:
            args['cancel'] = True
            self.sendCmd('/clear', playerId)
            lobbyGameApi.TryToKickoutPlayer(playerId, "§6与服务器断开连接")

        # todo 切石机取消生成
        if StonecutterInputContainer != None:
            args['cancel'] = True

    def OnActuallyHurtServer(self, data):
        playerId = data['srcId']
        hp = int(serverApi.GetEngineCompFactory().CreateAttr(data['entityId']).GetAttrValue(serverApi.GetMinecraftEnum().AttrType.HEALTH))
        if not playerId in serverApi.GetPlayerList():
            return

        if data['damage'] >= 20 and hp >= 20:
            data['damage'] = random.randint(1, 7)

    def OnPlayerAttackEntity(self, data):
        playerId = data['playerId']
        dmg = data['damage']

        if dmg > 50:
            data['cancel'] = True
            lobbyGameApi.TryToKickoutPlayer(playerId, "§6与服务器断开连接")

        self.overenchantedLogic(playerId, 2.0)

        print 'FOUND PLAYER WITH 32K'

    def OnPlayerJoinMessage(self, data):
        nick = data['name']
        data['message'] = '§7%s 加入了' % nick

        # 软封禁
        shadowBanList = c.shadowBanUsernames
        isBan = False
        for name in shadowBanList:
            if name in nick:
                isBan = True
                break

        if isBan:
            chance = c.shadowBanChance
            if random.randint(1, 100) <= chance:
                delay = random.randint(30, 120)
                print 'shadowban! delay=', delay
                def a(p):
                    lobbyGameApi.TryToKickoutPlayer(p, "§6与服务器断开连接")
                commonNetgameApi.AddTimer(delay, a, data['id'])

    def OnPlayerLeftMessageServer(self, data):
        nick = data['name']
        data['message'] = '§7%s 退出了' % nick

        playerId = data['id']
        if playerId in self.cd:
            self.cd.pop(playerId)
        if playerId in self.reply:
            self.reply.pop(playerId)
        if playerId in self.last:
            self.last.pop(playerId)

    def OnServerChat(self, data):
        playerId = data['playerId']

        msg = data['message'].strip('§')
        if msg[0] == '>':
            msg = '§a>§r'+msg

        if playerId in self.cd:
            data['cancel'] = True
            self.cd[playerId] += 1
        else:
            self.cd[playerId] = 4

        data['msg'] = msg

    def OnPlayerRespawnFinishServer(self, data):
        playerId = data['playerId']

        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        items = comp.GetPlayerAllItems(serverApi.GetMinecraftEnum().ItemPosType.INVENTORY)

        for item in items:
            if item:
                slot = items.index(item)
                comp.SpawnItemToPlayerInv({
                    'itemName': 'minecraft:dirt',
                    'count': 0,
                    'auxValue': 0
                }, playerId, slot)
                commonNetgameApi.AddTimer(2.5, lambda p: lobbyGameApi.TryToKickoutPlayer(p, "§6与服务器断开连接"),
                                          playerId)

        items = comp.GetPlayerAllItems(serverApi.GetMinecraftEnum().ItemPosType.ARMOR)

        for item in items:
            if item:
                slot = items.index(item)
                comp.SpawnItemToPlayerInv({
                    'itemName': 'minecraft:dirt',
                    'count': 0,
                    'auxValue': 0
                }, playerId, slot)
                commonNetgameApi.AddTimer(2.5, lambda p: lobbyGameApi.TryToKickoutPlayer(p, "§6与服务器断开连接"),
                                          playerId)

        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        pos = comp.GetFootPos()

        if abs(pos[0]) < 1000 and abs(pos[2]) < 1000:
            self.RandomPos(playerId, pos[1])

    def RandomPos(self, playerId, y=256):
        x = random.randint(-1024, 1024)
        z = random.randint(-1024, 1024)

        checkBuffer = y
        for i in range(255):
            comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
            blockDict = comp.GetBlockNew((x, (256 - y), z), 0)
            if blockDict['name'] == 'minecraft:air':
                break
            else:
                checkBuffer -= 1

        print 'simulated pos = %s' % ((x, y, z),)

        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        comp.SetFootPos((x, y, z))

        return (x, y, z)

    def OnCommand(self, data):
        playerId = data['entityId']
        msg = data['command'].split()
        cmd = msg[0].strip('/')
        data['cancel'] = True
        if cmd == 'kill':
            self.sendCmd('/kill', playerId)
        elif cmd == 'hub':
            transData = {'position': [1, 2, 3]}
            lobbyGameApi.TransferToOtherServer(playerId, 'auth', json.dumps(transData))
        elif cmd == 'list':
            msg = ''
            for player in serverApi.GetPlayerList():
                nickname = lobbyGameApi.GetPlayerNickname(player)
                uid = lobbyGameApi.GetPlayerUid(player)
                msg = msg + '%s-----%s §l§c| §r' % (nickname, uid)
            self.sendMsg(msg, playerId)
            print '=== surv player exe list ===', msg

        elif cmd in ['t', 'w', 'msg', 'tell']:
            if len(msg) < 3:
                self.sendMsg('§6/%s <player> <msg...' % cmd, playerId)
                return

            target = msg[1]
            self.mIsOnline = False
            for player in serverApi.GetPlayerList():
                if lobbyGameApi.GetPlayerNickname(player) == target:
                    self.mIsOnline = True
                    break

            if not self.mIsOnline:
                self.sendMsg('§6This player is offline', playerId)
                return

            msg = msg.replace('/%s ' % cmd, '').replace('%s ' % lobbyGameApi.GetPlayerNickname(target), '')

            self.sendMsg('§dTo %s: %s' % (lobbyGameApi.GetPlayerNickname(target), msg), playerId)
            self.sendMsg('§d%s: %s' % (lobbyGameApi.GetPlayerNickname(player), msg), target)

            self.last[playerId] = target
            self.reply[target] = playerId
        elif cmd == 'r':
            if len(msg) < 2:
                self.sendMsg('§6/%s <msg...' % cmd, playerId)
                return
            elif playerId not in self.reply:
                self.sendMsg('§6没人可以回复' % cmd, playerId)
                return

            target = self.reply[playerId]
            self.mIsOnline = False
            for player in serverApi.GetPlayerList():
                if lobbyGameApi.GetPlayerNickname(player) == target:
                    self.mIsOnline = True
                    break

            if not self.mIsOnline:
                self.sendMsg('§6This player is offline', playerId)
                return

            msg = msg.replace('/%s ' % cmd, '')

            self.sendMsg('§dTo %s: %s' % (lobbyGameApi.GetPlayerNickname(target), msg), playerId)
            self.sendMsg('§d%s: %s' % (lobbyGameApi.GetPlayerNickname(player), msg), target)

            self.last[playerId] = target
            self.reply[target] = playerId
        elif cmd == 'l':
            if len(msg) < 2:
                self.sendMsg('§6/%s <msg...' % cmd, playerId)
                return
            elif playerId not in self.last:
                self.sendMsg('§6你还没跟任何人私聊过' % cmd, playerId)
                return

            target = self.reply[playerId]
            self.mIsOnline = False
            for player in serverApi.GetPlayerList():
                if lobbyGameApi.GetPlayerNickname(player) == target:
                    self.mIsOnline = True
                    break

            if not self.mIsOnline:
                self.sendMsg('§6This player is offline', playerId)
                return

            msg = msg.replace('/%s ' % cmd, '')

            self.sendMsg('§dTo %s: %s' % (lobbyGameApi.GetPlayerNickname(target), msg), playerId)
            self.sendMsg('§d%s: %s' % (lobbyGameApi.GetPlayerNickname(player), msg), target)

            self.last[playerId] = target
            self.reply[target] = playerId

        elif cmd == 'cmdhelp':
            self.sendMsg("""§6------------------------
§3/kill - Commit suicide
/hub - back to main server
/cmdhelp - shows this page
/t /w /msg - PM Others
/r /reply - reply to last player
/l /last - PM last contacted player
§6------------------------""", playerId)
        else:
            self.sendMsg('§4Bad command. Do /cmdhelp for a list of commands.', playerId)
