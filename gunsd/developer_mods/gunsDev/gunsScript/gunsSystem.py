# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
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

    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self, self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self, self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnCarriedNewItemChangedServerEvent", self, self.OnCarriedNewItemChangedServerEvent)
        # self.ListenForEvent('sign', 'signClient', 'SignActionEvent', self,
        #                     self.OnSignAction)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("lobbyutils", "lobbyutilsClient", 'TestRequest', self, self.OnTestRequest)

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
        if 'guns:' in newItem['itemName']:
            self.equipData[playerId] = int(newItem['itemName'].replace('guns:a', ''))
            self.LoadNewEquipment(playerId, newItem)
        else:
            self.equipData[playerId] = None

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
