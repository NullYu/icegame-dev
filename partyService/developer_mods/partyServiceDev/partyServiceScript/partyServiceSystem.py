# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServiceApi as serviceApi
import apolloCommon.mysqlPool as mysqlPool
import time
import random
import json
import service.serverManager as serverManager
import apolloCommon.commonNetgameApi as commonNetgameApi
import service.serviceConf as serviceConf
import apolloCommon.redisPool as redisPool
redisPool.InitDB(30)

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serviceApi.GetServiceSystemCls()

# 在modMain中注册的Server System类
class partyServiceSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        print 'INIT namespace='+namespace+' systemName='+systemName
        self.RegisterRpcMethod("party", 'LobbyNodeCommEvent', self.OnLobbyNodeComm)
        self.RegisterRpcMethodForMod('LobbyNodeCommEvent', self.OnLobbyNodeComm)

        self.ListenForEvent(serviceApi.GetEngineNamespace(), serviceApi.GetEngineSystemName(), "ServerConnectedEvent", self, self.OnServerConnected)
        self.ListenForEvent(serviceApi.GetEngineNamespace(), serviceApi.GetEngineSystemName(), "ServerDisconnectEvent", self, self.OnServerDisconnect)

        self.partys = {}
        self.perms = {}
        self.servers = []

        self.mSrcPartyStatus = None

    def item2Index(self, li, value):
        try:
            return li.index(value)
        except ValueError:
            return -1

    def OnServerConnected(self, data):
        sid = data['serverId']
        self.servers.append(sid)

    def OnServerDisconnect(self, data):
        sid = data['serverId']
        if sid in self.servers:
            self.servers.pop(self.servers.index(sid))

    def OnLobbyNodeComm(self, serverId, callbackId, data):
        print 'OnLobbyNodeComm args=%s' % (data,)

        operation = data['operation']

        if operation == 'makePartyInit':
            srcUid = data['src']
            targetNickname = data['targetNickname']

            self.mSrcPartyStatus = None
            def Cb(args):
                self.mSrcPartyStatus = args
            redisPool.AsyncGet("partyStatus-%s" % srcUid, Cb)

            if self.mSrcPartyStatus:
                response = {
                    'uid': srcUid,
                    'operation': 'msg',
                    'content': '§e你已经在一个队伍里了'
                }
                self.NotifyToServerNode(serverId, "ServiceCommEvent", response)
                return

            response = {
                'operation': 'searchForPlayer',
                'subOperation': 'makeParty',
                'srcUid': srcUid,
                'targetNickname': targetNickname,
                'srcSid': serverId,
                'srcNick': data['srcNick']
            }
            for server in self.servers:
                self.NotifyToServerNode(server, "ServiceCommEvent", response)

        elif operation == 'searchForPlayer':
            subOperation = data['subOperation']

            if subOperation == 'makeParty':
                srcUid = data['srcUid']
                targetUid = data['targetUid']
                srcSid = data['srcSid']
                targetSid = data['targetSid']

                self.mSrcPartyStatus = None
                def Cb(args):
                    self.mSrcPartyStatus = args
                redisPool.AsyncGet("partyStatus-%s" % targetUid, Cb)

                if self.mSrcPartyStatus:
                    response = {
                        'uid': srcUid,
                        'operation': 'msg',
                        'content': '§c该玩家已经在一个队伍里了。您必须使用-apply参数。'
                    }
                    self.NotifyToServerNode(srcSid, "ServiceCommEvent", response)
                    return

                # def a(conn):
                #     conn.set('partyApply-%s' % targetUid, srcUid)
                #     conn.expire('partyApply-%s' % targetUid, (60, 'NX'))
                # def Cb(args):
                #     return
                # redisPool.AsyncFuncWithKey(a, "party-api-%s" % (targetUid,), Cb)

                redisPool.AsyncSet('partyApply-%s' % targetUid, srcUid)

                response = {
                    'uid': srcUid,
                    'operation': 'msg',
                    'content': '§a已发送请求。对方有60秒时间接受。'
                }
                self.NotifyToServerNode(srcUid, "ServiceCommEvent", response)
                response = {
                    'uid': targetUid,
                    'operation': 'msg',
                    'content': '§l§6%s想与您组队。§r§e在60秒内输入§b/p -p true§e以接受, §b/p -p false§e以拒绝。' % data['srcNick']
                }
                self.NotifyToServerNode(targetSid, "ServiceCommEvent", response)

        elif operation == 'partyAccept':
            srcUid = data['srcUid']
            targetUid = data['targetUid']
            redisPool.AsyncDelete('partyApply-%s' % targetUid)

            self.mSrcPartyStatus = None
            def Cb(args):
                self.mSrcPartyStatus = args
            redisPool.AsyncGet("partyStatus-%s" % targetUid, Cb)

            if self.mSrcPartyStatus:
                # join the player into the existing party
                pass
            else:
                # create a new party.
                # redis record format: [partyId-#]: {playerId: perms}
                partyInfo = {
                    srcUid: 1,
                    targetUid: 2
                }
                redisPool.AsyncSet("partyId")

                def a(conn):
                    conn.key('*partyApply*')
                def Cb(args):
                    print 'key *partyApply* = ', args
                    createPartyId = len(args) + 1
                    createPartyContent = json.dumps(partyInfo)
                    redisPool.AsyncSet('partyId-%s' % createPartyId, createPartyContent)

                    response = {
                        'operation': 'searchForPlayer',
                        'subOperation': 'msg',
                        'uid': srcUid,
                        'content': '§l§a成功创建车队§r§d#%s§l§a， 队长是§r§6%s§l§a。已自动为您加入车队。' % (createPartyId, targetUid)
                    }
                    for server in self.servers:
                        self.NotifyToServerNode(server, "ServiceCommEvent", response)

                    response = {
                        'operation': 'searchForPlayer',
                        'subOperation': 'msg',
                        'uid': targetUid,
                        'content': '§l§a成功创建车队§r§d#%s§l§a，队长是您。目前的成员是§r§6%s§l§a。' %  (createPartyId, srcUid)
                    }
                    for server in self.servers:
                        self.NotifyToServerNode(server, "ServiceCommEvent", response)

                    redisPool.AsyncDelete('partyApply-%s' % targetUid)

                redisPool.AsyncFuncWithKey(a, "party-api-%s" % (targetUid,), Cb)
        elif operation == 'partyDeny':
            srcUid = data['srcUid']
            targetUid = data['targetUid']
            redisPool.AsyncDelete('partyApply-%s' % targetUid)

            response = {
                'operation': 'searchForPlayer',
                'subOperation': 'msg',
                'uid': srcUid,
                'content': '§l§c申请被拒绝'
            }
            for server in self.servers:
                self.NotifyToServerNode(server, "ServiceCommEvent", response)
