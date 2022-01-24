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
import v5Script.skillMgr as skillMgr

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
class v5SystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()
        self.consts = c
        
        # ------------------
        u"""
            Variables: PrepScreen and WeaponSelection related variables
        """

        self.selectionData = {
            0: {},
            1: {}
        }
        # Structure:
        # selectionData{
        #     team: {
        #         player: [weaponSelectionId, skillSelectionId]
        #     }
        # }

        self.playerKits = {}
        # Structure:
        # playerKits{
        #     playerId: {
        #         slotId: ['itemId', usesLeft]
        #     }
        # }

        self.playerEquips = {}
        self.playerIsFixing = {}
        self.playerNearSite = {}

        self.timers = {}
        self.defuserPlanting = False
        self.defuserDestroying = False
        self.defuserActive = False
        self.roundTimer = c.roundTime
        self.defuserPlanted = False
        self.timerTicking = False
        self.reinfLeft = 0

        self.teams = {}
        self.pts = {}
        self.kd = {}
        self.waiting = []
        self.defenders = []
        self.attackers = []
        self.currentSite = []
        self.defuserDropPos = ()

        self.status = 0
        self.phase = 0
        self.countdown = 60
        self.defuserCarrier = None

        self.wins = {
            0: 0,
            1: 0
        }
        self.alivePlayers = {
            0: 5,
            1: 5
        }
        self.alive = {}
        self.rff = {}
        self.roundNum = 1
        self.roundSiteIndex = 0

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
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnScriptTickServer", self, self.OnScriptTickServer)

        # self.ListenForEvent('hud', 'hudClient', "DisplayDeathDoneEvent", self, self.OnDisplayDeathDone)
        # self.ListenForEvent('music', 'musicSystem', 'CreateMusicIdEvent', self, self.OnCreateMusicId)

        self.ListenForEvent('v5', 'v5Client', 'ActionEvent', self, self.OnClientAction)

        self.ListenForEvent('hud', 'hudSystem', 'PlayerDeathEvent', self, self.HudPlayerDeathEvent)

        commonNetgameApi.AddRepeatedTimer(1.0, self.roundTick)
        commonNetgameApi.AddRepeatedTimer(1.0, self.boardTick)
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
        self.RequestToServiceMod("service_v5", "RecordSidEvent", args)

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

        if operation == 'weaponSelect':
            selectionId = int(data['selectionId'])

            isRepeat = False
            for player in self.selectionData[self.teams[playerId]]:
                teamSelectionDict = self.selectionData[self.teams[playerId]]
                id = teamSelectionDict[player][0]

                # id is others' selection
                # selectionId is new selection
                if id == selectionId:
                    if player == playerId:
                        selectionId = 0
                        isRepeat = False
                    else:
                        isRepeat = True
                    break

            if not isRepeat:
                self.selectionData[self.teams[playerId]][playerId][0] = selectionId

            if self.phase == 0 and not c.debugMode:
                self.ShowPrepSelectionScreen(True, True)
            else:
                self.ShowPrepSelectionScreen(False, True)

        elif operation == 'skillSelect':
            selectionId = int(data['selectionId'])

            isRepeat = False
            for player in self.selectionData[self.teams[playerId]]:
                teamSelectionDict = self.selectionData[self.teams[playerId]]
                id = teamSelectionDict[player][1]

                # id is others' selection
                # selectionId is new selection
                if id == selectionId:
                    if player == playerId:
                        selectionId = 0
                        isRepeat = False
                    else:
                        isRepeat = True
                    break

            if not isRepeat:
                self.selectionData[self.teams[playerId]][playerId][1] = selectionId

            if self.phase == 0 and not c.debugMode:
                self.ShowPrepSelectionScreen(True, True)
            else:
                self.ShowPrepSelectionScreen(False, True)

        elif operation == 'kickOut':
            playerId = data['playerId']

            lobbyGameApi.TryToKickoutPlayer(playerId, "§6与服务器断开连接")

        elif operation == 'fixWeapon':
            print 'fixWeapon req rcv'

            if data['stage'] == 'start':
                comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
                comp.ChangeSelectSlot(4)
                self.sendMsg('§e正在修复武器...', playerId)
                self.playerIsFixing[playerId] = True
            elif data['stage'] == 'finish':
                comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
                comp.ChangeSelectSlot(self.playerEquips[playerId] - 1)
                self.sendMsg('§a武器修复完成', playerId)
                self.playerIsFixing[playerId] = False

                if self.playerEquips[playerId] == 1:
                    self.playerKits[playerId][1][1] = 20
                else:
                    weaponData = self.playerKits[playerId][2][0]
                    print 'weaponData is', weaponData
                    if 'shield' in weaponData:
                        slot2Dur = 10
                    elif 'bow/1' in weaponData:
                        slot2Dur = 2
                        itemDict = {
                            'itemName': 'minecraft:arrow',
                            'count': 64,
                            'auxValue': 22
                        }
                        for i in range(5):
                            serverApi.GetEngineCompFactory().CreateItem(playerId).SpawnItemToPlayerInv(itemDict, playerId, i+9)
                    elif 'bow' in weaponData:
                        slot2Dur = 15
                        itemDict = {
                            'itemName': 'minecraft:arrow',
                            'count': 64,
                            'auxValue': 0
                        }
                        for i in range(5):
                            serverApi.GetEngineCompFactory().CreateItem(playerId).SpawnItemToPlayerInv(itemDict, playerId, i + 9)
                    else:
                        slot2Dur = 20
                    self.playerKits[playerId][2][1] = slot2Dur

                comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
                comp.SetItemDurability(serverApi.GetMinecraftEnum().ItemPosType.INVENTORY, self.playerEquips[playerId] - 1, 99999)

                self.UpdateKitDurability(playerId)

        elif operation == 'equipWeapon':

            if self.playerIsFixing[playerId]:
                self.sendMsg('§c正在修复武器，不能装备', playerId)
                return

            equipId = data['equipId']
            self.playerEquips[playerId] = equipId

            comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
            comp.ChangeSelectSlot(4)
            def a():
                comp.ChangeSelectSlot(self.playerEquips[playerId] - 1)
            commonNetgameApi.AddTimer(1.5, a)

        elif operation == 'useSkill':

            # Structure:
            # playerKits{
            #     playerId: {
            #         slotId: ['itemId', usesLeft]
            #     }
            # }

            if self.playerIsFixing[playerId]:
                self.sendMsg('§c正在修复武器，不能使用', playerId)
                return

            skillName = self.playerKits[playerId][3][0]
            usesLeft = self.playerKits[playerId][3][1]

            if usesLeft <= 0:
                return

            comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
            comp.ChangeSelectSlot(4)

            # main skill handle
            def a():
                skillMgr.DoSkill(playerId, skillName, self.teams, self.roundSiteIndex, self.playerEquips[playerId])
                comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
                comp.ChangeSelectSlot(self.playerEquips[playerId] - 1)


            commonNetgameApi.AddTimer(1.0, a)

            self.playerKits[playerId][3][1] -= 1
            self.UpdateKitDurability(playerId)

        elif operation == 'defuserPlant':
            if data['stage'] == 'start':
                self.StartDefuserPlant()
            elif data['stage'] == 'finish':
                for player in serverApi.GetPlayerList():
                    self.sendTitle('§l拆弹器已部署', 1, player)
                    self.playerNearSite[player] = True
                    response = {
                        'isShow': False
                    }
                    self.NotifyToClient(player, 'ShowDefuserButtonsEvent', response)
            elif data['stage'] == 'stop':
                self.InterruptDefuserPlant()

        elif operation == 'defuserDestroy':
            print 'stage is', data['stage']
            if data['stage'] == 'start':
                self.StartDefuserDestroy()
            elif data['stage'] == 'finish':
                print 'defuser destroy finish'
                self.DefuserDestroySuccess()
                for player in serverApi.GetPlayerList():
                    response = {
                        'isShow': False
                    }
                    self.NotifyToClient(player, 'ShowDefuserButtonsEvent', response)
            elif data['stage'] == 'stop':
                self.InterruptDefuserDestroy()

    def OnCommand(self, data):
        data['cancel'] = True
        playerId = data['entityId']
        msg = data['command'].split()
        cmd = msg[0].strip('/')

        if cmd not in ['v5debug']:
            return

        if cmd == 'v5debug':
            flag = msg[1]
            keyword = msg[2]

            if flag == 'prep':
                if keyword == 'show':
                    self.ShowPrepSelectionScreen(True)
                elif keyword == 'init':
                    self.selectionData[0][playerId] = [0, 0]
                    self.teams[playerId] = 0
                elif keyword == 'set':
                    self.selectionData[0][1] = [int(msg[3]), int(msg[4])]
                    self.ShowPrepSelectionScreen(True, True)
                elif keyword == 'get':
                    print self.selectionData, self.teams
                    self.sendMsg(str(self.selectionData), playerId)
                elif keyword == 'exit':
                    self.ShowPrepSelectionScreen(False)

            elif flag == 'uiPos':
                data = {
                    'operation': 'uiDebug',
                    'x': int(msg[2]),
                    'y': int(msg[3])
                }
                self.NotifyToClient(playerId, 'DebugEvent', data)

            elif flag == 'defuser':
                if keyword == 'start':
                    self.StartDefuserPlant()
                elif keyword == 'show':
                    self.NotifyToClient(playerId, 'ShowTimerPanelEvent', (True, True))
                elif keyword == 'interrupt':
                    self.InterruptDefuserPlant()

            elif flag == 'timer':
                if keyword == 'start':
                    self.timerTicking = True
                elif keyword == 'stop':
                    self.timerTicking = False
                elif keyword == 'reset':
                    self.roundTimer = c.roundTime

            elif flag == 'eqp':
                if keyword == 'show':
                    self.NotifyToClient(playerId, 'ShowEqpPanelEvent', (True, True))
                elif keyword == 'set':
                    self.GivePlayerKit(playerId, int(msg[3]), int(msg[4]))

            elif flag == 'reinf':
                if keyword == 'show':
                    self.UpdateReinfCount(playerId, self.reinfLeft, True)
                elif keyword == 'init':
                    self.reinfLeft = 180
                    self.defenders.append(playerId)
                elif keyword == 'exit':
                    self.UpdateReinfCount(playerId, self.reinfLeft, False)

            elif flag == 'cmd':
                self.sendCmd(data['command'].replace('/v5debug cmd ', ''), playerId)

            elif flag == 'game':
                if keyword == 'start':
                    self.status = 1
                elif keyword == 'stop':
                    self.status = 0

            elif flag == 'plant':
                if keyword == 'init':
                    self.sendMsg('exec', playerId)
                    self.phase = 2
                    self.defuserCarrier = playerId
                    self.currentSite = [(int(msg[3]), int(msg[4]), int(msg[5])), (int(msg[3]), int(msg[4]), int(msg[5]))]
                    self.sendCmd('/setblock ~~~ v5:bomb', playerId)
                    self.sendMsg('suc', playerId)

    # ################## UI INTERFACES #####################
    u"""
        This section contains UI interface functions.
        Complete development of this section before moving on to server code.
    """

    def ShowPrepSelectionScreen(self, isShow, isUpdate=False, playerLi=None):
        print 'showprep req'

        if playerLi:
            li = playerLi
        else:
            li = serverApi.GetPlayerList()

        for player in li:
            # TODO remove debug
            if player in self.teams or True:
                response = {
                    'isShow': isShow,
                    'isUpdate': isUpdate,
                    'selections': self.selectionData[self.teams[player]]
                }
                print 'send showprep'
                self.NotifyToClient(player, 'ShowPrepSelectionScreenEvent', response)

    def StartDefuserPlant(self):
        musicSystem = serverApi.GetSystem('music', 'musicSystem')
        self.defuserPlanting = False

        for player in serverApi.GetPlayerList():
            musicSystem.PlayMusicToPlayer(player, 'sfx.v5.plant', True)

        self.timers['defuserPlantTimer'] = commonNetgameApi.AddTimer(7.5, self.StartDefuserProgress)

        comp = serverApi.GetEngineCompFactory().CreatePlayer(self.defuserCarrier)
        comp.ChangeSelectSlot(4)

    def InterruptDefuserPlant(self):
        musicSystem = serverApi.GetSystem('music', 'musicSystem')

        self.defuserPlanting = False
        commonNetgameApi.CancelTimer(self.timers['defuserPlantTimer'])
        for player in serverApi.GetPlayerList():
            musicSystem.StopMusicById(player, 'sfx.v5.plant')

        comp = serverApi.GetEngineCompFactory().CreatePlayer(self.defuserCarrier)
        comp.ChangeSelectSlot(0)

    def StartDefuserProgress(self):
        self.defuserPlanted = True
        self.nextPhase()

        self.defuserPlanting = False
        self.defuserActive = True

        musicSystem = serverApi.GetSystem('music', 'musicSystem')
        for player in serverApi.GetPlayerList():
            musicSystem.PlayMusicToPlayer(player, 'sfx.v5.defuse', True)
            self.NotifyToClient(player, 'StartDefuserProgressEvent', None)

        if self.roundTimer <= 14:
            for player in serverApi.GetPlayerList():
                musicSystem.StopMusicById(player, 'sfx.v5.round.timeout')

        self.timers['defuserProgressTimer'] = commonNetgameApi.AddTimer(44.0, self.DefuserSuccess)

        comp = serverApi.GetEngineCompFactory().CreatePos(self.defuserCarrier)
        pos = comp.GetFootPos()
        self.defuserDropPos = pos
        self.sendCmd('/setblock ~~~ v5:defuser', self.defuserCarrier)
        comp = serverApi.GetEngineCompFactory().CreatePlayer(self.defuserCarrier)
        comp.ChangeSelectSlot(0)

        self.sendTitle('§l§e+200§r部署拆弹器', 3, self.defuserCarrier)
        self.pts[self.defuserCarrier] += 200

        self.defuserCarrier = None

    def DefuserSuccess(self):
        print '=== DEFUSE SUCCESS! ATK wins ==='
        # self.sendMsgToAll('Debug: Bomb has been defused. ATK wins')
        if self.defuserActive:
            self.defuserActive = False
            self.roundEnd(True)

    def StartDefuserDestroy(self):

        if self.defuserDestroying:
            print 'invalid StartDefuserDestroy!!! Destroy already in progress'
            return

        musicSystem = serverApi.GetSystem('music', 'musicSystem')
        self.defuserDestroying = True

        for player in serverApi.GetPlayerList():
            musicSystem.PlayMusicToPlayer(player, 'sfx.v5.counter-defuse', True)

    def InterruptDefuserDestroy(self):
        musicSystem = serverApi.GetSystem('music', 'musicSystem')

        self.defuserDestroying = False
        for player in serverApi.GetPlayerList():
            musicSystem.StopMusicById(player, 'sfx.v5.counter-defuse')

    def DefuserDestroySuccess(self):
        print 'defuser destroyed'
        musicSystem = serverApi.GetSystem('music', 'musicSystem')

        self.defuserDestroying = False
        self.defuserActive = False
        for player in serverApi.GetPlayerList():
            musicSystem.StopMusicById(player, 'sfx.v5.counter-defuse')
        self.roundEnd(False)
    
    def GivePlayerKit(self, playerId, weaponId, skillId):
        weaponData = c.weaponPresets[weaponId]
        skillData = c.skillPresets[skillId]

        self.playerKits[playerId] = {}
        self.playerKits[playerId][1] = [weaponData[0], 20]

        if 'shield' in weaponData[1]:
            slot2Dur = 10
        elif 'bow/1' in weaponData[1]:
            slot2Dur = 2
        elif 'bow' in weaponData[1]:
            slot2Dur = 15
        else:
            slot2Dur = 20
        self.playerKits[playerId][2] = [weaponData[1], slot2Dur]
        self.playerKits[playerId][3] = [skillData[0], skillData[1]]

        print 'playerdata is', self.playerKits[playerId]

        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        itemData = weaponData[0].split('/')
        itemDict = {
            'itemName': 'minecraft:%s' % itemData[0],
            'count': 1,
            'auxValue': 0
        }
        if len(itemData) > 1:
            itemDict['enchantData'] = [(12, int(itemData[1]))]
        comp.SpawnItemToPlayerInv(itemDict, playerId, 0)

        itemData = weaponData[1].split('/')
        if 'sword' in weaponData[1]:
            itemDict = {
                'itemName': 'minecraft:%s' % itemData[0],
                'count': 1,
                'auxValue': 0
            }
            if len(itemData) > 1:
                itemDict['enchantData'] = [(12, int(itemData[1]))]
            comp.SpawnItemToPlayerInv(itemDict, playerId, 1)
        elif 'bow' in weaponData[1]:
            if len(itemData) > 1:
                itemDict = {
                    'itemName': 'minecraft:arrow',
                    'count': 64,
                    'auxValue': 22
                }
            else:
                itemDict = {
                    'itemName': 'minecraft:arrow',
                    'count': 64,
                    'auxValue': 0
                }
            for i in range(5):
                comp.SpawnItemToPlayerInv(itemDict, playerId, i + 9)

            itemDict = {
                'itemName': 'minecraft:bow',
                'count': 1,
                'auxValue': 0
            }
            comp.SpawnItemToPlayerInv(itemDict, playerId, 1)
        elif 'shield' in weaponData[1]:
            itemDict = {
                'itemName': 'minecraft:shield',
                'count': 1,
                'auxValue': 0
            }
            comp.SpawnItemToPlayerInv(itemDict, playerId, 1)

        self.NotifyToClient(playerId, 'SetEqpDataEvent', self.playerKits[playerId])

        self.OnClientAction({
            'operation': 'equipWeapon',
            'equipId': 1,
            'playerId': playerId
        })

        self.playerEquips[playerId] = 1

        armorKeyword = c.armorPresets[weaponId]
        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        if armorKeyword != 'none':
            itemDict = {
                'itemName': 'minecraft:%s_helmet' % armorKeyword,
                'count': 1
            }
            comp.SpawnItemToArmor(itemDict, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.HEAD)
            itemDict = {
                'itemName': 'minecraft:%s_chestplate' % armorKeyword,
                'count': 1
            }
            comp.SpawnItemToArmor(itemDict, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.BODY)
            itemDict = {
                'itemName': 'minecraft:%s_leggings' % armorKeyword,
                'count': 1
            }
            comp.SpawnItemToArmor(itemDict, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.LEG)
            itemDict = {
                'itemName': 'minecraft:%s_boots' % armorKeyword,
                'count': 1
            }
            comp.SpawnItemToArmor(itemDict, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.FOOT)
        else:
            itemDict = {
                'itemName': 'minecraft:air',
                'count': 1
            }
            comp.SpawnItemToArmor(itemDict, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.HEAD)
            itemDict = {
                'itemName': 'minecraft:air',
                'count': 1
            }
            comp.SpawnItemToArmor(itemDict, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.BODY)
            itemDict = {
                'itemName': 'minecraft:air',
                'count': 1
            }
            comp.SpawnItemToArmor(itemDict, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.LEG)
            itemDict = {
                'itemName': 'minecraft:air',
                'count': 1
            }
            comp.SpawnItemToArmor(itemDict, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.FOOT)

    def UpdateKitDurability(self, playerId):
        response = {
            1: self.playerKits[playerId][1],
            2: self.playerKits[playerId][2],
            3: self.playerKits[playerId][3],
            'selected': self.playerEquips[playerId]
        }
        self.NotifyToClient(playerId, 'UpdateKitDurabilityEvent', response)

        if 'shield' in self.playerKits[playerId][2][0] and self.playerKits[playerId][2][1] <= 0:
            itemDict = {
                'itemName': 'minecraft:deadbush',
                'count': 1
            }
            comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
            comp.SpawnItemToPlayerInv(itemDict, playerId, 1)

    def UpdateReinfCount(self, playerId, count, isShow=True):
        self.reinfLeft = count
        data = {
            'count': count,
            'isShow': isShow
        }
        self.NotifyToClient(playerId, 'UpdateReinfPanelEvent', data)

        if self.reinfLeft > 0:
            def a(p):
                if self.phase == 1 and (self.reinfLeft % 20 == 0 or self.reinfLeft < 30):
                    self.sendCmd('/replaceitem entity @s slot.hotbar 0 destroy v5:hard_wall 10 0 {"minecraft:can_place_on":{"blocks":["concrete"]}}', p)
            commonNetgameApi.AddTimer(0.05, a, playerId)
            comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
            comp.ChangeSelectSlot(0)
        else:
            self.sendCmd('/clear @s v5:hard_wall', playerId)

    def DropDefuser(self, isElimination=False):
        if not self.defuserDropPos and self.defuserCarrier:
            self.sendCmd('/setblock ~~~ v5:defuser', self.defuserCarrier)
            comp = serverApi.GetEngineCompFactory().CreatePos(self.defuserCarrier)
            self.defuserDropPos = comp.GetFootPos()
            self.defuserCarrier = None

            if self.phase == 2:
                if isElimination:
                    for player in self.attackers:
                        self.sendTitle('§l拆弹器已被放下', 2, player)
                else:
                    for player in self.attackers:
                        self.sendTitle('§l拆弹器已被放下', 1, player)
                        self.sendTitle('§e坐标 %s %s %s' % (int(self.defuserDropPos[0]), int(self.defuserDropPos[1]), int(self.defuserDropPos[2])), 2, player)

                for player in self.attackers:
                    self.sendMsg('§l§e拆弹器已被放下，坐标为 §6%s %s %s' % (int(self.defuserDropPos[0]), int(self.defuserDropPos[1]), int(self.defuserDropPos[2])), player)

    def PickupDefuser(self, playerId):
        if self.defuserDropPos and not self.defuserCarrier and playerId in self.attackers:
            for player in self.attackers:
                self.sendTitle('§l拆弹器已被捡起', 2, player)
                self.sendTitle('§e坐标 %s %s %s' % (int(self.defuserDropPos[0]), int(self.defuserDropPos[1]), int(self.defuserDropPos[2])), 2, player)
                self.sendMsg('§e§l%s捡起了拆弹器' % lobbyGameApi.GetPlayerNickname(playerId), player)

            blockDict = {
                'name': 'minecraft:air',
                'aux': 0
            }
            comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
            comp.SetBlockNew(self.defuserDropPos, blockDict, 0, 0)

            self.defuserDropPos = ()
            self.defuserCarrier = playerId

    def forceSelect(self):
        # Structure:
        # selectionData{
        #     team: {
        #         player: [weaponSelectionId, skillSelectionId]
        #     }
        # }
        for team in self.selectionData:
            for player in self.selectionData[team]:
                selections = self.selectionData[team][player]
                if selections[0] == 0:
                    for i in range(1, 6):
                        isRepeat = False
                        for player2 in self.selectionData[team]:
                            if player2 != player and self.selectionData[team][player2][0] == i:
                                isRepeat = True
                                break
                        if not isRepeat:
                            self.selectionData[team][player][0] = i
                            break

                if selections[1] == 0:
                    for i in range(1, 6):
                        isRepeat = False
                        for player2 in self.selectionData[team]:
                            if player2 != player and self.selectionData[team][player2][1] == i:
                                isRepeat = True
                                break
                        if not isRepeat:
                            self.selectionData[team][player][1] = i
                            break


    # ################# TICK TIMERS ###############
    u"""
        This section contains all the timers
    """

    def roundTick(self):
        if self.timerTicking and not self.defuserPlanted and self.roundTimer > 0 and self.phase < 4:
            self.roundTimer -= 1
            for player in serverApi.GetPlayerList():
                self.NotifyToClient(player, 'TimerUpdateEvent', str(datetime.timedelta(seconds=int(self.roundTimer))))

            if self.roundTimer == 13  and self.phase == 2:
                musicSystem = serverApi.GetSystem('music', 'musicSystem')
                for player in self.teams:
                    musicSystem.PlayMusicToPlayer(player, 'sfx.v5.round.timeout', True)

            if self.roundTimer == 0:
                self.nextPhase()
                return

            if self.phase == 1:
                self.ShowPrepSelectionScreen(False, True)

    # ################# SERVER CODE ###############
    u"""
        Starting in this section are the server codes
    """

    def OnPlayerInventoryOpenScriptServer(self, data):
        playerId = data['playerId']

        # lobbyGameApi.TryToKickoutPlayer(playerId, "§6与服务器断开连接")

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


    def OnOnCarriedNewItemChangedServer(self, data):
        playerId = data['playerId']
        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        newSlotId = comp.GetSelectSlotId()
        oldSlotId = self.playerEquips[playerId] - 1
        if newSlotId != oldSlotId and newSlotId != 4:
            comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
            comp.ChangeSelectSlot(oldSlotId)

    def OnServerEntityTryPlaceBlock(self, data):
        playerId = data['entityId']
        if data['fullName'] == 'v5:hard_wall':
            if self.reinfLeft <= 0:
                data['cancel'] = True
            else:
                self.reinfLeft -= 1
                self.sendTitle('§l§e+2 §r加固墙', 3, playerId)
                self.pts[playerId] += 2
            for player in self.defenders:
                self.UpdateReinfCount(player, self.reinfLeft)

    def OnPlayerAttackEntity(self, data):
        playerId = data['playerId']
        victimId = data['victimId']
        dmg = data['damage']
        def doFriendlyFireWarning():
            if self.teams[playerId] == self.teams[victimId]:
                self.sendTitle('', 1, playerId)
                self.sendTitle('§l§c不要攻击你的队友！', 2, playerId)
                self.sendTitle('§l§4-5 §r友伤', 1, playerId)
                self.pts[playerId] -= 5

        if self.status == 0:
            data['cancel'] = True

        elif self.status == 1:

            if self.playerIsFixing[playerId]:
                return

            if not self.alive[victimId] or not self.alive[playerId]:
                data['cancel'] = True
                return

            if self.teams[playerId] == self.teams[victimId] and self.rff[playerId]:
                print 'deal rff'
                data['cancel'] = True
                comp = serverApi.GetEngineCompFactory().CreateHurt(playerId)
                comp.Hurt(8, serverApi.GetMinecraftEnum().ActorDamageCause.EntityAttack, playerId, None, True)

            if victimId in serverApi.GetPlayerList():
                opponentComp = serverApi.GetEngineCompFactory().CreateItem(victimId)
                opponentCarried = opponentComp.GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0)
                if opponentCarried:
                    opponentItemName = opponentCarried['itemName']
                else:
                    opponentItemName = 'minecraft:air'
            else:
                opponentItemName = 'none'

            print 'opponentItem', opponentItemName
            try:
                durability = self.playerKits[playerId][self.playerEquips[playerId]][1]
            except KeyError:
                durability = 1
            if durability <= 0:
                data['cancel'] = True

            elif 'shield' in opponentItemName and victimId in serverApi.GetPlayerList():
                # data['cancel'] = True
                print 'shield attack, playerKits=', self.playerKits[victimId]
                self.playerKits[victimId][2][1] -= 1
                self.UpdateKitDurability(victimId)
                return
            else:
                comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
                carried = comp.GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0)
                itemName = carried['itemName']

                if 'sword' in itemName:
                    data['isKnockBack'] = '/' in itemName
                    self.playerKits[playerId][self.playerEquips[playerId]][1] -= 1
                    doFriendlyFireWarning()
                elif 'bow' in itemName:
                    data['cancel'] = True
                    print 'bow hit'
                    comp = serverApi.GetEngineCompFactory().CreateHurt(victimId)
                    comp.Hurt(1, serverApi.GetMinecraftEnum().ActorDamageCause.EntityAttack, playerId, None, False)
                    self.playerKits[playerId][self.playerEquips[playerId]][1] -= 1
                    print self.playerKits[playerId]

                elif 'shield' in itemName:
                    self.playerKits[playerId][self.playerEquips[playerId]][1] -= 2

                for slot in self.playerKits[playerId]:
                    if self.playerKits[playerId][slot][1] <= 0:
                        self.playerKits[playerId][slot][1] = 0
                        self.sendCmd('/clear @s arrow', playerId)

            self.UpdateKitDurability(playerId)

    def OnPlayerRespawnFinishServer(self, data):
        playerId = data['playerId']
        if not c.debugMode:

            self.sendTitle('§l§c您已阵亡', 1, playerId)
            self.sendTitle('等待下一局复活', 2, playerId)
            self.NotifyToClient(playerId, 'ShowEqpPanelEvent', (False, True))

    def OnActorUseItemServer(self, data):
        playerId = data['playerId']
        useMethod = data['useMethod']
        if useMethod == 5:
            print 'bow shot'
            self.playerKits[playerId][self.playerEquips[playerId]][1] -= 1
            if self.playerKits[playerId][2][1] <= 0:
                self.sendCmd('/clear @s arrow', playerId)
            self.UpdateKitDurability()

    def OnServerChat(self, data):
        playerId = data['playerId']
        nickname = data['username']
        msg = data['message']

        data['cancel'] = True

        if not commonNetgameApi.CheckWordsValid(msg):
            self.sendMsg('§3不允许发送该消息，请检查', playerId)
            return

        replaceSystem = serverApi.GetSystem('replaceWords', 'replaceWordsSystem')
        if playerId in replaceSystem.db:
            db = replaceSystem.db[playerId]
        else:
            db = None

        if self.status == 0:
            msg = db[0] + db[1] + "§r§3" + nickname + ": §7" + db[2] + msg
            self.sendMsgToAll(msg)

        elif self.status >= 1:
            if self.alive[playerId]:
                isShout = bool(msg[0] == '!' or msg[0] == '！')
                teamName = c.teamNames[self.teams[playerId]]

                if isShout:
                    msg = "§r§b[全体]§r§e" + nickname + ": §f" + db[2] + msg
                    self.sendMsgToAll(msg)
                else:
                    msg = "§r§b[队伍]§6" + nickname + ": §f " + db[2] + msg
                    for player in self.teams:
                        if self.teams[player] == self.teams[playerId]:
                            self.sendMsg(msg, player)
            else:
                msg = "[观战]§3" + nickname + ": §7" + msg
                self.sendMsgToAll(msg)

    def HudPlayerDeathEvent(self, data):
        playerId = data['playerId']
        attackerId = data['attackerId']

        # ➔
        self.ElimPlayer(playerId)

        musicSystem = serverApi.GetSystem('music', 'musicSystem')
        for player in serverApi.GetPlayerList():
            musicSystem.PlayMusicToPlayer(player, 'sfx.v5.elim', True)

        self.kd[playerId][1] += 1
        if attackerId in self.teams and self.teams[playerId] != self.teams[attackerId] and playerId != attackerId:
            self.kd[attackerId][0] += 1
            self.sendTitle('§l§e+100 §r解决一名敌人的奖励', 3, playerId)
            self.pts[attackerId] += 100

        elif self.teams[playerId] == self.teams[attackerId]:
            self.sendTitle('§l§4-100 §r击杀队友', 3, playerId)
            self.pts[attackerId] -= 100

            if not self.rff[playerId] and playerId != attackerId:
                self.sendMsgToAll('§l%s的反向友伤已开启' % lobbyGameApi.GetPlayerNickname(attackerId))
                def a():
                    self.sendTitle('§l§4反向友伤已开启', 1, attackerId)
                    self.sendTitle('您对队友造成的伤害将被反弹', 2, attackerId)
                commonNetgameApi.AddTimer(1.0, a)
                self.rff[attackerId] = True

        teamsColorCode = {
            0: '§b',
            1: '§6'
        }
        for player in serverApi.GetPlayerList():
            if attackerId in self.teams:
                msg = '§l%s%s §f➔ %s%s' % (
                    teamsColorCode[self.teams[attackerId]],
                    lobbyGameApi.GetPlayerNickname(attackerId),
                    teamsColorCode[self.teams[playerId]],
                    lobbyGameApi.GetPlayerNickname(playerId)
                )
                self.sendMsg(msg, player)
            else:
                msg = '§l§f➔ %s%s' % (
                    teamsColorCode[self.teams[playerId]],
                    lobbyGameApi.GetPlayerNickname(playerId)
                )
                self.sendMsg(msg, player)

    def OnExplosionServer(self, data):
        victims = data['victims']
        pos = data['explodePos']
        blocks = data['blocks']

        for blockData in data['blocks']:
            comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
            blockName = comp.GetBlockNew((blockData[0], blockData[1], blockData[2]), 0)['name']

            if blockName.replace('minecraft:', '') not in c.breakableBlocks:
                blockData[3] = True

    def OnDamage(self, data):
        playerId = data['entityId']
        srcId = data['srcId']
        projId = data['projectileId']
        cause = data['cause']

        if cause == 'entity_explosion':
            print 'explosion dmg', data['damage']
            data['damage'] = 0
            comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
            tPos = comp.GetPos()
            comp = serverApi.GetEngineCompFactory().CreatePos(srcId)
            sPos = comp.GetPos()
            comp = serverApi.GetEngineCompFactory().CreatePos(projId)
            jPos = comp.GetPos()
            distance = self.dist(tPos[0], tPos[1], tPos[2], sPos[0], sPos[1], sPos[2])

            # print 'dist', distance
            damageDict = c.explosionDamageSetting

            for dist in damageDict:
                if distance <= dist:
                    print 'damage', damageDict[dist]
                    comp = serverApi.GetEngineCompFactory().CreateHurt(playerId)
                    comp.Hurt(damageDict[dist], serverApi.GetMinecraftEnum().ActorDamageCause.EntityAttack, srcId, None, False)
                    break

            if jPos:
                jDistance = self.dist(tPos[0], tPos[1], tPos[2], jPos[0], jPos[1], jPos[2])
                for dist in damageDict:
                    if jDistance <= dist:
                        print 'damage', damageDict[dist]
                        comp = serverApi.GetEngineCompFactory().CreateHurt(playerId)
                        comp.Hurt(damageDict[dist], serverApi.GetMinecraftEnum().ActorDamageCause.EntityAttack, srcId, None, False)
                        break

        elif cause == 'fall':
            dmg = data['damage']

            if dmg >= 4.5:
                self.sendCmd('/kill', playerId)
            else:
                data['damage'] = 0

    def OnScriptTickServer(self):
        if self.status == 0:
            pass
        elif self.status == 1:
            if self.currentSite and self.phase == 2:

                if self.defuserCarrier:
                    player = self.defuserCarrier
                    comp = serverApi.GetEngineCompFactory().CreatePos(player)
                    pos = comp.GetFootPos()
                    dist = [self.dist(pos[0], pos[1], pos[2], self.currentSite[0][0], self.currentSite[0][1], self.currentSite[0][2]), self.dist(pos[0], pos[1], pos[2], self.currentSite[1][0], self.currentSite[1][1], self.currentSite[1][2])]
                    # print 'dist is', dist
                    # return

                    if not self.playerNearSite[player] and (dist[0] < 5 or dist[1] < 5):
                        self.playerNearSite[player] = True
                        response = {
                            'isShow': True,
                            'type': 'plant'
                        }
                        self.NotifyToClient(player, 'ShowDefuserButtonsEvent', response)
                        # print 'notify 1'
                    if self.playerNearSite[player] and (dist[0] > 5 or dist[1] > 5):
                        response = {
                            'isShow': False
                        }
                        self.NotifyToClient(player, 'ShowDefuserButtonsEvent', response)
                        # print 'notify 2'
                        self.playerNearSite[player] = False
                else:
                    for player in self.attackers:
                        comp = serverApi.GetEngineCompFactory().CreatePos(player)
                        pos = comp.GetFootPos()
                        dist = self.dist(pos[0], pos[1], pos[2], self.defuserDropPos[0], self.defuserDropPos[1], self.defuserDropPos[2])

                        if dist <= 1 and self.alive[player]:
                            self.PickupDefuser(player)

            elif self.phase == 3:
                for player in self.attackers:
                    if self.playerNearSite[player]:
                        self.playerNearSite[player] = False

                for player in self.defenders:
                    comp = serverApi.GetEngineCompFactory().CreatePos(player)
                    pos = comp.GetFootPos()
                    dist = [self.dist(pos[0], pos[1], pos[2], self.currentSite[0][0], self.currentSite[0][1],
                                      self.currentSite[0][2]),
                            self.dist(pos[0], pos[1], pos[2], self.currentSite[1][0], self.currentSite[1][1],
                                      self.currentSite[1][2])]
                    # print 'dist is', dist

                    if not self.playerNearSite[player] and (dist[0] < 5 or dist[1] < 5):
                        self.playerNearSite[player] = True
                        response = {
                            'isShow': True,
                            'type': 'defuse'
                        }
                        self.NotifyToClient(player, 'ShowDefuserButtonsEvent', response)
                        # print 'notify 1'
                    if self.playerNearSite[player] and (dist[0] > 5 or dist[1] > 5):
                        response = {
                            'isShow': False
                        }
                        self.NotifyToClient(player, 'ShowDefuserButtonsEvent', response)
                        # print 'notify 2'
                        self.playerNearSite[player] = False

    def ElimPlayer(self, playerId):
        self.alivePlayers[self.teams[playerId]] -= 1
        self.alive[playerId] = False

        if self.alivePlayers[0] <= 0:
            print 'roundend trig 1'
            self.roundEnd(True)
        elif self.alivePlayers[1] <= 0 and self.phase == 2:
            print 'roundend trig 2'
            self.roundEnd(False)
        else:
            for player in self.attackers:
                if player != playerId:
                    self.sendTitle('§l%s VS %s' % (self.alivePlayers[1], self.alivePlayers[0]), 1, player)
            for player in self.defenders:
                if player != playerId:
                    self.sendTitle('§l%s VS %s' % (self.alivePlayers[0], self.alivePlayers[1]), 1, player)

        if playerId == self.defuserCarrier:
            self.DropDefuser(True)

    def newRoundInit(self):
        musicSystem = serverApi.GetSystem('music', 'musicSystem')
        self.roundTimer = c.roundTime
        self.defuserPlanting = False
        self.defuserActive = False
        self.defuserDestroying = False
        self.roundTimer = c.roundTime
        self.defuserPlanted = False
        self.timerTicking = False
        self.currentSite = []
        self.reset_selectionData()
        if self.defuserDropPos:
            blockDict = {
                'name': 'minecraft:air',
                'aux': 0
            }
            # 不依赖playerId举例，支持常加载区块
            comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
            comp.SetBlockNew(self.defuserDropPos, blockDict, 0, 0)
        self.defuserDropPos = ()

        if self.wins[0] >= 3 or self.wins[1] >= 3:
            return

        # self.playerEquips[playerId] = 0
        # self.playerIsFixing[playerId] = False
        # self.playerNearSite[playerId] = False
        for player in self.teams:
            self.playerEquips[player] = 0
            self.playerIsFixing[player] = False
            self.playerNearSite[player] = False

            self.NotifyToClient(player, 'ResetEvent', None)

            self.alive[player] = True

            musicSystem.PlayMusicToPlayer(player, 'sfx.v5.game.start', True)

        self.roundTimer = 0
        self.phase = 0
        self.roundSiteIndex = random.randint(0, c.totalSites - 1)
        self.alivePlayers = {
            0: self.getCountInDict(0, self.teams),
            1: self.getCountInDict(1, self.teams)
        }

        comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
        for pos in c.mapBlockers:
            comp.SetBlockNew(pos, {
                'name': 'minecraft:bedrock'
            }, 0, 0)

        self.attackers = []
        self.defenders = []

        for player in self.teams:
            if self.teams[player] == 0:
                print 'append player to defenders'
                self.defenders.append(player)
            else:
                print 'append player to attackers'
                self.attackers.append(player)

            self.sendCmd('/effect @s instant_health 1 255 true', player)

        for player in self.defenders:
            self.setPos(player, c.defendersSpawn[self.roundSiteIndex])
        for player in self.attackers:
            self.setPos(player, c.attackersSpawn)

        print 'site index is', self.roundSiteIndex
        self.currentSite = [(c.bombSites[self.roundSiteIndex][0][0],
                            c.bombSites[self.roundSiteIndex][0][1],
                            c.bombSites[self.roundSiteIndex][0][2]),
                            (c.bombSites[self.roundSiteIndex][1][0],
                            c.bombSites[self.roundSiteIndex][1][1],
                            c.bombSites[self.roundSiteIndex][1][2])
                            ]

        for player in self.teams:
            self.sendTitle('§l第 %s 局' % self.roundNum, 1, player)
        for player in self.defenders:
            self.sendTitle('§l§6防守', 2, player)
        for player in self.attackers:
            self.sendTitle('§l§b进攻', 2, player)

        if self.wins[0] == 2 or self.wins[1] == 2:
            def a():
                if self.wins[0] == 2 and self.wins[1] == 2:
                    msg = '§lALL LAST'
                elif self.wins[0] == 2 or self.wins[1] == 2:
                    msg = '§l赛点'
                for player in self.teams:
                    self.sendTitle(msg, 1, player)
            commonNetgameApi.AddTimer(2.0, a)

        def b():
            # Start round setup
            self.roundTimer = c.phaseTimes[self.phase]
            self.reset_selectionData()
            self.timerTicking = True
            for player in self.teams:
                self.selectionData[self.teams[player]][player] = [0, 0]
                self.ShowPrepSelectionScreen(True)
                self.NotifyToClient(player, "ShowTimerPanelEvent", (True, True))
                musicSystem.PlayMusicToPlayer(player, 'sfx.v5.round.comm')
        commonNetgameApi.AddTimer(12.0, b)

        print ('teams, attackers, defenders', self.teams, self.attackers, self.defenders)

    def nextPhase(self):
        """
        Phases:
        0 = choose eqp
        1 = prep
        2 = battle
        3 = defuser planted
        """

        print 'prep phase finish'

        musicSystem = serverApi.GetSystem('music', 'musicSystem')

        if self.phase >= 3:
            return

        self.phase += 1
        self.roundTimer = c.phaseTimes[self.phase]

        if c.debugMode:
            return

        if self.phase == 1:
            utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
            for player in self.teams:
                self.ShowPrepSelectionScreen(False)

                self.sendTitle('§l交流阶段', 1, player)
                self.sendTitle('与队友沟通战术，并保护目标点', 2, player)

                musicSystem.PlayMusicToPlayer(player, 'sfx.v5.round.prep')

            self.forceSelect()

            sites = c.bombSites[self.roundSiteIndex][0]
            self.currentSite.append(sites)
            self.sendCmd('/setblock %s %s %s v5:bomb' % (sites[0], sites[1], sites[2]), self.defenders[0])
            sites = c.bombSites[self.roundSiteIndex][1]
            self.currentSite.append(sites)
            self.sendCmd('/setblock %s %s %s v5:bomb' % (sites[0], sites[1], sites[2]), self.defenders[0])

            for player in self.defenders:
                self.UpdateReinfCount(player, self.reinfLeft, True)

            self.defuserCarrier = random.choice(self.attackers)
            for player in self.attackers:
                if player == self.defuserCarrier:
                    self.sendMsg('§l§e你持有拆弹器。将其部署在任意目标点。', player)
                else:
                    self.sendMsg('§l§e%s持有拆弹器，将其护送至任意标点，并安全部署。' % lobbyGameApi.GetPlayerNickname(self.defuserCarrier), player)

            for player in self.teams:
                utilsSystem.SetHideName(player, True)

        elif self.phase == 2:
            for player in self.teams:
                self.sendTitle('§l行动阶段', 1, player)
            for player in self.defenders:
                self.sendTitle('消灭敌人或拆除已部署的拆弹器', 2, player)
            for player in self.attackers:
                self.sendTitle('消灭敌人或部署拆弹器', 2, player)

            for player in self.defenders:
                self.UpdateReinfCount(player, self.reinfLeft, False)
                self.sendCmd('/clear @s v5:hard_wall', player)

            print 'notify showeqp'
            for player in self.teams:
                self.NotifyToClient(player, 'ShowEqpPanelEvent', (True, True))

            for team in self.selectionData:
                for player in self.selectionData[team]:
                    self.GivePlayerKit(player, self.selectionData[team][player][0], self.selectionData[team][player][1])

            comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
            for pos in c.mapBlockers:
                comp.SetBlockNew(pos, {
                    'name': 'minecraft:air'
                }, 0, 0)

        elif self.phase == 3 and not self.defuserPlanted:
            self.roundEnd(False)

    def roundEnd(self, isAttackersWin):
        self.phase = 4
        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')

        for player in self.teams:
            self.NotifyToClient(player, 'ShowTimerPanelEvent', (False, True))
            self.sendCmd('/clear @s', player)
            self.sendCmd('/kill @e[type=item]', player)

            utilsSystem.SetHideName(player, False)

        if self.defuserDropPos:
            blockDict = {
                'name': 'minecraft:air',
                'aux': 0
            }
            # 不依赖playerId举例，支持常加载区块
            comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
            comp.SetBlockNew(self.defuserDropPos, blockDict, 0, 0)

        sites = c.bombSites[self.roundSiteIndex][0]
        self.currentSite.append(sites)
        self.sendCmd('/setblock %s %s %s air' % (sites[0], sites[1], sites[2]), self.defenders[0])
        sites = c.bombSites[self.roundSiteIndex][1]
        self.currentSite.append(sites)
        self.sendCmd('/setblock %s %s %s air' % (sites[0], sites[1], sites[2]), self.defenders[0])

        if self.defuserPlanted == True:
            self.defuserActive = False
            self.defuserPlanted = False
            musicSystem = serverApi.GetSystem('music', 'musicSystem')
            for player in serverApi.GetPlayerList():
                musicSystem.StopMusicById(player, 'sfx.v5.defuse')

        musicSystem = serverApi.GetSystem('music', 'musicSystem')

        if isAttackersWin:
            self.wins[1] += 1
            for player in self.attackers:
                self.sendTitle('§l§b第%s局胜利' % self.roundNum, 1, player)
                self.sendTitle('%s : %s' % (self.wins[1], self.wins[0]), 2, player)
                self.sendTitle('§l§e+200§r胜利', 3, player)
                musicSystem.PlayMusicToPlayer(player, 'sfx.v5.round.win')
                self.pts[player] += 200
            for player in self.defenders:
                self.sendTitle('§l§6第%s局落败' % self.roundNum, 1, player)
                self.sendTitle('%s : %s' % (self.wins[0], self.wins[1]), 2, player)
                musicSystem.PlayMusicToPlayer(player, 'sfx.v5.round.loss')
        else:
            self.wins[0] += 1
            for player in self.defenders:
                self.sendTitle('§l§b第%s局胜利' % self.roundNum, 1, player)
                self.sendTitle('%s : %s' % (self.wins[0], self.wins[1]), 2, player)
                self.sendTitle('§l§e+200§r胜利', 3, player)
                musicSystem.PlayMusicToPlayer(player, 'sfx.v5.round.win')
                self.pts[player] += 200
            for player in self.attackers:
                self.sendTitle('§l§6第%s局落败' % self.roundNum, 1, player)
                self.sendTitle('%s : %s' % (self.wins[1], self.wins[0]), 2, player)
                musicSystem.PlayMusicToPlayer(player, 'sfx.v5.round.loss')

        if self.wins[0] >= 3 or self.wins[1] >= 3:
            print 'winning'
            if self.wins[0] >= 3:
                self.win(0)
            else:
                self.win(1)
            return

        if self.roundNum == 2:
            for player in self.teams:
                if self.teams[player] == 0:
                    self.teams[player] = 1
                else:
                    self.teams[player] = 0

            winsDict = []
            for i in range(2):
                winsDict.append(self.wins[i])
            self.wins[0] = winsDict[1]
            self.wins[1] = winsDict[0]

            self.reinfLeft = 180

        def a():
            self.newRoundInit()
        commonNetgameApi.AddTimer(10.0, a)

        self.roundNum += 1

    def tick(self):
        count = len(serverApi.GetPlayerList())

        if self.status == 0:
            print 'countdown=%s' % self.countdown
            self.roundTimer = c.roundTime
            self.phase = 0
            enough = c.enoughPlayers
            if count < c.startCountdown:
                pass
            elif c.startCountdown <= count <= enough:
                self.countdown -= 1
                for player in serverApi.GetPlayerList():
                    self.sendTitle("§e§l%s" % self.countdown, 1, player)
                    self.sendTitle("游戏即将开始", 2, player)
            if count == enough and self.countdown > 15:
                self.countdown = 15
            if self.countdown < 60 and count < c.startCountdown:
                self.countdown = 60

                def a():
                    self.updateServerStatus(0, True)
                    rebootSystem = serverApi.GetSystem('reboot', 'rebootSystem')
                    rebootSystem.DoReboot(False)

                commonNetgameApi.AddTimer(2.0, a)
                self.sendMsgToAll("§c§l人数不够，比赛已被取消，请重新匹配")

            if self.countdown == 0:
                print 'starting!'
                self.start()
                self.status = 1

        if self.status == 1:
            for player in serverApi.GetPlayerList():
                self.sendCmd('/effect @s saturation 2 255 true', player)

            if self.phase == 2 and self.defuserCarrier:
                if self.defuserCarrier:
                    self.sendTitle('§e§l你持有拆弹器', 3, self.defuserCarrier)

                if self.defuserDropPos:
                    for player in self.attackers:
                        comp = serverApi.GetEngineCompFactory().CreatePos(player)
                        pos = comp.GetFootPos()
                        dist = self.dist(pos[0], pos[1], pos[2], self.defuserDropPos[0], self.defuserDropPos[1],
                                         self.defuserDropPos[2])

                        if dist <= 1:
                            self.PickupDefuser(player)

            if len(self.teams) <= 1 or len(self.attackers) < 1 or len(self.defenders) < 1:
                def a():
                    self.updateServerStatus(0, True)
                    rebootSystem = serverApi.GetSystem('reboot', 'rebootSystem')
                    rebootSystem.DoReboot(False)

                commonNetgameApi.AddTimer(2.0, a)
                self.sendMsgToAll("§c§l人数不够，比赛已被取消，请重新匹配")

        self.updateServerStatus(self.status)

    def boardTick(self):
        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        do = utilsSystem.TextBoard
        if self.status == 0:
            for player in serverApi.GetPlayerList():
                self.sendCmd('/gamerule sendcommandfeedback false', player)
                self.sendCmd('/gamerule showdeathmessages false', player)
                do(player, True, """
§e§lICE§a_§bGAME§r§l -> §c5v5

§7满%s人即可开始游戏§r
§l目前人数: §e%s人
§f倒计时: §c%s秒

§r§e在ICE_GAME体验5V5攻防战
§7%s
""" % (c.startCountdown, len(self.waiting), self.countdown, self.epoch2Datetime(time.time())))

        elif self.status == 1:
            for player in self.teams:
                extra = ""
                for otherPlayer in self.teams:
                    if self.teams[otherPlayer] == self.teams[player]:
                        if player == otherPlayer:
                            extra += '§l§e'

                        otherHp = serverApi.GetEngineCompFactory().CreateAttr(otherPlayer).GetAttrValue(serverApi.GetMinecraftEnum().AttrType.HEALTH)
                        if self.alive[otherPlayer]:
                            extra += '%s %sHP %s/%s §l§b%s PTS§r\n' % (lobbyGameApi.GetPlayerNickname(otherPlayer),
                                                               otherHp,
                                                               self.kd[otherPlayer][0],
                                                               self.kd[otherPlayer][1],
                                                               self.pts[otherPlayer]
                                                            )
                        else:
                            extra += '%s §l§cDEAD§r %s/%s §l§b%s PTS§r\n' % (lobbyGameApi.GetPlayerNickname(otherPlayer),
                                                                   self.kd[otherPlayer][0],
                                                                   self.kd[otherPlayer][1],
                                                                   self.pts[otherPlayer]
                                                                   )

                if self.rff[player]:
                    extra2 = '§r\n\n§l§4反向友伤已开启\n'
                else:
                    extra2 = '§r'

                if self.teams[player] == 0:
                    side = '§l§6防守方§r'
                else:
                    side = '§l§b进攻方§r'

                content = """
§e§lICE§a_§bGAME§r§l -> §c5V5§r

%s

§r你是%s
§f§l%s : %s%s

§r§e在ICE_GAME体验5V5攻防战
""" % (extra, side, self.wins[self.teams[player]], self.wins[abs(self.teams[player] - 1)], extra2)
                do(player, True, content)

    def win(self, winningTeamId):
        self.status = 2

        # totalList = []
        # for player in serverApi.GetPlayerList():
        #     totalList.append((lobbyGameApi.GetPlayerNickname(player),))
        # mysqlPool.AsyncExecutemanyWithOrderKey('bwconclusion', 'UPDATE bw SET total=total+1 WHERE uid=%s;', totalList)
        ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')
        for player in self.teams:
            if self.teams[player] == winningTeamId:
                self.sendTitle("§6§l胜利", 1, player)
                self.sendTitle("恭喜您获得胜利！！！", 2, player)
                self.sendMsg("§a+256NEKO §f获得胜利的奖励", player)
                mysqlPool.AsyncExecuteWithOrderKey('121doas9ps8dna9p8s', 'UPDATE bw SET win=win+1 WHERE uid=%s',
                                                   (player))


                ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(player), 256, '5v5 win')

        winner = self.rank(self.pts)
        ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(winner), 8, '5v5 mvp', True)
        self.sendMsg("§a+8CREDITS §f获得MVP的奖励", winner)

        # handle win sql
        # sql = 'UPDATE total SET total=total+1 WHERE uid=%s;'
        # mysqlPool.AsyncExecuteWithOrderKey('121doas9ps8dna9p8s', sql, totalList)
        # sql = 'UPDATE total SET win=win+1 WHERE uid=%s;'
        # mysqlPool.AsyncExecuteWithOrderKey('121doas9ps8ddna9p8s', sql, winningTeam)
        # over

        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        utilsSystem.ShowWinBanner(winner)
        sql = 'UPDATE bw SET mvp=mvp+1 WHERE uid=%s AND total>=mvp;'
        mysqlPool.AsyncExecuteWithOrderKey('asd8912381das', sql, (lobbyGameApi.GetPlayerUid(winner),))

        def a():
            self.status = 0
            self.updateServerStatus(self.status)

            rebootSystem = serverApi.GetSystem('reboot', 'rebootSystem')
            rebootSystem.DoReboot(False)

        commonNetgameApi.AddTimer(15.0, a)

    def start(self):
        musicSystem = serverApi.GetSystem('music', 'musicSystem')
        for player in self.waiting:
            self.pts[player] = 0
            self.rff[player] = False
            self.kd[player] = [0, 0]
            tCount = self.getCountInDict(0, self.teams)
            ctCount = self.getCountInDict(1, self.teams)
            if tCount == ctCount:
                self.teams[player] = random.randint(0, 1)
            elif tCount > ctCount:
                self.teams[player] = 1
            else:
                self.teams[player] = 0

            self.selectionData[self.teams[player]][player] = [0, 0]

            self.sendCmd('/spawnpoint @s %s %s %s' % (c.spectatorPos[0], c.spectatorPos[1], c.spectatorPos[2]), player)

        self.newRoundInit()
