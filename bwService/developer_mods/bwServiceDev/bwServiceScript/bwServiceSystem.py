# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServiceApi as serviceApi
import apolloCommon.mysqlPool as mysqlPool
import time
import random
import service.serverManager as serverManager
import apolloCommon.commonNetgameApi as commonNetgameApi
import service.serviceConf as serviceConf

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serviceApi.GetServiceSystemCls()

# 在modMain中注册的Server System类
class bwServiceSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        print 'INIT namespace='+namespace+' systemName='+systemName
        self.RegisterRpcMethod("bw", 'RecordSidEvent', self.OnRecordSid)
        self.RegisterRpcMethodForMod('RecordSidEvent', self.OnRecordSid)
        self.RegisterRpcMethod("bw", 'RequestMatchmakingEvent', self.OnRequestMatchmaking)

        self.ListenForEvent(serviceApi.GetEngineNamespace(), serviceApi.GetEngineSystemName(), "ServerConnectedEvent", self, self.OnServerConnected)
        self.ListenForEvent(serviceApi.GetEngineNamespace(), serviceApi.GetEngineSystemName(), "ServerDisconnectEvent", self, self.OnServerDisconnect)

        self.servers = {}

    def item2Index(self, li, value):
        try:
            return li.index(value)
        except ValueError:
            return -1

    def OnServerConnected(self, data):
        sid = data['serverId']
        serverType = serverManager.GetServerType(sid)

        if ('bw' in serverType or 'game_sw' in serverType or 'tntr' in serverType or 'mm' in serverType) and sid not in self.servers:
            self.servers[sid] = [0]

    def OnServerDisconnect(self, data):
        sid = data['serverId']
        if sid in self.servers:
            self.servers.pop(sid)

    def OnRecordSid(self, serverId, callbackId, args):
        print 'Onrecordsid args=%s' % (args,)
        sid = args['sid']
        status = args['value']

        if 'count' in args:
            self.servers[sid] = [status, args['count']]
        else:
            self.servers[sid] = [status]

        print('Updated/record game/unranked game server: sid='+str(sid))

    def OnRequestMatchmaking(self, serverId, callbackId, data):
        playerId = data['playerId']
        mode = data['mode']

        self.mCount = 0
        print 'servers are now %s' % (self.servers,)

        for server in self.servers:
            if self.servers[server][0] == 0 and serverManager.GetServerType(server).split('T')[0] == mode:
                self.mCount += 1
        if self.mCount <= 0:
            response = {
                'value': 0,
                'playerId': playerId
            }
            self.ResponseToServer(serverId, callbackId, response)
            return

        mPossibleServer = 0
        mComp = 0
        mChoice = random.randint(1, 100)

        if mode in ['game_8bw1']:
            threshhold = 6
        elif 'fb' in mode:
            threshhold = 4
        else:
            threshhold = 12

        for server in self.servers:
            params = self.servers[server]
            if params[0] == 0 and len(params) > 0 and params[1] < threshhold and mChoice > 25 and serverManager.GetServerType(server).split('T')[0] == mode:
                count = params[1]
                if not mComp or (count > mComp):
                    mPossibleServer = server
                    mComp = count
            elif params[0] == 0 and len(params) > 0 and params[1] < threshhold and mChoice <= 25 and serverManager.GetServerType(server).split('T')[0] == mode:
                count = params[1]
                if not mComp or (count > mComp):
                    mPossibleServer = server
                    mComp = count

        # self.mPossibleServers = []
        # for server in self.servers:
        #     params = self.servers[server]
        #     if len(params) > 1 and params[0] == 0 and 14 <= params[1] < 16 and serverManager.GetServerType(server) == mode:
        #         self.mPossibleServers.append(server)
        # if self.mPossibleServers:
        #     response = {
        #         'value': 1,
        #         'sid': random.choice(self.mPossibleServers),
        #         'playerId': playerId
        #     }
        #     self.ResponseToServer(serverId, callbackId, response)
        #     return
        # for server in self.servers:
        #     params = self.servers[server]
        #     if len(params) > 1 and params[0] == 0 and 8 < params[1] < 16 and serverManager.GetServerType(server) == mode:
        #         self.mPossibleServers.append(server)
        # if self.mPossibleServers:
        #     response = {
        #         'value': 1,
        #         'sid': random.choice(self.mPossibleServers),
        #         'playerId': playerId
        #     }
        #     self.ResponseToServer(serverId, callbackId, response)
        #     return
        # for server in self.servers:
        #     params = self.servers[server]
        #     if len(params) > 1 and params[0] == 0 and params[1] < 16 and serverManager.GetServerType(server) == mode:
        #         self.mPossibleServers.append(server)

        response = {
            'value': 1,
            'sid': mPossibleServer,
            'playerId': playerId
        }
        self.ResponseToServer(serverId, callbackId, response)
        return
