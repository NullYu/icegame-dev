# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServiceApi as serviceApi
import apolloCommon.mysqlPool as mysqlPool
import time
import random
import apolloCommon.commonNetgameApi as commonNetgameApi
import service.serviceConf as serviceConf

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serviceApi.GetServiceSystemCls()

# Servers structure:
# {serverId INT: [status INT, count INT OPT]}
# 在modMain中注册的Server System类
class manhuntServiceSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        print 'INIT namespace='+namespace+' systemName='+systemName
        self.RegisterRpcMethod("manhunt", 'RecordSidEvent', self.OnRecordSid)
        self.RegisterRpcMethod("manhunt", 'RequestMatchmakingEvent', self.OnRequestMatchmaking)
        
        self.servers = {}

    def item2Index(self, li, value):
        try:
            return li.index(value)
        except ValueError:
            return -1

    def OnRecordSid(self, serverId, callbackId, args):
        print 'Onrecordsid args=%s' % (args,)
        sid = args['sid']
        status = args['value']

        if 'count' in args:
            self.servers[sid] = [status, args['count']]
        else:
            self.servers[sid] = [status]

        print('Updated/record game/unranked game server: sid='+str(sid))

    def OnRequestMatchmaking(self, serverId, callbackId, playerId):
        self.mCount = 0

        print 'servers are now %s' % (self.servers,)

        for server in self.servers:
            if self.servers[server][0] == 0:
                self.mCount += 1
        if self.mCount <= 0:
            response = {
                'value': 0,
                'playerId': playerId
            }
            self.ResponseToServer(serverId, callbackId, response)
            return

        self.mPossibleServers = []
        for server in self.servers:
            params = self.servers[server]
            if len(params) > 1 and params[0] == 0 and params[1] == 3:
                self.mPossibleServers.append(server)
        if self.mPossibleServers:
            response = {
                'value': 1,
                'sid': random.choice(self.mPossibleServers),
                'playerId': playerId
            }
            self.ResponseToServer(serverId, callbackId, response)
            return
        for server in self.servers:
            params = self.servers[server]
            if len(params) > 1 and params[0] == 0 and params[1] == 2:
                self.mPossibleServers.append(server)
        if self.mPossibleServers:
            response = {
                'value': 1,
                'sid': random.choice(self.mPossibleServers),
                'playerId': playerId
            }
            self.ResponseToServer(serverId, callbackId, response)
            return
        for server in self.servers:
            params = self.servers[server]
            if params[0] == 0:
                self.mPossibleServers.append(server)
        response = {
            'value': 1,
            'sid': random.choice(self.mPossibleServers),
            'playerId': playerId
        }
        self.ResponseToServer(serverId, callbackId, response)
        return
