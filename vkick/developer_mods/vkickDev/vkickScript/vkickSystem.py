# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import json
import math
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
class vkickSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        self.ayeVotes = 0
        self.nayVotes = 0
        self.lastVote = 0

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self,
                            self.OnCommand)
        self.ListenForEvent('vkick', 'vkickClient', 'ActionEvent', self, self.OnClientAction)
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

    def OnClientAction(self, data):
        print 'update vote'
        playerId = data['playerId']
        if data['vote']:
            self.ayeVotes += 1
        else:
            self.nayVotes += 1

        self.UpdateVote()

    def UpdateVote(self):
        data = {
            'aye': self.ayeVotes,
            'nay': self.nayVotes
        }
        for player in serverApi.GetPlayerList():
            self.NotifyToClient(player, 'UpdateVote', data)

    def ConcludeVote(self, target):
        if self.ayeVotes > (self.nayVotes + self.ayeVotes)*(2/3.0):
            suc = True
        else:
            suc = False
        print 'vote done, suc=', suc
        for player in serverApi.GetPlayerList():
            self.NotifyToClient(player, 'EndVote', suc)

        if suc:
            commonNetgameApi.AddTimer(3.0, lambda p: lobbyGameApi.TryToKickoutPlayer(p, "被投票踢出"), target)

        sql = 'INSERT INTO votekick (uid, aye, nay, result, date) VALUES (%s, %s, %s, %s, %s);'
        mysqlPool.AsyncExecuteWithOrderKey('asd1je91dsdas', sql, (
            lobbyGameApi.GetPlayerUid(target),
            self.ayeVotes,
            self.nayVotes,
            int(suc),
            time.time()
        ))

    def OnCommand(self, data):
        data['cancel'] = True
        playerId = data['entityId']
        msg = data['command'].split()
        cmd = msg[0].strip('/')
        if cmd not in ['vk', 'votekick', 'vkick']:
            return

        if len(msg) > 1 and msg[1] == '-h'.lower():
            self.sendMsg('§bvotekick - 投票踢出一名玩家\n§f/votekick [玩家名关键词] [原因]\n§7根据关键词搜索玩家，选中昵称内包含关键词的玩家。', playerId)
            return

        if len(msg) != 3:
            self.sendMsg('§c无效的命令。使用/votekick -h查看帮助。\n请确保您的投票原因中不包含空格。', playerId)
            return
        elif len(serverApi.GetPlayerList()) < 2:
            self.sendMsg('§e本房间只有您自己，不能投票。', playerId)
            return
        elif self.lastVote and time.time()-self.lastVote < 40:
            self.sendMsg('§c该房间还有%s秒才能再次投票' % (int(math.floor(time.time()-self.lastVote,))), playerId)
            return

        keyword = msg[1]
        target = None
        mTargetCount = 0
        for player in serverApi.GetPlayerList():
            name = lobbyGameApi.GetPlayerNickname(player)
            if player != playerId and keyword in name:
                target = player
                mTargetCount += 1

        if not target:
            self.sendMsg('§e没有找到该玩家，尝试换一个关键词!', playerId)
            return
        elif mTargetCount != 1:
            self.sendMsg('§e找到的玩家过多，尝试使用更长的关键词!', playerId)
            print 'try to call vote targetCounts=', mTargetCount
            return

        # start vote
        for player in serverApi.GetPlayerList():
            response = {
                'playerId': player,
                'target': target,
                'nickname': lobbyGameApi.GetPlayerNickname(target),
                'source': playerId,
                'reason': msg[2]
            }
            self.NotifyToClient(player, 'StartVote', response)

            self.ayeVotes = 1
            self.nayVotes = 1
            self.UpdateVote()

            commonNetgameApi.AddTimer(15.0, self.ConcludeVote, target)
            self.lastVote = time.time()
            # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("lobbyutils", "lobbyutilsClient", 'TestRequest', self, self.OnTestRequest)
