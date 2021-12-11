# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import json
import math
import apolloCommon.commonNetgameApi as commonNetgameApi
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.redisPool as redisPool
redisPool.InitDB(30) #建立连接池

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

blocks = {}
spawnPoints = {}
equipStats = {}
clutch = {}
clutchTimer = {}

# 在modMain中注册的Server System类
class bridgeServerSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.pvp = {}
        self.ListenEvents()

        print 'CALL ListenEvents'
        lobbyGameApi.ShieldPlayerJoinText(True)
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

    def blockPosChange(self, pos):
        pos = list(pos)
        for i in range(3):
            if int(pos[i]) > 0:
                pos[i] = int(pos[i])
            else:
                pos[i] = math.floor(pos[i])
        pos = tuple(pos)
        return pos

    def removeBlocks(self, playerId):
        try:
            comp = serverApi.GetEngineCompFactory().CreateBlockInfo(playerId)
            blockDict = {
                'name': 'minecraft:air',
                'aux': 0
            }
            for block in blocks[playerId]:
                comp.SetBlockNew(block, blockDict)
        except KeyError:
            pass

    def getBlockBelow(self, playerId):
        # console warning suppressor
        try:
            comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
            footPos = comp.GetFootPos()
            comp = serverApi.GetEngineCompFactory().CreateBlockInfo(playerId)
            return comp.GetBlockNew(self.blockPosChange((footPos[0], footPos[1]-1, footPos[2])))
        except TypeError:
            pass

    def victory(self, playerId):
        self.sendTitle("§6§lVictory", 1, playerId)
        self.sendTitle("练习已完成", 2, playerId)
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        comp.SetPos((0, 201, 0))
        self.sendCmd("/playsound random.levelup", playerId)
        self.removeBlocks(playerId)
        self.sendCmd("/effect @s instant_health 1 255 true", playerId)

    def sendMsg(self, msg, playerId):
        comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
        comp.NotifyOneMessage(playerId, msg, "§f")

    def spawnpoint(self, playerId):
        comp = self.CreateComponent(playerId, "Minecraft", "player")
        posComp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        suc = comp.SetPlayerRespawnPos(posComp.GetPos())
        spawnPoints[playerId] = posComp.GetPos()

        self.sendTitle("§b", 1, playerId)
        self.sendTitle("§aSpawnpoint", 2, playerId)
        self.removeBlocks(playerId)
        # comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        # comp.SetPos(spawnPoints[playerId])

        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        for i in range(35):
            comp.SetInvItemNum(i, 0)
        print 'give item to player'
        comp.SpawnItemToPlayerInv({
            'itemName': 'minecraft:sandstone',
            'count': 64,
            'auxValue': 0,
        }, playerId, 0)
        comp.SpawnItemToPlayerInv({
            'itemName': 'minecraft:sandstone',
            'count': 64,
            'auxValue': 0,
        }, playerId, 1)
        comp.SpawnItemToPlayerInv({
            'itemName': 'minecraft:diamond_pickaxe',
            'count': 1,
            'auxValue': 0,
        }, playerId, 2)


    #################################

    def ListenEvents(self):
        print 'events listening'
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self,
                            self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent",
                            self,
                            self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DestroyBlockEvent",
                            self,
                            self.OnDestroyBlock)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerAttackEntityEvent",
                            self,
                            self.OnPlayerAttackEntity)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerEntityTryPlaceBlockEvent",
                            self,
                            self.OnServerEntityTryPlaceBlock)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(),
                            "OnScriptTickServer",
                            self,
                            self.OnScriptTickServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self,
                            self.OnCommand)

        gameComp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        gameComp.SetCanBlockSetOnFireByLightning(False)
        gameComp.SetCanActorSetOnFireByLightning(False)
        spawnPos = gameComp.GetSpawnPosition()


        comp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        ruleDict = {
            'option_info': {
                'natural_regeneration': False,  # 自然生命恢复
                'immediate_respawn': True, # 作弊开启
                'show_death_messages': False,
                'show_coordinates': True
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

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("bridge", "bridgeClient", 'TestRequest', self, self.OnTestRequest)

    def OnPlayerAttackEntity(self, data):
        victimId = data['victimId']
        playerId = data['playerId']

        if not self.pvp[victimId] and playerId in serverApi.GetPlayerList():
            data['cancel'] = True
            self.sendMsg("§c不能攻击该玩家！", playerId)

    def OnAddServerPlayer(self, data):
        print 'OnAddServerPlayer playerId='+data['id']
        playerId = data['id']
        uid = data['uid']
        equipStats[playerId] = 0
        clutch[playerId] = 0
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        comp.SetFootPos((0, 201, 0))
        self.sendTitle("§b§l踩在绿宝石块上以获得方块", 3, playerId)

        self.pvp[playerId] = False
        def a(playerId):
            self.sendMsg("§b已默认关闭PVP。使用/pvp来开关PVP模式。",playerId)
        commonNetgameApi.AddTimer(5.0, a, playerId)

    def OnServerEntityTryPlaceBlock(self, data):
        playerId = data['entityId']
        x = data['x']
        y = data['y']
        z = data['z']
        
        if (abs(x)<5 and abs(z)<5) or (x > 100 and z > 100) or (x < -100 and z < -100):
            data['cancel'] = True
            print 'cancelled block place xyz='+str((x, y, z))
            self.sendTitle("§c§l这里不能放方块哦", 3, playerId)
            return

        comp = serverApi.GetEngineCompFactory().CreateBlockInfo(playerId)
        if comp.GetBlockNew((x, y-1, z))['name'] == 'minecraft:emerald_block' or comp.GetBlockNew((x, y-2, z))['name'] == 'minecraft:emerald_block':
            data['cancel'] = True
            print 'cancelled block place xyz=' + str((x, y, z))
            self.sendTitle("§c§l这里不能放方块哦", 3, playerId)
            return

        if comp.GetBlockNew((x, 200, z))['name'] not in ['minecraft:air', 'minecraft:melon_block', 'minecraft:quartz_block']:
            data['cancel'] = True
            print 'cancelled block=%s' % (comp.GetBlockNew((x, 200, z)),)
            self.sendTitle("§c§l这里不能放方块哦", 3, playerId)
            return

        if not(playerId in blocks):
            blocks[playerId] = []
        blocks[playerId].append((x, y, z))

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        if playerId in blocks:
            self.removeBlocks(playerId)
            blocks.pop(playerId)
        if playerId in spawnPoints:
            spawnPoints.pop(playerId)

    def OnScriptTickServer(self):
        if serverApi.GetPlayerList():
            self.sendCmd('/kill @e[type=item]', serverApi.GetPlayerList()[0])
            for playerId in serverApi.GetPlayerList():
                if playerId in blocks:
                    self.sendTitle(str(blocks[playerId]), 3, playerId)
                comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
                blockBelow = self.getBlockBelow(playerId)['name']
                # self.sendTitle(blockBelow, 3, playerId)
                # self.sendTitle(blockBelow, 3, playerId)
                if blockBelow == "minecraft:redstone_block":
                    self.victory(playerId)
                elif blockBelow == "minecraft:melon_block":
                    hurtcomp = serverApi.GetEngineCompFactory().CreateHurt(playerId)
                    hurtcomp.Hurt(0, serverApi.GetMinecraftEnum().ActorDamageCause.EntityAttack, playerId, None, True)
                # elif blockBelow == "minecraft:diamond_block" and not(clutch[playerId]): #clutch
                #     # ±64 200 -10
                #     # ±56 200 -10
                #     # ±58 200 -10
                #     def a():
                #         if clutch[playerId]:
                #             comp = serverApi.GetEngineCompFactory().CreateHurt(playerId)
                #             comp.Hurt(0, serverApi.GetMinecraftEnum().ActorDamageCause.EntityAttack, playerId, None, True)
                #     self.sendTitle("§b§l等待攻击", 3, playerId)
                #     clutchTimer[playerId] = commonNetgameApi.AddTimer(3.0, a)
                #     clutch[playerId] = 1

                if comp.GetPos()[1] < 185:
                    comp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId)
                    comp.KillEntity(playerId)
                    self.removeBlocks(playerId)

                if blockBelow == "minecraft:emerald_block" and equipStats[playerId] == 0:
                    equipStats[playerId] = 1
                    self.spawnpoint(playerId)
                    self.sendCmd("/playsound random.orb", playerId)
                elif not(blockBelow == "minecraft:emerald_block") and equipStats[playerId] == 1:
                    equipStats[playerId] = 0

                if not(blockBelow == "minecraft:diamond_block") and clutch[playerId]:
                    self.sendTitle("§c§l攻击取消。请站定不动等待攻击。", 3, playerId)
                    clutch[playerId] = 0
                    if clutchTimer[playerId]:
                        commonNetgameApi.CancelTimer(clutchTimer[playerId])


    def OnDestroyBlock(self, data):
        pos = (data['x'], data['y'], data['z'])
        playerId = data['playerId']
        name = data['fullName']
        aux = data['auxData']
        blockDict = {
            'name': name,
            'aux': aux
        }
        if name != "minecraft:sandstone":
            comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId)
            comp.SetBlockNew(pos, blockDict, 0, 0)

    def OnCommand(self, args):
        playerId = args['entityId']
        print 'oncommand'
        cmd = args['command'].split()
        print 'OnCommand playerId='+playerId+' cmd='+str(cmd)

        if cmd[0] == "hub" or cmd[0] == "lobby":
            transData = {'position': [107, 153, 105]}
            lobbyGameApi.TransferToOtherServer(playerId, 'lobby', json.dumps(transData))
        elif cmd[0] == '/pvp':
            self.pvp[playerId] = not(self.pvp[playerId])
            if self.pvp[playerId]:
                self.sendMsg('PVP已§a§l开启', playerId)
            else:
                self.sendMsg('PVP已§c§l关闭', playerId)
