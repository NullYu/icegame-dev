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

# Status codes:
# 0=ok
# 1=in game
# 2=down

# 在modMain中注册的Server System类
class unrankedServiceSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        print 'INIT namespace='+namespace+' systemName='+systemName
        self.RegisterRpcMethod("matchmaking", 'RequestMatchmakingEvent', self.OnRequestMatchmaking)
        self.RegisterRpcMethod("matchmaking", 'CancelMatchmakingEvent', self.OnCancelMatchmaking)
        # self.RegisterRpcMethod("matchmaking", 'NotifyStartGameEvent', self.OnNotifyStartGame)
        self.RegisterRpcMethod("matchmaking", 'GameEndByKillEvent', self.OnGameEndByKill)
        self.RegisterRpcMethod("matchmaking", 'GameEndByDisconnectionEvent', self.OnGameEndByDisconnection)
        self.RegisterRpcMethod("matchmaking", 'RecordSidEvent', self.OnRecordSid)
        self.RegisterRpcMethod("matchmaking", 'ForceReset', self.OnForceReset)
        self.ListenForEvent(serviceApi.GetEngineNamespace(), serviceApi.GetEngineSystemName(), "ServerConnectedEvent", self, self.OnServerConnected)
        self.ListenForEvent(serviceApi.GetEngineNamespace(), serviceApi.GetEngineSystemName(), "ServerDisconnectEvent", self, self.OnServerDisconnect)

        self.servers = {}
        self.waiting = {
            "s2p2": [],
            "sumo": [],
            "nor": [],
            "buhc": [],
            "archer": [],
            "combo": [],
            "totem": []
        }
        self.sids = {}
        self.sumoServers = []

        def sendStatus():
            print 'Server sendStatus servers='+str(self.servers)+' waiting='+str(self.waiting)
        commonNetgameApi.AddRepeatedTimer(10.0, sendStatus)

        mQueueTimer = commonNetgameApi.AddRepeatedTimer(1.0, self.tick)

    def OnForceReset(self, serverId, callbackId, args):
        if self.servers[serverId] == 1:
            print 'force reseted server %s' % (serverId,)
            self.servers[serverId] = 0

    def OnServerDisconnect(self, data):
        sid = data['serverId']
        if sid in self.servers:
            self.servers.pop(sid)

    def OnServerConnected(self, data):
        serverId = data['serverId']
        serverType = serverManager.GetServerType(serverId)

        print 'game connected id=%s type=%s' % (serverId, serverType)

        if 'game_unranked' in serverType:
            self.servers[serverId] = 0
            print 'recorded server %s' % serverId

        if 'Sumo' in serverType:
            print 'server is sumo!'
            self.sumoServers.append((serverType))

    def OnRecordSid(self, serverId, callbackId, args):
        return
        self.servers[serverId] = 0
        if args['specify'] == 'sumo':
            print 'recorded server is sumo mode!'
            self.sumoServers.append(serverId)

        print 'recorded server %s' % (serverId,)

    def OnRequestMatchmaking(self, serverId, callbackId, args):
        playerId = args['playerId']
        mode = args['mode']
        operation = args['operation']

        if operation == 'pre_start':
            self.waiting[mode].append(playerId)
            self.sids[playerId] = [serverId, callbackId]

    def OnCancelMatchmaking(self, serverId, callbackId, args):
        response = {
            'event': 'CancelMatchmakingEvent',
            'value': 'ok',
            'playerId': args['playerId']
        }
        self.ResponseToServer(serverId, callbackId, response)
        playerId = args['playerId']
        for queue in self.waiting:
            mode = self.waiting[queue]
            print 'cancel checking queue %s %s' % (queue, mode)
            if playerId in mode:
                print 'cancel for %s' % (playerId,)
                mode.pop(mode.index(playerId))

    def tick(self):
        for queue in self.waiting:
            mode = self.waiting[queue]
            validServers = []

            # sumo mode specific
            if queue == 'sumo':
                for server in self.servers:
                    if self.servers[server] == 0 and server in self.sumoServers:
                        validServers.append(server)
            # general mode
            else:
                for server in self.servers:
                    if self.servers[server] == 0:
                        validServers.append(server)
            if validServers:
                matchServer = random.choice(validServers)

            for player in mode:
                if len(mode) < 2 or (len(mode) % 2 == 1 and mode.index(player)+1 == len(mode)):
                    response = {
                        "event": "RequestMatchmakingEvent",
                        "value": "waiting",
                        "playerId": player,
                        "mode": queue
                    }
                    if player in self.sids:
                        print 'notify'
                        self.NotifyToServerNode(self.sids[player][0], "UpdateMatchEvent", response)
                elif len(mode) >= 2 and not validServers:
                    response = {
                        "event": "RequestMatchmakingEvent",
                        "value": "queue",
                        "playerId": player,
                        "mode": queue
                    }
                    if player in self.sids:
                        self.NotifyToServerNode(self.sids[player][0], "UpdateMatchEvent", response)
                else:
                    response = {
                        "event": "RequestMatchmakingEvent",
                        "value": "ready",
                        "playerId": player,
                        # "rivalId": queue[pos],
                        "mode": queue,
                        "server": matchServer
                    }
                    pos = mode.index(player)
                    print 'pos=%s' % (pos,)
                    if pos == 0:
                        response['rivalId'] = mode[1]
                        response['record'] = True
                        self.NotifyToServerNode(self.sids[player][0], "UpdateMatchEvent", response)
                        response['playerId'] = response['rivalId']
                        response['rivalId'] = player
                        self.NotifyToServerNode(self.sids[mode[1]][0], "UpdateMatchEvent", response)
                    else:
                        response['rivalId'] = mode[0]
                        response['record'] = True
                        self.NotifyToServerNode(self.sids[player][0], "UpdateMatchEvent", response)
                        response['playerId'] = response['rivalId']
                        response['rivalId'] = player
                        self.NotifyToServerNode(self.sids[mode[0]][0], "UpdateMatchEvent", response)

                    if player in self.sids:
                        response['rivalId'] = mode[1]
                        self.NotifyToServerNode(self.sids[player][0], "UpdateMatchEvent", response)
                    self.StartGame(response)

    def StartGame(self, args):
        if args['record']:
            sid = args['server']
            response = args
            response['matchId'] = random.randint(1000000000000000000, 9223372036854775806)
            self.NotifyToServerNode(sid, "ServiceStartOk", args)


            mode = args['mode']
            sql = 'INSERT INTO unranked (id, mode, p1, p2, date) values (%s, %s, %s, %s, %s);'
            mysqlPool.AsyncExecuteWithOrderKey('ads89a7ndsa09', sql,
                                               (response['matchId'], mode, args['playerId'], args['rivalId'], time.time() + 0))
            mWaitingList = self.waiting[mode]
            mWaitingList.pop(0)
            mWaitingList.pop(0)
            self.sids.pop(args['playerId'])
            self.sids.pop(args['rivalId'])
            self.servers[args['server']] = 1

    def OnGameEndByKill(self, serverId, callbackId, args, param="*"):
        win = args["winner"]
        lose = args["loser"]
        nickname = args['nickname']
        matchId = args["matchId"]
        self.servers[serverId] = 0

        sql = "UPDATE unranked SET winner=%s WHERE id=%s;"
        mysqlPool.AsyncExecuteWithOrderKey("OnGameEndByKill/RecordGameData", sql, (win, matchId))

        mysqlPool.AsyncExecuteWithOrderKey('asd9asdams9a', "UPDATE unrankedWin SET win=win+1 WHERE uid=%s", (win,))
        mysqlPool.AsyncExecuteWithOrderKey('asd9asdams9a', "UPDATE unrankedWin SET lose=lose+1 WHERE uid=%s", (lose,))

        self.t1(args)

    def OnGameEndByDisconnection(self, serverId, callbackId, args, param="*"):
        win = args["winner"]
        lose = args["loser"]
        nickname = args['nickname']
        matchId = args["matchId"]

        self.servers[serverId] = 0

        sql = "UPDATE unranked SET winner=%s,byDisconnection=1 WHERE id=%s;"
        mysqlPool.AsyncExecuteWithOrderKey("OnGameEndByKill/RecordGameData", sql, (win, matchId))

        mysqlPool.AsyncExecuteWithOrderKey('asd9asdams9a', "UPDATE unrankedWin SET win=win+1 WHERE uid=%s", (win,))
        mysqlPool.AsyncExecuteWithOrderKey('asd9asdams9a', "UPDATE unrankedWin SET lose=lose+1 WHERE uid=%s", (lose,))

        self.t1(args)

    # match processing
    # TODO delete after match
    def t1(self, data):

        if not(1625932800 < time.time() < 1627747199):
            return

        win = data["winner"]
        lose = data["loser"]
        nickname = data['nickname']
        matchId = data["matchId"]

        sql = 'SELECT * FROM reg WHERE uid=%s;'
        def Cb(args):
            if args:
                mysqlPool.AsyncExecuteWithOrderKey('t1match', "UPDATE t1 SET win=win+1 WHERE uid=%s;", (win,))
                mysqlPool.AsyncExecuteWithOrderKey('t1match', "UPDATE t1 SET lose=lose+1 WHERE uid=%s;", (lose,))
        mysqlPool.AsyncQueryWithOrderKey('t1matchCond', sql, (win,), Cb)
