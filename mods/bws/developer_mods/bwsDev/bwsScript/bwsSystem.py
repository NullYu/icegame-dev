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
import bwsScript.consts as c

mysqlPool.InitDB(30)

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()


##

# 在modMain中注册的Server System类
class bwsSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()


    def ListenEvents(self):
        self.ListenForEvent('bws', 'bwsClient', 'ActionEvent', self, self.OnClientAction)
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

    ##############################

    def OnClientAction(self, data):
        print 'bws client action data=%s' % data
        path = data['path']
        namespaced = data['namespaced']
        itemData = data['itemData']
        playerId = data['playerId']

        price = itemData[0]
        qty = itemData[1]

        bwSystem = serverApi.GetSystem('bw', 'bwSystem')

        if namespaced:

            if 'bow' in path:
                path = path.strip('1')

            comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
            print 'buy path=%s qty=%s' % (path, qty)
            itemDict = {
                'itemName': 'minecraft:'+path,
                'count': qty
            }

            if len(itemData) > 2:
                itemDict['enchantData'] = itemData[2]

            comp.SpawnItemToPlayerInv(itemDict, playerId)

        else:
            print 'buy path=%s qty=%s' % (path, qty)
            if path == 'wool':
                colorData = bwSystem.consts.colorData
                comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
                itemDict = {
                    'itemName': 'minecraft:wool',
                    'count': qty,
                    'auxValue': colorData[bwSystem.teams[playerId]]
                }
                comp.SpawnItemToPlayerInv(itemDict, playerId)

            elif path in c.armor:

                bwSystem = serverApi.GetSystem('bw', 'bwSystem')
                timers = bwSystem.armors
                con = bwSystem.consts
                if playerId in timers and timers[playerId] <= 0 and path in con.armorTimers:
                    bwSystem.armors[playerId] = con.armorTimers[path]
                bwSystem.armorsTime[playerId] = con.armorTimers[path]

                path = path.replace('chain', 'chainmail')
                comp = serverApi.GetEngineCompFactory().CreateItem(playerId)

                name = path.replace('_half', '')
                comp.SpawnItemToPlayerInv({
                    'itemName': 'minecraft:%s_leggings' % name,
                    'count': 1
                }, playerId)
                comp.SpawnItemToPlayerInv({
                    'itemName': 'minecraft:%s_boots' % name,
                    'count': 1
                }, playerId)
                if not '_half' in path:
                    comp.SpawnItemToPlayerInv({
                        'itemName': 'minecraft:%s_helmet' % name,
                        'count': 1
                    }, playerId)
                    comp.SpawnItemToPlayerInv({
                        'itemName': 'minecraft:%s_chestplate' % name,
                        'count': 1
                    }, playerId)

                self.sendMsg('§l§6您购买了盔甲！§r您必须在%s秒内击杀一名敌人，否则盔甲将失效!' % bwSystem.armors[playerId], playerId)

        bwSystem.balance[playerId] -= price


    def OpenBws(self, playerId, balance):

        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        if playerId in utilsSystem.spectating:
            return

        self.NotifyToClient(playerId, "ShowbwsEvent", balance)
        print 'opening bws for %s' % playerId

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("lobbyutils", "lobbyutilsClient", 'TestRequest', self, self.OnTestRequest)
