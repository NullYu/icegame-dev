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

        self.timers = {}
        self.defuserPlanting = False
        self.defuserActive = False
        self.roundTimer = c.roundTime
        self.defuserPlanted = False
        self.timerTicking = False

        self.teams = {}
        self.waiting = []

        self.status = 0

        # 0=t, 1=ct

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self, self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self, self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(),"PlayerInventoryOpenScriptServerEvent", self, self.OnPlayerInventoryOpenScriptServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self, self.OnCommand)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnCarriedNewItemChangedServerEvent", self, self.OnOnCarriedNewItemChangedServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerAttackEntityEvent", self, self.OnPlayerAttackEntity)

        # self.ListenForEvent('hud', 'hudClient', "DisplayDeathDoneEvent", self, self.OnDisplayDeathDone)
        # self.ListenForEvent('music', 'musicSystem', 'CreateMusicIdEvent', self, self.OnCreateMusicId)

        self.ListenForEvent('v5', 'v5Client', 'ActionEvent', self, self.OnClientAction)

        commonNetgameApi.AddRepeatedTimer(1.0, self.roundTick)

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

    def getCountInDict(self, key, dic):
        ret = 0
        for item in dic:
            if dic[item] == key:
                ret += 1
        return ret

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

            elif flag == 'cmd':
                self.sendCmd(data['command'].replace('/v5debug cmd ', ''), playerId)

            elif flag == 'game':
                if keyword == 'start':
                    self.status = 1
                elif keyword == 'stop':
                    self.status = 0

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

    # ################# TICK TIMERS ###############
    u"""
        This section contains all the timers
    """

    def roundTick(self):
        if self.timerTicking and not self.defuserPlanted:
            self.roundTimer -= 1
            for player in serverApi.GetPlayerList():
                self.NotifyToClient(player, 'TimerUpdateEvent', str(datetime.timedelta(seconds=int(self.roundTimer))))

    # ################# SERVER CODE ###############
    u"""
        Starting in this section are the server codes
    """

    def OnPlayerInventoryOpenScriptServer(self, data):
        playerId = data['playerId']

        lobbyGameApi.TryToKickoutPlayer(playerId, "§6与服务器断开连接")

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        self.playerEquips[playerId] = 0
        self.playerIsFixing[playerId] = False

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        self.playerEquips.pop(playerId)
        self.playerIsFixing.pop(playerId)

    def OnOnCarriedNewItemChangedServer(self, data):
        playerId = data['playerId']
        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        newSlotId = comp.GetSelectSlotId()
        oldSlotId = self.playerEquips[playerId] - 1
        if newSlotId != oldSlotId and newSlotId != 4:
            comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
            comp.ChangeSelectSlot(oldSlotId)

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

    def newRoundInit(self):
        self.roundTimer = c.roundTime
        self.defuserPlanting = False
        self.defuserActive = False
        self.roundTimer = c.roundTime
        self.defuserPlanted = False
        self.timerTicking = False
        self.reset_selectionData()

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
