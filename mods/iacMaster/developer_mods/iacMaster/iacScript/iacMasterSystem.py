# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraMasterApi as extraMasterApi
import apolloCommon.mysqlPool as mysqlPool
import time
import master.serverManager as serverManager
import apolloCommon.redisPool as redisPool
import apolloCommon.commonNetgameApi as commonNetgameApi
redisPool.InitDB(30)
mysqlPool.InitDB(30)

# 获取引擎服务端System的基类，System都要继承于MasterSystem来调用相关函数
MasterSystem = extraMasterApi.GetMasterSystemCls()

# 在modMain中注册的Server System类
class iacMasterSystem(MasterSystem):
    # MasterSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        MasterSystem.__init__(self, namespace, systemName)
        self.ListenEvent()

    def ListenEvent(self):
        self.ListenForEvent('iac', 'iacSystem', 'ApiAddVlEvent', self, self.OnApiAddVl)
        self.ListenForEvent('iac', 'iacSystem', 'RecIacBanEvent', self, self.OnIacBan)
        self.ListenForEvent('admin', 'adminSystem', 'GlobalKickEvent', self, self.OnGlobalKick)

    def OnApiAddVl(self, data):
        uid = data['uid']
        vl = data['vl']

        def b(args):
            return
        def a(conn):
            conn.incrby('iac-vl-%s'%(uid,), vl)
        redisPool.AsyncFuncWithKey(a, "iac-api-%s"%(uid,), b)

    def OnIacBan(self, data):
        uid = data['uid']
        sid = data['sid']

        print 'on OnIacBan'

        sql = 'INSERT INTO banData (uid, startDate, endDate, reason, executorUid) VALUES (%s, %s, %s, "iac assertion", 0);'
        mysqlPool.AsyncExecuteWithOrderKey('09as7fn91209', sql, (uid, time.time()+0, time.time()+10368000))
        redisPool.AsyncSet('iac-vl-%s' % (uid,), '0')
        self.NotifyToServerNode(sid, "IacBanEvent", data)

    def OnGlobalKick(self, data):
        uid = data['uid']

        idList = serverManager.GetConnectedLobbyAndGameIds()

        for server in idList:
            self.NotifyToServerNode(server, "GlobalKickServerEvent", uid)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass