# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import json
import datetime
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.redisPool as redisPool
import apolloCommon.commonNetgameApi as commonNetgameApi
import apolloCommon.mysqlPool as mysqlPool

mysqlPool.InitDB(30)

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()


##

# 在modMain中注册的Server System类
class hudSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        self.playerData = {}
        self.nearDeathPlayers = []

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self, self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self, self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnScriptTickServer", self, self.OnScriptTickServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerAttackEntityEvent", self, self.OnPlayerAttackEntity)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DamageEvent", self, self.OnDamage)
        self.ListenForEvent('hud', 'hudClient', "DisplayDeathDoneEvent", self, self.OnDisplayDeathDone)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerRespawnFinishServerEvent", self, self.OnPlayerRespawnFinishServer)
        # self.ListenForEvent('utils', 'utilsClient', 'ActionEvent', self, self.OnClientAction)
        pass
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

    def epoch2Datetime(self, epoch):
        ts = datetime.datetime.fromtimestamp(int(epoch))
        return ts.strftime('%Y-%m-%d %H:%M:%S')

    def sendMsg(self, msg, playerId):
        comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
        comp.NotifyOneMessage(playerId, msg, "§f")

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("lobbyutils", "lobbyutilsClient", 'TestRequest', self, self.OnTestRequest)

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        uid = lobbyGameApi.GetPlayerUid(playerId)
        sql = 'SELECT hudOverride FROM userSettings WHERE uid=%s AND hudOverride=1;'
        self.playerData[playerId] = None

        # TODO remove debug
        def a():
            self.NotifyToClient(playerId, 'SetEnableHudEvent', True)
            print 'set hudenable'
        commonNetgameApi.AddTimer(14.5, a)
        return

        def Cb(args):
            commonNetgameApi.AddTimer(5.0, lambda a: self.NotifyToClient(a, 'SetEnableHudEvent', bool(args)), playerId)
        mysqlPool.AsyncQueryWithOrderKey('cioasud89u123klk', sql, (uid,), Cb)

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        if playerId in self.playerData:
            self.playerData.pop(playerId)

        if playerId in self.nearDeathPlayers:
            self.nearDeathPlayers.pop(self.nearDeathPlayers.index(playerId))

    def OnPlayerRespawnFinishServer(self, data):
        playerId = data['playerId']
        self.NotifyToClient(playerId, 'ResetHudEvent', None)
        if playerId in self.nearDeathPlayers:
            self.nearDeathPlayers.pop(self.nearDeathPlayers.index(playerId))

    def OnDisplayDeathDone(self, playerId):
        print 'death done for %s' % playerId
        comp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        comp.KillEntity(playerId)

    def OnPlayerAttackEntity(self, data):
        playerId = data['victimId']
        if playerId in self.nearDeathPlayers:
            data['cancel'] = True

    def OnDamage(self, data):
        attackerId = data['srcId']
        victimId = data['entityId']
        damage = data['damage']

        if victimId not in serverApi.GetPlayerList():
            return

        if victimId in self.nearDeathPlayers:
            data['damage'] = 0
            return

        comp = serverApi.GetEngineCompFactory().CreateAttr(victimId)
        victimHp = comp.GetAttrValue(serverApi.GetMinecraftEnum().AttrType.HEALTH)
        print 'damage, hp, isInNearDeath: %s %s %s' % (damage, victimHp, victimId in self.nearDeathPlayers)
        if damage >= victimHp:
            # server custom death logic FIRST
            print 'damage enough to kill'
            self.nearDeathPlayers.append(victimId)
            data['damage'] = 0

            deathMsgSystem = serverApi.GetSystem('deathmsg', 'deathmsgSystem')
            if deathMsgSystem:
                deathMsgSystem.OnPlayerDie({
                    'id': victimId,
                    'attacker': attackerId
                })

            self.sendCmd('/effect @s invisibility 99999 1 true', victimId)

            response = {
                'isSuicide': not(attackerId != victimId and attackerId in serverApi.GetPlayerList()),
                'killerId': attackerId,
                'killerNickname': lobbyGameApi.GetPlayerNickname(attackerId),
                'victimId': victimId
            }
            if (attackerId != victimId) and attackerId in serverApi.GetPlayerList():
                print 'kill by others'
                self.NotifyToClient(attackerId, 'DisplayKillIndicatorEvent', response)
                self.NotifyToClient(victimId, 'DisplayKillIndicatorEvent', response)
                self.NotifyToClient(victimId, 'DisplayDeathEvent', response)
            else:
                print 'kill by self'
                self.NotifyToClient(victimId, 'DisplayKillIndicatorEvent', response)
                self.NotifyToClient(victimId, 'DisplayDeathEvent', response)


    def OnScriptTickServer(self):
        for player in serverApi.GetPlayerList():
            comp = serverApi.GetEngineCompFactory().CreateAttr(player)
            data = {
                'hp': comp.GetAttrValue(serverApi.GetMinecraftEnum().AttrType.HEALTH),
                'extra': comp.GetAttrValue(serverApi.GetMinecraftEnum().AttrType.ABSORPTION),
                'hunger': comp.GetAttrValue(serverApi.GetMinecraftEnum().AttrType.HUNGER),
                'armor': 0
            }
            comp = serverApi.GetEngineCompFactory().CreateItem(player)

            for i in range(4):
                if comp.GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.ARMOR, i):
                    name = comp.GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.ARMOR, i)['itemName']
                    if 'helmet' in name:
                        if 'leather' in name:
                            data['armor'] += 0.5
                        elif 'diamond' in name:
                            data['armor'] += 1.5
                        else:
                            data['armor'] += 1
                    elif 'chestplate' in name:
                        if 'leather' in name:
                            data['armor'] += 1.5
                        elif 'diamond' in name:
                            data['armor'] += 4
                        elif 'iron' in name:
                            data['armor'] += 3
                        else:
                            data['armor'] += 2.5
                    elif 'leggings' in name:
                        if 'leather' in name:
                            data['armor'] += 1
                        elif 'diamond' in name:
                            data['armor'] += 3
                        elif 'iron' in name:
                            data['armor'] += 2.5
                        elif 'gold' in name:
                            data['armor'] += 1.5
                        elif 'chainmail' in name:
                            data['armor'] += 2
                        else:
                            data['armor'] += 2.5
                    elif 'boots' in name:
                        if 'iron' in name:
                            data['armor'] += 1
                        elif 'diamond' in name:
                            data['armor'] += 1.5
                        else:
                            data['armor'] += 0.5
                    elif 'turtle' in name:
                        data['armor'] += 1

            if self.playerData[player] != data:
                self.NotifyToClient(player, 'UpdateHudEvent', data)

            self.playerData[player] = data
