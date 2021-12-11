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
class regSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()


    def ListenEvents(self):
        self.ListenForEvent('reg', 'regClient', 'ActionEvent', self, self.OnAction)
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

    ###########################

    def OnAction(self, data):
        playerId = data['playerId']
        uid = lobbyGameApi.GetPlayerUid(playerId)

        print 'player register'

        sql = 'SELECT unsafe FROM sudo WHERE uid=%s AND password!="0";'
        def Cb(args):
            if args:
                unsafe = args[0][0]
                if unsafe:
                    self.sendMsg('reg: permission denied', playerId)
                    return
                else:
                    # Start register
                    nickname = lobbyGameApi.GetPlayerNickname(playerId)
                    sql = 'INSERT INTO reg (uid, nickname, date) VALUES (%s, %s, %s);'
                    mysqlPool.AsyncExecuteWithOrderKey('xcvm80d9fn0', sql, (uid, nickname, time.time()))

                    msg = '§l§e报名成功！§rt=%s 请将本页面截图，作为比赛出现争议时的依据！' % time.time()
                    self.sendMsg(msg, playerId)
            else:
                self.sendMsg('§c§l对不起，您必须创建一个独立密码才能报名！\n§r§b使用/sudo了解如何操作', playerId)
                return
        mysqlPool.AsyncQueryWithOrderKey('xcnboisdfu897', sql, (uid,), Cb)

    def OpenRegUi(self, playerId):
        uid = lobbyGameApi.GetPlayerUid(playerId)
        if not uid:
            self.sendMsg('reg: playerId: parse error', playerId)
            return

        sql = 'SELECT * FROM reg WHERE uid=%s;'
        def Cb(args):
            data = {
                'playerId': playerId,
                'uid': uid,
                'reg': True
            }

            # TODO End of registration: 30JUN 2021 23:59:59
            if time.time() > 1625068799 and not bool(args):
                self.sendMsg('§c抱歉，报名已截至！如有问题联系service@icegame.xyz', playerId)
                return
            print 'openregui data=%s' % data
            self.NotifyToClient(playerId, "OpenRegEvent", data)
        mysqlPool.AsyncQueryWithOrderKey('ads98n7dasd', sql, (uid,), Cb)
