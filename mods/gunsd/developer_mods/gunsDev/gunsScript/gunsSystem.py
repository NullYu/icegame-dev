# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import math

import server.extraServerApi as serverApi
import time
import random
import json
import datetime
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.commonNetgameApi as commonNetgameApi
import apolloCommon.mysqlPool as mysqlPool
import gunsScript.gunsConsts as c
mysqlPool.InitDB(30)

# global consts
manual = 0
auto = 1
bolt = 2
# isSilent, isScope, isHeavy, isShotgun, isMelee, isCharge, canZoom
silent, scope, heavy, shotgun, melee, charge, zoom = 'silent', 'canscope', 'heavy', 'shotgun', 'melee', 'charge', 'zoom'
# side
t = 'terrorist'
ct = 'police'
all = 'universal_use'

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

playerAmmo = {}

import apolloCommon.redisPool as redisPool

# 在modMain中注册的Server System类
class gunsServerSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        self.healthData = {}
        self.equipData = {}
        self.pendingBullets = {}
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

    def sendMsg(self, msg, playerId):
        comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
        comp.NotifyOneMessage(playerId, msg, "§f")

    def forceSelect(self, slot, playerId):
        #print 'forceSelect called slot='+slot+' playerId='+playerId
        comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
        comp.ChangeSelectSlot(slot)

    def epoch2Datetime(self, epoch):
        ts = datetime.datetime.fromtimestamp(int(epoch)+0)
        return ts.strftime('%Y%m%d%H%M%S')

    def datetime2Epoch(self, y, m, d, h, mi):
        # Datetime must be in tuple(YYYY, MM, DD, HH, mm), for example, (1977, 12, 1, 0, 0)
        ts = (datetime.datetime(y, m, d, h, mi) - datetime.datetime(1970, 1, 1)).total_seconds()
        return int(ts)

    def getGunsCountInInventory(self, playerId):
        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        items = comp.GetPlayerAllItems(serverApi.GetMinecraftEnum().ItemPosType.INVENTORY)
        ret = 0
        for item in items:
            namespace = item['itemName']
            if 'guns:' in namespace:
                ret += 1
        return ret

    def dist(self, x1, y1, z1, x2, y2, z2):
        """
        运算3维空间距离，返回float
        """
        p = ((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) ** 0.5
        re = float('%.1f' % p)
        return re

    def getBulletTracerEntity(self, From, To, now):
        """
        From[tuple](x,y,z)
        To[tuple](x,y,z)
        now[float] e.g.:11.45%
        return[tuple](nowX,nowY,nowZ)
        """
        x1 = From[0]
        x2 = To[0]
        y1 = From[1]
        y2 = To[1]
        z1 = From[2]
        z2 = To[2]
        x = x1 + (x2 - x1) * now
        y = y1 + (y2 - y1) * now
        z = z1 + (z2 - z1) * now
        tup = (x, y, z)
        return tup

    def getBulletTracer(self, start, end):
        density = int(round(self.dist(start[0], start[1], start[2], end[0], end[1], end[2]))*3)
        li = []
        for i in range(density):
            li.append(self.getBulletTracerEntity(start, end, i/density))
        return li

    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnScriptTickServer", self, self.OnScriptTickServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self, self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self, self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerRespawnFinishServerEvent", self, self.OnPlayerRespawnFinishServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnCarriedNewItemChangedServerEvent", self, self.OnCarriedNewItemChangedServerEvent)
        self.ListenForEvent('guns', 'gunsClient', 'ClientActionEvent', self, self.OnClientAction)
        self.ListenForEvent('guns', 'gunsSystem', 'PlayerDeathEvent', self, self.OnGunsPlayerDeath)

    def OnClientAction(self, data):
        print 'clientaction data=%s' % data
        if data['action'] == 'fire':
            gunId = data['weaponId']
            playerId = data['playerId']

            print 'shot fired'
            comp = serverApi.GetEngineCompFactory().CreateGame(playerId)
            for player in serverApi.GetPlayerList():
                if player != playerId:
                    #normal damage
                    canhear = comp.CanSee(playerId, player, 1000.0, False, 20.0, 40.0)
                    cansee = comp.CanSee(playerId, player, 1000.0, False, 3.0, 10.0)
                    crit = comp.CanSee(playerId, player, 1000.0, False, 1.0, 1.0)

                    comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
                    attackerPos = comp.GetPos()
                    comp = serverApi.GetEngineCompFactory().CreatePos(player)
                    victimPos = comp.GetPos()
                    distance = self.dist(attackerPos[0], attackerPos[1], attackerPos[2], victimPos[0], victimPos[1], victimPos[2])

                    if canhear:
                        self.NotifyToClient(player, 'HearGunshotEvent', None)
                    if cansee:
                        # temporary debug
                        if crit:
                            dmg = int(c.gunAttrs[gunId][4].split('/')[1])
                        else:
                            dmg = int(c.gunAttrs[gunId][4].split('/')[0])

                        if shotgun in c.gunAttrs[gunId]:
                            pellets = int(c.gunAttrs[gunId][2].split('/')[2])
                            pellets -= math.floor(distance/2.5)
                            if pellets <= 0:
                                pellets = 1
                            dmg *= int(pellets)

                        dmg += random.randint(-5, 5)
                        if self.healthData[player][1]:
                            armor = self.healthData[player][1]
                            if armor >= dmg:
                                self.healthData[player][1] -= dmg
                                dmg = round(dmg*0.33)
                            else:
                                self.healthData[player][1] = 0
                                absorbedDmg = dmg-armor
                                dmg = (round(absorbedDmg*0.33)) + (dmg-absorbedDmg)

                        comp = serverApi.GetEngineCompFactory().CreateGame(player)
                        inFov = comp.CanSee(player, playerId, 50.0, True, 180.0, 180.0)

                        self.healthData[player][0] -= dmg
                        response = {
                            'dmg': dmg,
                            'health': self.healthData[player][0],
                            'armor': self.healthData[player][1],
                            'inFov': inFov
                        }
                        self.NotifyToClient(player, 'TakeDamageEvent', response)
                        print 'taking damage data=%s' % response
                        self.sendCmd('/effect @s slowness 2 1', player)

        elif data['action'] == 'melee':
            playerId = data['playerId']
            for player in serverApi.GetPlayerList():
                comp = serverApi.GetEngineCompFactory().CreateGame(playerId)
                cansee = comp.CanSee(playerId, player, 1000.0, False, 3.0, 10.0)
                comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
                attackerPos = comp.GetPos()
                comp = serverApi.GetEngineCompFactory().CreatePos(player)
                victimPos = comp.GetPos()
                distance = self.dist(attackerPos[0], attackerPos[1], attackerPos[2], victimPos[0], victimPos[1], victimPos[2])

                if cansee and distance <= 3:
                    self.healthData[player][0] = 0
                    inFov = comp.CanSee(player, playerId, 50.0, True, 180.0, 180.0)
                    response = {
                        'dmg': 100,
                        'health': self.healthData[player][0],
                        'armor': self.healthData[player][1],
                        'inFov': inFov
                    }
                    self.NotifyToClient(player, 'TakeDamageEvent', response)

    def SetPlayerValues(self, playerId, health, armor):
        if playerId in self.healthData:
            self.healthData[playerId] = [health, armor]

            data = {
                'health': self.healthData[playerId][0],
                'armor': self.healthData[playerId][1]
            }
            self.NotifyToClient(playerId, 'SetHealthEvent', data)

    def OnScriptTickServer(self):
        pass

        # line of sight debug
        # if len(serverApi.GetPlayerList()) > 1:
        #     playerId = serverApi.GetPlayerList()[0]
        #     target = serverApi.GetPlayerList()[1]
        #
        #     comp = serverApi.GetEngineCompFactory().CreateGame(playerId)
        #     cansee = comp.CanSee(playerId, target, 1000.0, False, 3.0, 10.0)
        #     if cansee:
        #         self.sendTitle('seeing player', 3, playerId)
        #     else:
        #         self.sendTitle('not seeing', 3, playerId)

        for player in serverApi.GetPlayerList():
            if self.healthData[player][0] <= 0:
                self.healthData[player][1] = 0
                self.NotifyToClient(player, 'DeathEvent', None)
                self.BroadcastEvent("PlayerDeathEvent", {
                    'playerId': player
                })

    def OnGunsPlayerDeath(self, data):
        playerId = data['playerId']
        comp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        comp.KillEntity(playerId)

    def OnPlayerRespawnFinishServer(self, data):
        playerId = data['playerId']
        self.NotifyToClient(playerId, 'ResetClientEvent', None)
        print 'player reset'

        self.healthData[playerId] = [100, 0]
        self.equipData[playerId] = None

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        uid = lobbyGameApi.GetPlayerUid(playerId)

        self.healthData[playerId] = [100, 0]
        self.equipData[playerId] = None

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        if playerId in self.healthData:
            self.healthData.pop(playerId)
        if playerId in self.equipData:
            self.equipData.pop(playerId)

    # api
    def GiveGunToPlayer(self, id, playerId):
        attrs = c.gunAttrs[id]
        ammoData = attrs[2].split('/')
        recoilData = attrs[3].split('/')
        dmgData = attrs[4].split('/')
        data = {
            'id': id,
            'name': c.gunNames[id],
            'namespace': 'guns:a'+str(id),

            'ammo': int(ammoData[0]),
            'maxAmmo': int(ammoData[0]),
            'reserveAmmo': int(ammoData[1]),

            'firemode': attrs[1],
            'recoilUp': int(recoilData[0]),
            'recoilLeft': int(recoilData[1]),
            'dmg': int(dmgData[0]),
            'dmgCrit': int(dmgData[1]),
            'scope': scope in attrs,
            'silent': silent in attrs,
            'heavy': heavy in attrs,
            'shotgun': shotgun in attrs,
            'melee': melee in attrs,
            'charge': charge in attrs,
            'zoom': zoom in attrs
        }
        itemDict = {
            'itemName': 'guns:a%s' % id,
            'count': 1,
            'auxValue': 0,
            'extraId': '%s/%s' % (ammoData[0], ammoData[1])
        }
        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        comp.SpawnItemToPlayerInv(itemDict, playerId, 0)

        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        if not self.equipData[playerId] and comp.GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0)['itemName'] == 'guns:a%s' % id:
            self.equipData[playerId] = id

    def OnCarriedNewItemChangedServerEvent(self, data):
        playerId = data['playerId']
        newItem = data['newItemDict']
        if newItem and 'guns:' in newItem['itemName']:
            self.equipData[playerId] = int(newItem['itemName'].replace('guns:a', ''))
            self.LoadNewEquipment(playerId, newItem)
        else:
            self.equipData[playerId] = None
            self.NotifyToClient(playerId, 'UnloadNewEquipmentEvent', None)

    def LoadNewEquipment(self, playerId, itemDict):
        ammoData = itemDict['extraId'].split('/')
        itemName = itemDict['itemName']
        id = int(itemName.replace('guns:a', ''))
        attrs = c.gunAttrs[id]
        recoilData = attrs[3].split('/')
        dmgData = attrs[4].split('/')
        data = {
            'id': id,
            'name': c.gunNames[id],
            'namespace': 'guns:a' + str(id),

            'ammo': int(ammoData[0]),
            'maxAmmo': int(ammoData[0]),
            'reserveAmmo': int(ammoData[1]),

            'firemode': attrs[1],
            'recoilUp': int(recoilData[0]),
            'recoilLeft': int(recoilData[1]),
            'dmg': int(dmgData[0]),
            'dmgCrit': int(dmgData[1]),
            'scope': scope in attrs,
            'silent': silent in attrs,
            'heavy': heavy in attrs,
            'shotgun': shotgun in attrs,
            'melee': melee in attrs,
            'charge': charge in attrs,
            'zoom': zoom in attrs
        }

        self.NotifyToClient(playerId, 'LoadNewEquipmentEvent', data)
