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

mysqlPool.InitDB(30)

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()


##

# 在modMain中注册的Server System类
class v5matchSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        self.inQueue = []
        self.uids = {}

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self, self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self, self.OnAddServerPlayer)
        self.ListenForEvent('v5match', 'v5matchClient', 'ActionEvent', self, self.OnClientAction)
        self.ListenForEvent('v5Service', 'v5Service', 'UpdateMatchInfoEvent', self, self.OnUpdateMatchInfo)
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

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        uid = lobbyGameApi.GetPlayerUid(playerId)
        self.uids[playerId] = uid

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        if playerId in self.inQueue:
            self.inQueue.pop(self.inQueue.index(playerId))
            self.ExitPlayerQueue(playerId)

        self.uids.pop(playerId)

    def OnClientAction(self, data):
        print 'onclientaction'
        playerId = data['playerId']
        operation = data['operation']

        if operation == 'start':
            self.StartPlayerQueue(playerId)

        elif operation == 'exit':
            self.ExitPlayerQueue(playerId)

    def StartPlayerQueue(self, playerId):
        uid = lobbyGameApi.GetPlayerUid(playerId)
        response = {
            'playerId': playerId,
            'uid': uid
        }
        self.RequestToServiceMod("v5", "StartMatchmakingEvent", response, self.StartPlayerQueueCb)

    def StartPlayerQueueCb(self, suc, data):
        if suc and data['suc']:
            playerId = data['playerId']

            self.inQueue.append(playerId)
            self.NotifyToClient(playerId, 'StartMatchmakeEvent', None)

        elif suc:
            self.sendMsg('§c无法连接匹配服务，请稍等后再试', data['playerId'])

    def ExitPlayerQueue(self, playerId):
        uid = self.uids[playerId]
        response = {
            'playerId': playerId,
            'uid': uid
        }
        self.RequestToServiceMod("v5", "ExitMatchmakingEvent", response, self.ExitPlayerQueueCb)

    def ExitPlayerQueueCb(self, suc, data):
        print 'exit rcv'
        if suc and data['suc']:
            playerId = data['playerId']

            if playerId not in self.inQueue:
                self.sendMsg('§c请求被拒绝，请稍等后再试', playerId)
                return

            self.inQueue.pop(self.inQueue.index(playerId))
            self.NotifyToClient(playerId, 'ExitMatchmakeEvent', None)

        elif suc:
            self.sendMsg('§c无法连接匹配服务，请稍等后再试', data['playerId'])

    def OnUpdateMatchInfo(self, data):
        uid = data['uid']
        playerId = lobbyGameApi.GetPlayerIdByUid(uid)
        if playerId:
            status = data['status']
            count = data['count']

            if status == 'wait':
                response = {
                    'status': 'wait',
                    'count': count
                }
                self.NotifyToClient(playerId, 'UpdateInfoEvent', response)

            elif status == 'start':
                response = {
                    'status': 'start',
                    'count': count
                }
                self.NotifyToClient(playerId, 'UpdateInfoEvent', response)
                self.StartMatch(playerId, data['sid'])

    def StartMatch(self, playerId, serverId):
        print 'starting match'
        def a(tup):
            transData = {'position': [1, 2, 3]}
            lobbyGameApi.TransferToOtherServerById(tup[0], tup[1], json.dumps(transData))

        commonNetgameApi.AddTimer(6.0, a, (playerId, serverId))
        musicSystem = serverApi.GetSystem('music', 'musicSystem')
        musicSystem.PlayMusicToPlayer(playerId, 'sfx.v5match.start', False)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("lobbyutils", "lobbyutilsClient", 'TestRequest', self, self.OnTestRequest)
