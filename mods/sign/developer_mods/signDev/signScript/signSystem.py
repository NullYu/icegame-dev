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
mysqlPool.InitDB(30)

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

selectProt = {}
page = {}

import apolloCommon.redisPool as redisPool

# 在modMain中注册的Server System类
class signServerSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        self.lastsign = None

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

    def calcPrizes(self, combo, total):
        neko = 128 + 2**combo + total*2
        credits = (combo>=7)*2*total + (combo>=14)*2*combo + (combo>=30)*10*combo
        extraCredits = (combo>=14)*4*combo
        return tuple((neko, credits, extraCredits))

    def calcCanSign(self, lastsign):
        datenow = int(str(self.epoch2Datetime(time.time()+0))[0:8])
        dateLastsign = int(str(self.epoch2Datetime(lastsign))[0:8])

        if datenow == dateLastsign:
            return False
        else:
            return True

    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self,
                            self.OnAddServerPlayer)
        self.ListenForEvent('sign', 'signClient', 'SignActionEvent', self,
                            self.OnSignAction)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("lobbyutils", "lobbyutilsClient", 'TestRequest', self, self.OnTestRequest)

    def OnSignAction(self, args):
        playerId = args['playerId']
        uid = lobbyGameApi.GetPlayerUid(playerId)
        neko = args['neko']
        credits = args['credits']
        print '===SIGNIN FROM %s===' % (playerId,)

        sql = 'UPDATE sign SET lastsign=%s,total=total+1,combo=combo+1 WHERE uid=%s'
        mysqlPool.AsyncExecuteWithOrderKey('oaisuoq', sql, (time.time()+0, uid))

        ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')
        ecoSystem.GivePlayerEco(uid, neko, 'sign')
        if credits > 0:
            ecoSystem.GivePlayerEco(uid, credits, 'sign', True)

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        uid = lobbyGameApi.GetPlayerUid(playerId)

        sql = 'SELECT lastsign,combo,total FROM sign WHERE uid=%s;'
        def Cb(args):
            if args:
                data = args[0]
                lastsign = int(data[0])
                combo = data[1]
                total = data[2]

                if (time.time()+0 - lastsign) > 172800:
                    combo = 0
                    sql = "UPDATE sign SET combo=0 WHERE uid=%s"
                    mysqlPool.AsyncExecuteWithOrderKey('ail8qw012bh', sql, (uid,))

                if (time.time()+0 - lastsign) >= 86400:
                    response = {
                        'playerId': playerId,
                        'uid': uid,
                        'cansign': self.calcCanSign(lastsign),
                        'date': int(time.time()+0),
                        'lastsign': lastsign,
                        'combo': combo,
                        'total': total,
                        'prizes': self.calcPrizes(combo, total)
                    }
                    def a():
                        self.NotifyToClient(playerId, "OpenSignEvent", response)
                    commonNetgameApi.AddTimer(10.0, a)
                    print 'player try to open sign canSign=%s' % (self.calcCanSign(lastsign),)
            else:
                sql = 'INSERT INTO sign (uid, lastsign) VALUES (%s, %s);'
                mysqlPool.AsyncExecuteWithOrderKey('aoisghfoaiw', sql, (uid, time.time()-57600))

                lastsign = int(time.time()-57600)
                response = {
                    'playerId': playerId,
                    'uid': uid,
                    'cansign': True,
                    'date': int(time.time() + 0),
                    'lastsign': lastsign,
                    'combo': 0,
                    'total': 0,
                    'prizes': (128, 0, 0)
                }
                def a():
                    self.NotifyToClient(playerId, "OpenSignEvent", response)
                commonNetgameApi.AddTimer(10.0, a)

        mysqlPool.AsyncQueryWithOrderKey('aosiao8wuoreq', sql, (uid,), Cb)

    # Sign api
    def TrySign(self, playerId):
        print 'trysign playerId=%s' % (playerId,)
        uid = lobbyGameApi.GetPlayerUid(playerId)

        sql = 'SELECT lastsign,combo,total FROM sign WHERE uid=%s;'

        def Cb(args):
            if args:
                data = args[0]
                lastsign = int(data[0])
                combo = data[1]
                total = data[2]
                response = {
                    'playerId': playerId,
                    'uid': uid,
                    'cansign': self.calcCanSign(lastsign),
                    'date': int(time.time() + 0),
                    'lastsign': lastsign,
                    'combo': combo,
                    'total': total,
                    'prizes': self.calcPrizes(combo, total)
                }

                self.NotifyToClient(playerId, "OpenSignEvent", response)

                print 'player try to open sign canSign=%s' % (self.calcCanSign(lastsign),)
            else:
                sql = 'INSERT INTO sign (uid, lastsign) VALUES (%s, %s);'
                mysqlPool.AsyncExecuteWithOrderKey('aoisghfoaiw', sql, (uid, time.time() - 57600))

                lastsign = int(time.time() - 57600)
                response = {
                    'playerId': playerId,
                    'uid': uid,
                    'cansign': True,
                    'date': int(time.time() + 0),
                    'lastsign': lastsign,
                    'combo': 0,
                    'total': 0,
                    'prizes': (128, 0, 0)
                }

                self.NotifyToClient(playerId, "OpenSignEvent", response)

        mysqlPool.AsyncQueryWithOrderKey('8snasdbn128w', sql, (uid,), Cb)