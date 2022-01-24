# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServiceApi as serviceApi
import apolloCommon.mysqlPool as mysqlPool
import time
import random
import service.serverManager as serverManager
import v5ServiceScript.v5ServiceConsts as c
import apolloCommon.commonNetgameApi as commonNetgameApi
import service.serviceConf as serviceConf

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serviceApi.GetServiceSystemCls()

# 在modMain中注册的Server System类
class v5ServiceSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        print 'INIT namespace='+namespace+' systemName='+systemName
        self.RegisterRpcMethod("v5", 'RecordSidEvent', self.OnRecordSid)
        self.RegisterRpcMethodForMod('RecordSidEvent', self.OnRecordSid)
        self.RegisterRpcMethod("v5", 'StartMatchmakingEvent', self.OnStartMatchmaking)
        self.RegisterRpcMethod("v5", 'ExitMatchmakingEvent', self.OnExitMatchmaking)

        self.ListenForEvent(serviceApi.GetEngineNamespace(), serviceApi.GetEngineSystemName(), "ServerConnectedEvent", self, self.OnServerConnected)
        self.ListenForEvent(serviceApi.GetEngineNamespace(), serviceApi.GetEngineSystemName(), "ServerDisconnectEvent", self, self.OnServerDisconnect)
        commonNetgameApi.AddRepeatedTimer(1.0, self.tick)

        self.servers = {}

        self.queue = []
        self.playerServers = {}

    def item2Index(self, li, value):
        try:
            return li.index(value)
        except ValueError:
            return -1

    def OnServerConnected(self, data):
        sid = data['serverId']
        serverType = serverManager.GetServerType(sid)

        if ('v5' in serverType) and sid not in self.servers:
            self.servers[sid] = 0

    def OnServerDisconnect(self, data):
        sid = data['serverId']
        if sid in self.servers:
            self.servers.pop(sid)

    def OnRecordSid(self, serverId, callbackId, args):
        print 'Onrecordsid args=%s' % (args,)
        sid = args['sid']
        status = args['value']
        isOverride = args['override']

        if status == 0 and not isOverride:
            return

        self.servers[sid] = status

        print('Updated/record game/unranked game server: sid='+str(sid))

    def OnStartMatchmaking(self, serverId, callbackId, data):
        print 'start matchmaking rcv'
        uid = data['uid']
        self.queue.append(uid)
        self.playerServers[uid] = serverId
        response = {
            'suc': True,
            'playerId': data['playerId']
        }
        self.ResponseToServer(serverId, callbackId, response)

    def OnExitMatchmaking(self, serverId, callbackId, data):
        print 'exit matchmaking rcv'
        uid = data['uid']
        if uid not in self.queue:
            response = {
                'suc': False
            }
            self.ResponseToServer(serverId, callbackId, response)
            return

        self.queue.pop(self.queue.index(uid))
        self.playerServers.pop(uid)
        response = {
            'suc': True,
            'playerId': data['playerId']
        }
        self.ResponseToServer(serverId, callbackId, response)

    def tick(self):
        queueLength = len(self.queue)

        print 'queue=%s, servers=%s' % (self.queue, self.servers)

        for uid in self.queue:
            pos = self.queue.index(uid)

            if queueLength < c.roomSize:
                response = {
                    'uid': uid,
                    'status': 'wait',
                    'count': queueLength
                }
                self.NotifyToServerNode(self.playerServers[uid], "UpdateMatchInfoEvent", response)
                print 'WAIT 1'
            elif queueLength >= c.roomSize > pos == c.roomSize - 1:
                self.startMatch()
                print 'START'

            else:
                response = {
                    'uid': uid,
                    'status': 'wait',
                    'count': queueLength % c.roomSize
                }
                self.NotifyToServerNode(self.playerServers[uid], "UpdateMatchInfoEvent", response)
                print 'WAIT2'

    def startMatch(self):
        print 'starting match'
        li = self.queue[:c.roomSize]

        okServer = None
        for server in self.servers:
            if self.servers[server] == 0 or self.servers[server] == [0]:
                okServer = server
                break

        for uid in li:
            if okServer:
                response = {
                    'uid': uid,
                    'status': 'start',
                    'count': len(self.queue),
                    'sid': okServer
                }
                self.NotifyToServerNode(self.playerServers[uid], "UpdateMatchInfoEvent", response)
                self.servers[okServer] = 1
            else:
                response = {
                    'uid': uid,
                    'status': 'wait',
                    'count': len(self.queue)
                }
                self.NotifyToServerNode(self.playerServers[uid], "UpdateMatchInfoEvent", response)

        if okServer:
            del self.queue[:c.roomSize]
