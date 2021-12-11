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

# Status codes:
# 0=ok
# 1=in game
# 2=down

servers = {}
waiting = {
    "s2p2": [],
    "sumo": [],
    "nor": [],
    "buhc": [],
    "archer": [],
    "combo": [],
    "totem": []
}
mSid = {}

# 在modMain中注册的Server System类
class unrankedServiceSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        print 'INIT namespace='+namespace+' systemName='+systemName
        self.RegisterRpcMethod("matchmaking", 'RequestMatchmakingEvent', self.OnRequestMatchmaking)
        self.RegisterRpcMethod("matchmaking", 'CancelMatchmakingEvent', self.OnCancelMatchmaking)
        self.RegisterRpcMethod("matchmaking", 'NotifyStartGameEvent', self.OnNotifyStartGame)
        self.RegisterRpcMethod("matchmaking", 'GameEndByKillEvent', self.OnGameEndByKill)
        self.RegisterRpcMethod("matchmaking", 'GameEndByDisconnectionEvent', self.OnGameEndByDisconnection)
        self.RegisterRpcMethod("matchmaking", 'RecordSidEvent', self.OnRecordSid)
        self.RegisterRpcMethod("matchmaking", 'ForceReset', self.OnForceReset)

        def sendStatus():
            print 'Server sendStatus servers='+str(servers)+' waiting='+str(waiting)
        commonNetgameApi.AddRepeatedTimer(10.0, sendStatus)

        mQueueTimer = commonNetgameApi.AddRepeatedTimer(1.0, self.checkMatchmaking)

    def item2Index(self, li, value):
        try:
            return li.index(value)
        except ValueError:
            return -1

    def OnRecordSid(self, serverId, callbackId, args):
        sid = args['sid']
        servers[sid] = 0

        response = {
            "sid": sid,
        }
        print('Updated/record game/unranked game server: sid='+str(sid))
        self.ResponseToServer(serverId, callbackId, response)

    def OnForceReset(self, serverId, callbackId, args):
        servers[serverId] = 0
        print 'CALL OnForceReset'

    def OnRequestMatchmaking(self, serverId, callbackId, args, param="*"):
        playerId = args['playerId']
        mode = args['mode']
        operation = args['operation']

        if operation == "pre_start":
            if mode in waiting.keys():
                waiting[mode].append(playerId)
                mSid[playerId] = serverId

    def checkMatchmaking(self):
        for mode in waiting:
            if len(waiting[mode]) > 0:
                queue = waiting[mode]
                if queue:
                    print 'queue='+str(queue)
                else:
                    print 'queue empty'

                for playerId in waiting[mode]:
                    okServers = []
                    if servers:
                        for item in servers:
                            if servers[item] == 0:
                                okServers.append(item)
                    pos = self.item2Index(queue, playerId) + 1
                    if not pos:
                        break
                    serverId = mSid[playerId]
                    if len(queue) < 2 or (pos == len(queue) and len(queue)%2 == 1):
                        response = {
                            "event": "RequestMatchmakingEvent",
                            "value": "waiting",
                            "playerId": playerId,
                            "mode": mode
                        }
                        self.NotifyToServerNode(serverId, "CheckMatchmakingEvent", response)
                    elif len(okServers) < 1:
                        response = {
                            "event": "RequestMatchmakingEvent",
                            "value": "queue",
                            "playerId": playerId,
                            "mode": mode
                        }
                        self.NotifyToServerNode(serverId, "CheckMatchmakingEvent", response)
                    elif pos <= 2:
                        if pos == 1:
                            response = {
                                "event": "RequestMatchmakingEvent",
                                "value": "ready",
                                "playerId": playerId,
                                "rivalId": queue[pos],
                                "mode": mode,
                                "server": random.choice(okServers)
                            }
                            global response
                        elif pos == 2:
                            response = {
                                "event": "RequestMatchmakingEvent",
                                "value": "ready",
                                "playerId": playerId,
                                "rivalId": queue[pos-2],
                                "mode": mode,
                                "server": random.choice(okServers)
                            }
                            global response

                    self.NotifyToServerNode(serverId, "CheckMatchmakingEvent", response)


    def OnCancelMatchmaking(self, serverId, callbackId, args, params="*"):
        playerId = args["playerId"]
        for item in waiting:
            if playerId in waiting[item]:
                waiting[item].pop(self.item2Index(waiting[item], playerId))
                response = {
                    "playerId": playerId,
                    "event": "CancelMatchmakingEvent",
                    "value": "ok"
                }
                self.ResponseToServer(serverId, callbackId, response)
                break

    def OnNotifyStartGame(self, serverId, callbackId, args, param="*"):
        print 'CALL OnNotifyStartGame args='+str(args)

        p1 = args["p1"]
        p1uid = args["p1uid"]
        p2 = args["p2"]
        p2uid = args["p2uid"]
        mode = args["mode"]
        server = args["server"]
        matchId = 0
        queue = waiting[mode]
        try:
            queue.pop(self.item2Index(queue, p1))
        except IndexError:
            pass
        try:
            queue.pop(self.item2Index(queue, p2))
        except IndexError:
            pass

        response = {
            "event": "NotifyStartGameEvent",
            "value": 1
        }
        def Cb(args):
            print str(args)
            # if len(args) == 1:
            #     matchId = args[0]

        self.ResponseToServer(serverId, callbackId, response)
        servers[server] = 1
        args = {
            "player1Id": p1,
            "player2Id": p2,
            "mode": mode,
            "matchId": matchId
        }
        self.NotifyToServerNode(server, "ServiceStartOk", args)

        sql = "INSERT INTO unranked (mode, p1, p2, date) VALUES ('s2p2', %s, %s, %s);"
        mysqlPool.AsyncQueryWithOrderKey('OnNotifyStartGame/InitGameRecords', sql, (p1uid, p2uid, time.time()), Cb)

        print 'OnNotifyStartGame/ServiceStartOk server='+str(server)

    def OnGameEndByKill(self, serverId, callbackId, args, param="*"):
        win = args["winner"]
        lose = args["loser"]
        nickname = args['nickname']
        matchId = args["matchId"]
        servers[serverId] = 0

        sql = "UPDATE unranked SET winner=%s,loser=%s WHERE id=%s;"
        mysqlPool.AsyncExecuteWithOrderKey("OnGameEndByKill/RecordGameData", sql, (win, nickname, lose, matchId))

        mysqlPool.AsyncExecuteWithOrderKey('asd9asdams9a', "UPDATE unranked SET win=win+1 WHERE uid=%s", (win,))
        mysqlPool.AsyncExecuteWithOrderKey('asd9asdams9a', "UPDATE unranked SET lose=lose+1 WHERE uid=%s", (lose,))

    def OnGameEndByDisconnection(self, serverId, callbackId, args, param="*"):
        win = args["winner"]
        lose = args["loser"]
        nickname = args['nickname']
        matchId = args["matchId"]

        servers[serverId] = 0

        sql = "UPDATE unranked SET winner=%s,loser=%s, byDisconnection=1 WHERE id=%s;"
        mysqlPool.AsyncExecuteWithOrderKey("OnGameEndByKill/RecordGameData", sql, (win, nickname, lose, matchId))

        mysqlPool.AsyncExecuteWithOrderKey('asd9asdams9a', "UPDATE unranked SET win=win+1 WHERE uid=%s", (win,))
        mysqlPool.AsyncExecuteWithOrderKey('asd9asdams9a', "UPDATE unranked SET lose=lose+1 WHERE uid=%s", (lose,))
