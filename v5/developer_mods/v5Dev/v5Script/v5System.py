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
        self.defuserActive = False
        self.roundTimer = c.roundTime
        self.defuserPlanted = False
        self.timerTicking = False
        self.reinfLeft = 0

        self.teams = {}
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
        self.roundNum = 1
        self.roundSiteIndex = 0

        # 0=t, 1=ct

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self, self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self, self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(),"PlayerInventoryOpenScriptServerEvent", self, self.OnPlayerInventoryOpenScriptServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self, self.OnCommand)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnCarriedNewItemChangedServerEvent", self, self.OnOnCarriedNewItemChangedServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerAttackEntityEvent", self, self.OnPlayerAttackEntity)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerEntityTryPlaceBlockEvent", self, self.OnServerEntityTryPlaceBlock)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnScriptTickServer", self, self.OnScriptTickServer)

        # self.ListenForEvent('hud', 'hudClient', "DisplayDeathDoneEvent", self, self.OnDisplayDeathDone)
        # self.ListenForEvent('music', 'musicSystem', 'CreateMusicIdEvent', self, self.OnCreateMusicId)

        self.ListenForEvent('v5', 'v5Client', 'ActionEvent', self, self.OnClientAction)

        self.ListenForEvent('hud', 'hudSystem', 'PlayerDeathEvent', self, self.HudPlayerDeathEvent)

        commonNetgameApi.AddRepeatedTimer(1.0, self.roundTick)
        if not c.debugMode:
            commonNetgameApi.AddRepeatedTimer(1.0, self.tick)

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
            self.ShowPrepSelectionScreen(True, True)

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
            self.ShowPrepSelectionScreen(True, True)

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

    def InterruptDefuserPlant(self):
        musicSystem = serverApi.GetSystem('music', 'musicSystem')

        self.defuserPlanting = False
        commonNetgameApi.CancelTimer(self.timers['defuserPlantTimer'])
        for player in serverApi.GetPlayerList():
            musicSystem.StopMusicById(player, 'sfx.v5.plant')

    def StartDefuserProgress(self):
        self.defuserPlanting = False
        self.defuserActive = True
        musicSystem = serverApi.GetSystem('music', 'musicSystem')
        for player in serverApi.GetPlayerList():
            musicSystem.PlayMusicToPlayer(player, 'sfx.v5.defuse', True)
            self.NotifyToClient(player, 'StartDefuserProgressEvent', None)

        self.timers['defuserProgressTimer'] = commonNetgameApi.AddTimer(44.0, self.DefuserSuccess)

        comp = serverApi.GetEngineCompFactory().CreatePos(self.defuserCarrier)
        pos = comp.GetFootPos()
        self.defuserDropPos = pos
        self.sendCmd('/setblock ~~~ v5:defuser', self.defuserCarrier)
        self.defuserCarrier = None
        self.nextPhase()

    def DefuserSuccess(self):
        print '=== DEFUSE SUCCESS! ATK wins ==='
        self.sendMsgToAll('Debug: Bomb has been defused. ATK wins')
        self.defuserActive = False
    
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
            'equipId': 1
        })

    def UpdateKitDurability(self, playerId):
        response = {
            1: self.playerKits[playerId][1],
            2: self.playerKits[playerId][2],
            3: self.playerKits[playerId][3],
            'selected': self.playerEquips[playerId]
        }
        self.NotifyToClient(playerId, 'UpdateKitDurabilityEvent', response)

    def UpdateReinfCount(self, playerId, count, isShow=True):
        self.reinfLeft = count
        data = {
            'count': count,
            'isShow': isShow
        }
        self.NotifyToClient(playerId, 'UpdateReinfPanelEvent', data)

        if self.reinfLeft > 0:
            def a(p):
                self.sendCmd('/replaceitem entity @s slot.hotbar 0 destroy v5:hard_wall 10 0 {"minecraft:can_place_on":{"blocks":["concrete"]}}', p)
            commonNetgameApi.AddTimer(0.05, a, playerId)
            comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
            comp.ChangeSelectSlot(0)
        else:
            self.sendCmd('/clear @s v5:hard_wall', playerId)


    # ################# TICK TIMERS ###############
    u"""
        This section contains all the timers
    """

    def roundTick(self):
        if self.timerTicking and not self.defuserPlanted and self.roundTimer < 0 and self.phase < 4:
            self.roundTimer -= 1
            for player in serverApi.GetPlayerList():
                self.NotifyToClient(player, 'TimerUpdateEvent', str(datetime.timedelta(seconds=int(self.roundTimer))))

            if self.roundTimer == 0:
                self.nextPhase()
                return

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

        if self.status == 0:
            self.waiting.append(playerId)
        elif self.status == 1:
            lobbyGameApi.TryToKickoutPlayer(playerId, "§eMatch already started")

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        self.playerEquips.pop(playerId)
        self.playerIsFixing.pop(playerId)
        self.playerNearSite.pop(playerId)

        if self.status == 0:
            self.waiting.pop(self.waiting.index(playerId))
        elif self.status == 1:
            pass

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
            for player in self.defenders:
                self.UpdateReinfCount(player, self.reinfLeft)

    def OnPlayerAttackEntity(self, data):
        playerId = data['playerId']
        victimId = data['victimId']

        if self.status == 0:
            data['cancel'] = True

        elif self.status == 1:

            if self.playerIsFixing[playerId]:
                return

            if victimId in serverApi.GetPlayerList():
                opponentComp = serverApi.GetEngineCompFactory().CreateItem(victimId)
                opponentCarried = opponentComp.GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0)
                opponentItemName = opponentCarried['itemName']
            else:
                opponentItemName = 'none'

            durability = self.playerKits[playerId][self.playerEquips[playerId]][1]
            if durability <= 0:
                data['cancel'] = True

            elif 'shield' in opponentItemName and victimId in serverApi.GetPlayerList():
                data['cancel'] = True
                self.playerKits[victimId][self.playerEquips[victimId]][1] -= 1
            else:
                comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
                carried = comp.GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0)
                itemName = carried['itemName']

                if 'sword' in itemName:
                    data['isKnockBack'] = '/' in itemName
                    self.playerKits[playerId][self.playerEquips[playerId]][1] -= 1
                elif 'bow' in itemName:
                    data['cancel'] = True
                    print 'bow hit'
                    comp = serverApi.GetEngineCompFactory().CreateHurt(victimId)
                    comp.Hurt(1, serverApi.GetMinecraftEnum().ActorDamageCause.EntityAttack, playerId, None, False)
                    self.playerKits[playerId][self.playerEquips[playerId]][1] -= 1
                    print self.playerKits[playerId]

                for slot in self.playerKits[playerId]:
                    if self.playerKits[playerId][slot][1] <= 0:
                        self.playerKits[playerId][slot][1] = 0
                        self.sendCmd('/clear @s arrow', playerId)

            self.UpdateKitDurability(playerId)

    def HudPlayerDeathEvent(self, data):
        playerId = data['playerId']
        attackerId = data['attackerId']

        # ➔
        self.ElimPlayer(playerId)

        teamsColorCode = {
            0: '§b',
            1: '§6'
        }
        for player in serverApi.GetPlayerList():
            if attackerId in self.teams:
                msg = '§l%s%s §f➔ %s%s' % (
                    teamsColorCode[self.teams[attackerId]],
                    attackerId,
                    teamsColorCode[self.teams[playerId]],
                    playerId
                )
                self.sendMsg(msg, player)
            else:
                msg = '§l§f➔ %s%s' % (
                    teamsColorCode[self.teams[playerId]],
                    playerId
                )
                self.sendMsg(msg, player)

    def OnScriptTickServer(self):
        if self.status == 0:
            pass
        elif self.status == 1:
            if self.currentSite and self.phase == 2:
                for player in serverApi.GetPlayerList():
                    comp = serverApi.GetEngineCompFactory().CreatePos(player)
                    pos = comp.GetFootPos()
                    dist = self.dist(pos[0], pos[1], pos[2], self.currentSite[0][0], self.currentSite[0][1], self.currentSite[0][2]) or self.dist(pos[0], pos[1], pos[2], self.currentSite[1][0], self.currentSite[1][1], self.currentSite[1][2])
                    # print 'dist is', dist

                    if not self.playerNearSite[player] and dist < 5:
                        self.playerNearSite[player] = True
                        response = {
                            'isShow': True,
                            'type': 'plant'
                        }
                        self.NotifyToClient(player, 'ShowDefuserButtonsEvent', response)
                        # print 'notify 1'
                    if self.playerNearSite[player] and dist > 5:
                        response = {
                            'isShow': False
                        }
                        self.NotifyToClient(player, 'ShowDefuserButtonsEvent', response)
                        # print 'notify 2'
                        self.playerNearSite[player] = False

            if self.phase == 3:
                pass

    def ElimPlayer(self, playerId):
        self.alivePlayers[self.teams[playerId]] -= 1

        if self.alivePlayers[self.teams[playerId]] <= 0 and self.phase == 2:
            self.roundEnd(self.alivePlayers[0] <= 0)
        elif self.alivePlayers[0] <= 0 and self.phase == 3:
            self.roundEnd(True)
        else:
            for player in self.attackers:
                if player != playerId:
                    self.sendTitle('§l%s VS %s' % (self.alivePlayers[1], self.alivePlayers[0]), 1, playerId)
            for player in self.defenders:
                if player != playerId:
                    self.sendTitle('§l%s VS %s' % (self.alivePlayers[0], self.alivePlayers[1]), 1, playerId)

    def newRoundInit(self):
        self.roundTimer = c.roundTime
        self.defuserPlanting = False
        self.defuserActive = False
        self.roundTimer = c.roundTime
        self.defuserPlanted = False
        self.timerTicking = False
        self.currentSite = []
        self.reset_selectionData()
        self.defuserDropPos = ()

        # self.playerEquips[playerId] = 0
        # self.playerIsFixing[playerId] = False
        # self.playerNearSite[playerId] = False
        for player in self.teams:
            self.playerEquips[player] = 0
            self.playerIsFixing[player] = False
            self.playerNearSite = False

        self.roundTimer = 0
        self.phase = 0
        self.roundSiteIndex = random.randint(0, c.totalSites - 1)
        self.alivePlayers = {
            0: 5,
            1: 5
        }

        self.attackers = self.defenders = []

        for player in self.teams:
            if self.teams[player] == 0:
                self.defenders.append(player)
            else:
                self.attackers.append(player)

        for player in self.defenders:
            self.setPos(player, c.defendersSpawn[self.roundSiteIndex])
        for player in self.attackers:
            self.setPos(player, c.attackersSpawn)

        for player in self.teams:
            self.sendTitle('§l第 %s 局' % self.roundNum, 1, player)
        for player in self.defenders:
            self.sendTitle('§l§6防守', 2, player)
        for player in self.attackers:
            self.sendTitle('§l§b防守', 2, player)

        if self.wins[0] == 2 or self.wins[1] == 2:
            def a():
                if self.wins[0] == 2 and self.wins[1] == 2:
                    msg = '§l最终局'
                elif self.wins[0] == 2 or self.wins[1] == 2:
                    msg = '§l赛点'
                for player in self.teams:
                    self.sendTitle(msg, 1, player)
            commonNetgameApi.AddTimer(2.0, a)

        # Start round setup
        self.roundTimer = c.phaseTimes[self.phase]
        self.reset_selectionData()
        for player in self.teams:
            self.selectionData[self.teams[player]][player] = [0, 0]
            self.ShowPrepSelectionScreen(True)

    def nextPhase(self):
        """
        Phases:
        0 = choose eqp
        1 = prep
        2 = battle
        3 = defuser planted
        """

        print 'prep phase finish'

        if self.phase >= 2:
            return

        self.phase += 1
        self.roundTimer = c.phaseTimes[self.phase]

        if c.debugMode:
            return

        if self.phase == 1:
            for player in self.teams:
                self.ShowPrepSelectionScreen(False)

                self.sendTitle('§l交流阶段', 1, player)
                self.sendTitle('与队友沟通战术，并保护目标点', 2, player)

            sites = c.bombSites[self.roundSiteIndex][0]
            self.currentSite.append(sites)
            self.sendCmd('/setblock %s %s %s v5:bomb' % (sites[0], sites[1], sites[2]), self.defenders[0])
            sites = c.bombSites[self.roundSiteIndex][1]
            self.currentSite.append(sites)
            self.sendCmd('/setblock %s %s %s v5:bomb' % (sites[0], sites[1], sites[2]), self.defenders[0])

            self.reinfLeft = 180
            for player in self.defenders:
                self.UpdateReinfCount(player, self.reinfLeft, True)

        elif self.phase == 2:
            for player in self.teams:
                self.sendTitle('§l行动阶段', 1, player)
            for player in self.defenders:
                self.sendTitle('消灭敌人或拆除已部署的拆弹器', 2, player)
            for player in self.attackers:
                self.sendTitle('消灭敌人或部署拆弹器', 2, player)

            for team in self.selectionData:
                for player in self.selectionData[team]:
                    self.GivePlayerKit(player, self.selectionData[team][player][0], self.selectionData[team][player][1])

            for player in self.teams:
                self.NotifyToClient(player, 'ShowEqpPanelEvent', (True, True))

            comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
            for pos in c.mapBlockers:
                comp.SetBlockNew(pos, {
                    'name': 'minecraft:air'
                }, 0, 0)

        elif self.phase == 3 and not self.defuserPlanted:
            self.roundEnd(False)

    def roundEnd(self, isAttackersWin):
        self.phase = 4
        for player in self.team:
            self.NotifyToClient(player, 'ShowEqpPanelEvent', (False, True))

        if isAttackersWin:
            self.wins[1] += 1
            for player in self.attackers:
                self.sendTitle('§l§b第%s局胜利' % self.roundNum, 1, player)
                self.sendTitle('%s : %s' % (self.wins[1], self.wins[0]), 2, player)
            for player in self.defenders:
                self.sendTitle('§l§6第%s局落败' % self.roundNum, 1, player)
                self.sendTitle('%s : %s' % (self.wins[0], self.wins[1]), 2, player)
        else:
            self.wins[0] += 1
            for player in self.defenders:
                self.sendTitle('§l§b第%s局胜利' % self.roundNum, 1, player)
                self.sendTitle('%s : %s' % (self.wins[0], self.wins[1]), 2, player)
            for player in self.attackers:
                self.sendTitle('§l§6第%s局落败' % self.roundNum, 1, player)
                self.sendTitle('%s : %s' % (self.wins[1], self.wins[0]), 2, player)

        if self.roundNum == 2:
            for player in self.teams:
                if self.teams[player] == 0:
                    self.teams[player] = 1
                else:
                    self.teams[player] = 0

            winsDict = self.wins
            self.wins[0] = winsDict[1]
            self.wins[1] = winsDict[0]

        def a():
            self.newRoundInit()
        commonNetgameApi.AddTimer(10.0, a)

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
                self.sendMsgToAll("§c§l人数不够，比赛已被取消，请重新匹配")
                self.countdown = 60

                def a():
                    rebootSystem = serverApi.GetSystem('reboot', 'rebootSystem')
                    rebootSystem.DoReboot(False)
                commonNetgameApi.AddTimer(2.0, a)

            if self.countdown == 0:
                print 'starting!'
                self.start()
                self.status = 1

    def start(self):
        for player in self.waiting:
            tCount = self.getCountInDict(0, self.teams)
            ctCount = self.getCountInDict(1, self.teams)
            if tCount == ctCount:
                self.teams[player] = random.randint(0, 1)
            elif tCount > ctCount:
                self.teams[player] = 1
            else:
                self.teams[player] = 0

            self.selectionData[self.teams[player]][player] = [0, 0]
