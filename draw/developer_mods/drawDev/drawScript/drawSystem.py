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
import drawScript.drawConsts as vars

mysqlPool.InitDB(30)

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()


##

# 在modMain中注册的Server System类
class drawSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()


    def ListenEvents(self):
        self.ListenForEvent('draw', 'drawClient', 'ActionEvent', self, self.OnAction)
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

    ############################

    def OpenDrawUi(self, playerId, isOverride=False, specifyDraws=0):
        uid = lobbyGameApi.GetPlayerUid(playerId)

        sql = 'SELECT high FROM eco WHERE uid=%s;'
        def Cb(args):
            if args:
                sql = 'SELECT password FROM sudo WHERE uid=%s AND unsafe=0;'
                def Cb(m0):
                    if m0:
                        if m0[0][0] == '0' and not isOverride:
                            self.sendMsg("§c无独立密码，无法进行该操作！", playerId)
                            return

                        if not isOverride:
                            credits = args[0][0]
                        else:
                            credits = specifyDraws*16
                        data = {
                            "playerId": playerId,
                            "credits": credits
                        }
                        self.NotifyToClient(playerId, "OpenDrawUiEvent", data)

                    else:
                        self.sendMsg("Operation not permitted", playerId)
                        return
                mysqlPool.AsyncQueryWithOrderKey('adsmgb6213vb89n', sql, (uid,), Cb)
            else:
                self.sendMsg("Error while getting information!")
        mysqlPool.AsyncQueryWithOrderKey('as9d8ansd', sql, (uid,), Cb)

    def OnAction(self, data):
        playerId = data['playerId']
        poolId = data['pool']
        choice = data['choice']
        uid = lobbyGameApi.GetPlayerUid(playerId)

        # GENERATE NUMBTER
        if choice == 'single':
            value = random.randint(0, 199)
            pool = vars.labelPool
            prize = None
            for key in pool.keys():
                if value in pool[key]:
                    prize = key
                    level = key
                    break

            result = prize

            if prize != 'label':
                prize = vars.labelPoolNames[key]
                desc = '已交付 - 立即入账'
            else:
                index = random.randint(0, 16)
                prize = vars.labelPoolLabels[random.choice(vars.labelPoolLabels.keys())]
                if index == 0:
                    desc = "称号 - 已交付 - 永久有效"
                elif index < 7:
                    desc = "称号 - 已交付 - 30天"
                else:
                    desc = "称号 - 已交付 - 7天"

                prize = vars.labelPoolLabels[prize]
            data = {
                'playerId': playerId,
                'poolId': poolId,
                'prizeName': prize,  #
                'desc': desc,  #
                'choice': 'single',
                'level': vars.labelPoolLevels[level]
            }
            self.NotifyToClient(playerId, "DrawEvent", data)
            print 'drawevent args=%s' % data

            ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')
            ecoSystem.GivePlayerEco(uid, -16, 'draw labelpack 1', True)

            # Process draw result
            mInDict = False
            for item in vars.labelPoolLabels:
                if vars.labelPoolLabels[item] == prize:
                    mInDict = True
                    labelId = item
                    break

            if mInDict:
                if index == 0:
                    expire = -1
                elif index < 7:
                    expire = 30
                else:
                    expire = 7

                sql = 'INSERT INTO items (uid, type, itemId, expire) VALUES (%s, "label", %s, %s);'
                mysqlPool.AsyncExecuteWithOrderKey('9sad0d7sad8smasasda', sql, (uid, abs(labelId), expire))
            else:
                if '_credits' in result:
                    credits = int(result.replace('_credits', ''))
                    ecoSystem.GivePlayerEco(uid, credits, 'drawed', True)

    def ApiTestDraw(self, playerId):
        print 'api testdraw'
        data = {
            'playerId': playerId,
            'poolId': 0,
            'prizeName': '空气',
            'desc': '测试项 - 已交付 - 立即入账',
            'choice': 'single',
            'level': 0
        }
        self.NotifyToClient(playerId, "DrawEvent", data)
