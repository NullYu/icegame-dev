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
import apolloCommon.redisPool as redisPool
redisPool.InitDB(30)

mysqlPool.InitDB(30)

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()


##

# 在modMain中注册的Server System类
class adminSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()


    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self,
                            self.OnCommand)
        self.ListenForEvent('admin', 'adminClient', 'ActionEvent', self, self.OnClientAction)

        commonNetgameApi.AddRepeatedTimer(6.0, self.autokick)
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

    def OnClientAction(self, data):
        print 'clientaction data=%s' % (data,)

        target = None
        playerId = data['playerId']

        if data['mode'] == 'search':
            playerId = data['playerId']
            keyword = data['keyword']
            inaccurate = data['rangeSearch']
            if inaccurate:
                target = []
                for player in serverApi.GetPlayerList():
                    if keyword in lobbyGameApi.GetPlayerNickname(player):
                        target.append(player)
                if len(target) == 1:
                    response = {
                        'uid': lobbyGameApi.GetPlayerUid(target[0]),
                        'nickname': lobbyGameApi.GetPlayerNickname(target[0]),
                        'suc': True
                    }
                    self.NotifyToClient(playerId, "SearchResultEvent", response)
                else:
                    response = {
                        'suc': False
                    }
                    self.NotifyToClient(playerId, "SearchResultEvent", response)

            else:
                for player in serverApi.GetPlayerList():
                    if lobbyGameApi.GetPlayerNickname(player) == keyword:
                        target = player
                        break
                if target:
                    response = {
                        'uid': lobbyGameApi.GetPlayerUid(target),
                        'nickname': lobbyGameApi.GetPlayerNickname(target),
                        'suc': True
                    }
                    self.NotifyToClient(playerId, "SearchResultEvent", response)
                else:
                    sql = 'SELECT uid FROM sudo WHERE nickname=%s;'
                    def Cb(args):
                        if args:
                            uid = args[0][0]#.encode('utf-8')
                            response = {
                                'uid': uid,
                                'nickname': keyword,
                                'suc': True
                            }
                            self.NotifyToClient(playerId, "SearchResultEvent", response)

                        else:
                            response = {
                                'suc': False
                            }
                            self.NotifyToClient(playerId, "SearchResultEvent", response)
                    mysqlPool.AsyncQueryWithOrderKey('asd9nasas', sql, (keyword,), Cb)

        elif data['mode'] == 'action':
            print 'ADMIN Action! data=%s' % (data,)

            target = data['target']
            reason = data['reason']
            isPerm = data['isPerm']

            sql = 'SELECT type FROM perms WHERE uid=%s AND (endDate<0 OR endDate>%s) AND type>94;'
            def Cb(args):
                if args:
                    perm = args[0][0]
                else:
                    self.sendMsg('Operation not permitted', playerId)
                    return

                duration = data['duration']
                if data['type'] == 0 or data['type'] == 1:
                    if duration:
                        try:
                            int(duration)
                        except ValueError:
                            self.sendMsg("§cfailed: duration must be int", playerId)
                            return
                    elif not isPerm:
                        self.sendMsg("§cfailed: duration required", playerId)
                        return

                if data['type'] == 0:
                    try:
                        duration = int(duration)
                    except ValueError:
                        duration = 120

                    if perm < 96 and (isPerm or duration > 120):
                        self.sendMsg(
                            'Operation not permitted',
                            playerId)
                        return

                    if isPerm:
                        duration = -1
                    else:
                        duration = time.time()+0+duration*86400

                    sql = 'INSERT INTO banData (uid, startDate, endDate, reason, executorUid) VALUES (%s, %s, %s, %s, %s);'
                    mysqlPool.AsyncExecuteWithOrderKey('asd90213nxvcfa', sql, (target, time.time()+0, duration, reason, lobbyGameApi.GetPlayerUid(playerId)))
                    self.sendMsg("§asuc", playerId)

                    victimId = lobbyGameApi.GetPlayerIdByUid(target)
                    if not victimId:
                        self.sendMsg("§eTarget player not in server! Auto-kick commences in no longer than 6 seconds.", playerId)
                        redisPool.AsyncSet('autokick-%s' % target, "1")
                        return

                    lobbyGameApi.TryToKickoutPlayer(victimId, "§9§l您因违规行为被踢出服务器！\n§r§b原因：§f%s\n\n再犯将导致更严重的惩罚！" % reason)
                    self.sendMsg("§bTried to kick player. Please double-check local server player list.", playerId)

                    self.NotifyToMaster('AnnounceBanEvent', {
                        'nickname': lobbyGameApi.GetPlayerNickname(victimId),
                        'reason': reason,
                        'sid': lobbyGameApi.GetServerId()
                    })

                elif data['type'] == 1:
                    duration = int(duration)

                    if perm < 96 and (isPerm or duration > 720):
                        self.sendMsg(
                            'Operation not permitted',
                            playerId)
                        return
                    elif perm < 97 and (isPerm or duration > 2880):
                        self.sendMsg(
                            'Operation not permitted',
                            playerId)
                        return

                    if isPerm:
                        duration = -1
                    else:
                        duration = time.time() + 0 + duration * 3600

                    sql = 'INSERT INTO muteData (uid, startDate, endDate, reason, executorUid) VALUES (%s, %s, %s, %s, %s);'
                    mysqlPool.AsyncExecuteWithOrderKey('asdm9827', sql,
                                                       (target, time.time() + 0, duration, reason, lobbyGameApi.GetPlayerUid(playerId)))
                    self.sendMsg("§asuc", playerId)

                    lobbyGameApi.TryToKickoutPlayer(lobbyGameApi.GetPlayerIdByUid(target), '§6与服务器断开连接')

                elif data['type'] == 2:
                    if perm < 95:
                        self.sendMsg(
                            'Operation not permitted',
                            playerId)
                        return

                    msg = "§9§l您因违规行为被踢出服务器！\n§r§b原因：§f%s\n再犯将导致更严重的惩罚！\n§e§l若要举报滥用权限请截图§r§7[%s]" % (reason, int(time.time()))
                    lobbyGameApi.TryToKickoutPlayer(lobbyGameApi.GetPlayerIdByUid(target), msg)
                    self.sendMsg("§asuc. Operation was not recorded.", playerId)

            mysqlPool.AsyncQueryWithOrderKey('sdans89d70as', sql, (lobbyGameApi.GetPlayerUid(playerId), time.time()), Cb)


    def OnCommand(self, data):
        data['cancel'] = True
        playerId = data['entityId']
        uid = lobbyGameApi.GetPlayerUid(playerId)
        msg = data['command'].split()
        cmd = msg[0].strip('/')

        if not cmd == 'admin':
            return

        sql = 'SELECT * FROM perms WHERE uid=%s AND type>94 AND (endDate>%s OR endDate<0);'
        def Cb(args):
            if args:
                self.NotifyToClient(playerId, "ShowAdminEvent", None)
            else:
                self.sendMsg('admin: Operation not permitted', playerId)

        mysqlPool.AsyncQueryWithOrderKey('admin%s' % (uid,), sql, (uid, time.time()+0), Cb)

    def autokick(self):
        for player in serverApi.GetPlayerList():
            uid = lobbyGameApi.GetPlayerUid(player)
            def Cb(args):
                if args:
                    lobbyGameApi.TryToKickoutPlayer(player, "§6与服务器断开连接")
                    redisPool.AsyncDelete('autokick-%s' % uid)

                    utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
                    utilsSystem.CreateAdminMessage("§a%s#%s was banned remotely" % (lobbyGameApi.GetPlayerNickname(player), uid))

            redisPool.AsyncGet("autokick-%s" % uid, Cb)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("lobbyutils", "lobbyutilsClient", 'TestRequest', self, self.OnTestRequest)
