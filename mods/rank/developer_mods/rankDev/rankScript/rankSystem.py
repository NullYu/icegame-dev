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
class rankSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()


    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self,
                            self.OnCommand)
        # self.ListenForEvent('utils', 'utilsClient', 'ActionEvent', self, self.OnClientAction)
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

    def ShowRanking(self, playerId, title, content):
        data = {
            'title': title,
            'content': content,
            'time': self.epoch2Datetime(time.time())
        }
        print 'content = %s' % (content,)
        self.NotifyToClient(playerId, "ShowRankEvent", data)

    def OnCommand(self, data):
        data['cancel'] = True
        playerId = data['entityId']
        msg = data['command'].split()
        cmd = msg[0].strip('/')

        if cmd not in ['rank', 'stats']:
            return

        if cmd == 'rank':
            if len(msg) < 2:
                self.sendMsg("你想看哪个排行榜？", playerId)
                return
            elif len(msg) > 2:
                self.sendMsg("§c无效的命令。使用/rank -h查看帮助。", playerId)
                return

            type = msg[1]

            if type == 'help' or type == '-h':
                self.sendMsg("§brank - 查看分数排行榜\n§f/rank [TYPE | help | h]\n§7可用的排行榜名称：ffa, unranked, t1", playerId)
                return

            if type == 'ffa':
                sql = 'SELECT nickname,kills,death FROM ffa ORDER BY kills DESC,death ASC LIMIT 15;'
                def Cb(args):
                    if args:
                        import sys
                        reload(sys)
                        sys.setdefaultencoding('utf8')
                        print 'ffa args=%s' % (args,)
                        content = ''
                        for i in range(len(args)):
                            if i == 0:
                                content = content+'§g♛ §f'
                            content = content + \
                                "%s  %s  %s杀  %s死\n" % (i+1, args[i][0], args[i][1], args[i][2])
                        print 'content=%s' % (content,)
                        self.ShowRanking(playerId, "FFA综合排行榜", content)
                    else:
                        self.sendMsg('rank: Error while showing ffa ranks', playerId)
                mysqlPool.AsyncQueryWithOrderKey('as89dbnasd%s'%(type,), sql, (), Cb)
            elif type == 'unranked':
                sql = 'SELECT nickname,win,lose FROM unrankedWin ORDER BY win DESC,lose ASC LIMIT 15;'
                def Cb(args):
                    if args:
                        import sys
                        reload(sys)
                        sys.setdefaultencoding('utf8')
                        print 'ffa args=%s' % (args,)
                        content = ''
                        for i in range(len(args)):
                            if i == 0:
                                content = content+'§g♛ §f'
                            content = content + \
                                "%s  %s  %s胜  %s负\n" % (i+1, args[i][0], args[i][1], args[i][2])
                        print 'content=%s' % (content,)
                        self.ShowRanking(playerId, "Unranked综合排行榜", content)
                    else:
                        self.sendMsg('rank: Error while showing unranked ranks', playerId)
                mysqlPool.AsyncQueryWithOrderKey('as89dbnasd%s'%(type,), sql, (), Cb)
            elif type == 't1':
                sql = 'SELECT nickname,win,lose FROM t1 ORDER BY win DESC,lose ASC LIMIT 15;'

                if time.time() < 1625932800:
                    self.sendMsg('比赛还没开始噢！稍后再试试吧！\n§b本场比赛开始时间为：2021-07-11 0:00:00', playerId)
                    return

                def Cb(args):
                    if args:
                        import sys
                        reload(sys)
                        sys.setdefaultencoding('utf8')
                        print 'ffa args=%s' % (args,)
                        content = ''
                        for i in range(len(args)):
                            if i == 0:
                                content = content+'§g￥200 §f'
                            content = content + \
                                "%s  %s  %s胜  %s负\n" % (i+1, args[i][0], args[i][1], args[i][2])
                        print 'content=%s' % (content,)
                        self.ShowRanking(playerId, "第一届冲榜赛排行榜\n(8月1日结束奖金￥200）", content)
                    else:
                        self.sendMsg('rank: Error while showing unranked ranks', playerId)
                mysqlPool.AsyncQueryWithOrderKey('as89dbnasd%s'%(type,), sql, (), Cb)
            else:
                self.sendMsg("§c无效的命令。使用/rank -h查看帮助。", playerId)
                return

        elif cmd == 'stats':
            if len(msg) < 2:
                self.sendMsg("你想看哪个数据？", playerId)
                return
            elif len(msg) > 2:
                self.sendMsg("§c无效的命令。使用/stats -h查看帮助。", playerId)
                return

            type = msg[1]

            if type == 'help' or type == '-h':
                self.sendMsg("§bstats - 查看您自己的分数\n§f/stats [TYPE | help | h]\n§7可用的排行榜名称：ffa", playerId)
                return

            if type == 'ffa':
                uid = lobbyGameApi.GetPlayerUid(playerId)
                sql = 'SELECT kills,death FROM ffa WHERE uid=%s;'
                def Cb(args):
                    if args:
                        data = args[0]
                        self.sendMsg('§b您的FFA数据\n§f击杀： %s\n死亡: %s\n于%s查询' % (data[0], data[1], self.epoch2Datetime(time.time())), playerId)
                    else:
                        self.sendMsg('§c查询数据失败，请稍后再试！', playerId)
                mysqlPool.AsyncQueryWithOrderKey('zcas87d021', sql, (uid,), Cb)
            else:
                self.sendMsg("§c无效的命令。使用/rank -h查看帮助。", playerId)
                return

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("lobbyutils", "lobbyutilsClient", 'TestRequest', self, self.OnTestRequest)
