# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import math
import json
import datetime
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.mysqlPool as mysqlPool
import apolloCommon.commonNetgameApi as commonNetgameApi
mysqlPool.InitDB(30)

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()


# 在modMain中注册的Server System类
class banServerSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvent()

        self.roomLock = None

    def ListenEvent(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self,
                            self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self,
                            self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self,
                            self.OnCommand)
        self.ListenForEvent('shout', 'shoutMasterSystem', 'DisplayRefreshBanEvent', self, self.OnDisplayRefreshBan)
        self.ListenForEvent('shout', 'shoutMasterSystem', 'DisplayHlabaEvent', self, self.OnDisplayHlaba)

        def a(li):
            for player in li:
                self.CheckBan(player)
                print 'checked ban.'
        commonNetgameApi.AddRepeatedTimer(6.0, a, serverApi.GetPlayerList())

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("ban", "banClient", 'TestRequest', self, self.OnTestRequest)

    ##############UTILS##############

    def sendCmd(self, cmd, playerId):
        comp = serverApi.GetEngineCompFactory().CreateCommand(serverApi.GetLevelId())
        comp.SetCommand(cmd, playerId)

    def epoch2Datetime(self, epoch):
        ts = datetime.datetime.fromtimestamp(int(epoch))
        return ts.strftime('%Y-%m-%d %H:%M:%S')

    def sendTitle(self, title, type, playerId):
        if (type == 1):
            self.sendCmd("/title @s title " + title, playerId)
        elif (type == 2):
            self.sendCmd("/title @s subtitle " + title, playerId)
        elif (type == 3):
            self.sendCmd("/title @s actionbar " + title, playerId)
        else:
            print 'invalid params for call/sendTitle(): type'

    def sendMsg(self, msg, playerId):
        comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
        comp.NotifyOneMessage(playerId, msg, "§f")

    def forceSelect(self, slot, playerId):
        # print 'forceSelect called slot='+slot+' playerId='+playerId
        comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
        comp.ChangeSelectSlot(slot)

    #################################

    def CheckBan(self, playerId):
        uid = lobbyGameApi.GetPlayerUid(playerId)

        sql = 'SELECT * FROM banData WHERE uid=%s AND (endDate>%s OR endDate<1) AND valid=1;'
        def Cb(args):
            if args:
                data = args[0]
                banId = data[0]
                endDate = data[4]
                reason = data[5]

                compose = [banId, lobbyGameApi.GetPlayerNickname(playerId), endDate, reason]

                print 'ban enddate=%s' % endDate

                if int(endDate) < 1:
                    msg = '§c§l账号被永久禁止登录游戏§r\n§bBAN ID§r: %s\n§bIGN§r: %s\n§a(发送电子邮件至icegame.net.cn/appeal以申诉)' % (compose[0], compose[1])
                else:
                    msg = '§c§l账号被禁止登录游戏§r\n§bBAN ID§r: %s\n§bIGN§r: %s\n§b解封日期§r: %s\n§a(访问icegame.net.cn/appeal以申诉)' % (compose[0], compose[1], self.epoch2Datetime(compose[2]))

                lobbyGameApi.TryToKickoutPlayer(playerId, msg)
                print '!!!!!!KICKING OUT %S!!!!!!' % playerId

        mysqlPool.AsyncQueryWithOrderKey('checkban%s' % uid, sql, (uid,time.time()), Cb)

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        self.CheckBan(playerId)

        if self.roomLock:
            sql = 'SELECT * FROM perms WHERE uid=%s AND type>=95 AND (endDate < 0 OR endDate > %s);'
            def Cb(args):
                if not args:
                    lobbyGameApi.TryToKickoutPlayer(playerId, 'This room is not accepting new players.')
            mysqlPool.AsyncQueryWithOrderKey('czx9ay9sd8h', sql, (lobbyGameApi.GetPlayerUid(playerId), time.time()), Cb)

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        if playerId == self.roomLock:
            self.roomLock = None
            utils = serverApi.GetSystem('utils', 'utilsSystem')
            utils.CreateAdminMessage('§l§6!!! %s disabled room lock for server %s' % (
            lobbyGameApi.GetPlayerNickname(playerId), lobbyGameApi.GetServerId()))

    def OnDisplayRefreshBan(self, args):
        nick = args['nick']
        uid = args['uid']
        executor = args['executor']
        msg = "§a%s 封禁了 %s#%s" % (executor, nick, uid)

        utils = serverApi.GetSystem('utils', 'utilsSystem')
        utils.CreateAdminMessage(msg)

        victim = lobbyGameApi.GetPlayerIdByUid(int(uid))
        if victim:
            lobbyGameApi.TryToKickoutPlayer(victim, '§6与服务器断开连接')

    def OnDisplayHlaba(self, args):
        print 'ondisplayhlaba args=%s' % (args,)
        nick = args['nick']
        content = args['msg']
        sid = args['sid']
        sname = args['sname']

        msg = "§c§lHELPER-CHANNEL:§f %s@%s-%s: §r§a%s" % (nick, sname, sid, content)

        utils = serverApi.GetSystem('utils', 'utilsSystem')
        utils.CreateAdminMessage(msg)

    def OnCommand(self, data):
        playerId = data['entityId']
        msg = data['command'].split()
        cmd = msg[0].strip('/')
        uid = str(lobbyGameApi.GetPlayerUid(playerId))

        if cmd == "ban":
            data['cancel'] = True
            timeNow = time.time()+0
            sql = 'SELECT endDate FROM perms WHERE uid=%s and type >= 96'

            if '-h' in data['command']:
                self.sendMsg('Usage: /ban <victim> <duration: day; -1=perm-ban> <reason>')

            def CallBack(args):
                print 'CALL OnCommand/ban checkban args='+str(args)
                if not args:
                    self.sendMsg('ban: Operation not permitted', playerId)
                else:
                    data = args[0]
                    endDate = int(str(data[0]).strip("L"))
                    if endDate < timeNow and endDate > -1:
                        self.sendMsg('ban: Operation not permitted', playerId)
                        sql = 'UPDATE perms SET type=1 WHERE uid=%s'
                        def Cb(args):
                            pass
                        mysqlPool.AsyncExecuteWithOrderKey('player', sql, (uid,), Cb)
                    else:
                        if len(msg) != 4:
                            self.sendMsg('§einvalid command', playerId)
                        else:
                            victim = msg[1]
                            time = 0
                            if int(msg[2]) > 0:
                                time += int(msg[2])*86400
                                time += int(math.floor(timeNow))
                            else:
                                time -= 1
                            reason = msg[3]
                            if victim in serverApi.GetPlayerList():
                                for player in serverApi.GetPlayerList():
                                    if lobbyGameApi.GetPlayerNickname(player) == victim:
                                        victim = lobbyGameApi.GetPlayerUid(player)
                            sql = "INSERT INTO banData (id, uid, ip, startDate, endDate, reason, executorUid, valid, isIpBan) values (0, %s, '1', 0, %s, %s, 0, 1, 0)"
                            def Cb(args):
                                pass
                            mysqlPool.AsyncExecuteWithOrderKey('player', sql,
                                                               (victim, time, reason), Cb)

                            data = {
                                'nick': lobbyGameApi.GetPlayerNickname(lobbyGameApi.GetPlayerIdByUid(int(victim))),
                                'uid': victim,
                                'executor': lobbyGameApi.GetPlayerNickname(playerId)
                            }
                            self.NotifyToMaster("RefreshBanEvent", data)

            mysqlPool.AsyncQueryWithOrderKey("OnRequestBan/CheckExecutorPerms", sql, (uid,), CallBack)

        elif cmd == "mute":
            data['cancel'] = True
            timeNow = time.time()+0
            sql = 'SELECT endDate FROM perms WHERE uid=%s and type >= 96'

            if '-h' in data['command']:
                self.sendMsg('Usage: /mute <victim> <duration: hours; -1=perm-mute> <reason>')

            def CallBack(args):
                print 'CALL OnCommand/ban checkban args='+str(args)
                if not args:
                    self.sendMsg('mute: Operation not permitted', playerId)
                else:
                    data = args[0]
                    endDate = int(str(data[0]).strip("L"))
                    if endDate < timeNow and endDate > -1:
                        self.sendMsg('mute: Operation not permitted', playerId)
                        sql = 'UPDATE perms SET type=1 WHERE uid=%s'
                        def Cb(args):
                            pass
                        mysqlPool.AsyncExecuteWithOrderKey('player', sql, (uid,), Cb)
                    else:
                        if len(msg) != 4:
                            self.sendMsg('§einvalid command', playerId)
                        else:
                            victim = msg[1]
                            time = 0
                            if int(msg[2]) > 0:
                                time += int(msg[2])*3600
                                time += int(math.floor(timeNow))
                            else:
                                time -= 1
                            reason = msg[3]
                            if victim in serverApi.GetPlayerList():
                                for player in serverApi.GetPlayerList():
                                    if lobbyGameApi.GetPlayerNickname(player) == victim:
                                        victim = lobbyGameApi.GetPlayerUid(player)
                            sql = "INSERT INTO muteData (uid, endDate, reason) values (%s, %s, %s)"
                            def Cb(args):
                                pass
                            mysqlPool.AsyncExecuteWithOrderKey('player', sql,
                                                               (lobbyGameApi.GetPlayerUid(victim), endDate, reason), Cb)

            mysqlPool.AsyncQueryWithOrderKey("OnRequestBan/CheckExecutorPerms", sql, (uid,), CallBack)

        elif cmd == "stage":
            sql = 'SELECT * FROM perms WHERE uid=%s AND (type>=95 OR 2<=type<=6) AND (endDate<0 OR endDate>%s);'
            def Cb(args):
                if not args:
                    self.sendMsg('stage: Operation not permitted', playerId)
                    return
                else:
                    if (msg[1] == 'join') and len(msg) == 3:
                        try:
                            value = int(msg[2])
                        except ValueError:
                            self.sendMsg("§einvalid command: serverId must be integer", playerId)
                            return
                        transData = {"position": [1, 2, 3], "isAdmin": True}
                        #lobbyGameApi.TransferToOtherServerById(playerId, value, json.dumps(transData))

                        # TODO debug only - remove all players and change from PLAYER to PLAYERID
                        for player in serverApi.GetPlayerList():
                            lobbyGameApi.TransferToOtherServerById(player, value, json.dumps(transData))
                    elif (msg[1] == 'fast') and len(msg) == 2:
                        serverType = commonNetgameApi.GetServerType()
                        if serverType == 'game_bts' and len(serverApi.GetPlayerList()) > 1:
                            (serverApi.GetSystem("bts", "btsSystem")).FastStart()
                        elif serverType == 'game_cparty' and len(serverApi.GetPlayerList()) > 1:
                            (serverApi.GetSystem("cparty", "cpartySystem")).FastStart()
                        elif serverType == 'game_manhunt' and len(serverApi.GetPlayerList()) > 2:
                            (serverApi.GetSystem("manhunt", "manhuntSystem")).FastStart()
                        elif 'bw' in serverType and len(serverApi.GetPlayerList()) > 1:
                            (serverApi.GetSystem("bw", "bwSystem")).countdown = 15
                        elif 'fb' in serverType and len(serverApi.GetPlayerList()) > 1:
                            (serverApi.GetSystem("fb", "fbSystem")).countdown = 15
                        elif serverType == 'game_sw' and len(serverApi.GetPlayerList()) > 1:
                            (serverApi.GetSystem("sw", "swSystem")).countdown = 15
                        elif 'tntr' in serverType and len(serverApi.GetPlayerList()) > 1:
                            (serverApi.GetSystem("tntr", "tntrSystem")).countdown = 15
                        elif 'mm' in serverType and len(serverApi.GetPlayerList()) > 2:
                            (serverApi.GetSystem("mm", "mmSystem")).countdown = 15
                        else:
                            self.sendMsg("stage: cannot boost current room", playerId)

                    else:
                        self.sendMsg("§einvalid command", playerId)

            mysqlPool.AsyncQueryWithOrderKey("stageCommand/CheckExecutorPerms", sql, (uid, time.time()), Cb)

        elif cmd == "roomlock" or cmd == "rl":
            sql = 'SELECT * FROM perms WHERE uid=%s AND type>=95 AND (endDate<0 OR endDate>%s);'
            def Cb(args):
                if not args:
                    self.sendMsg('stage: Operation not permitted', playerId)
                    return
                else:
                    if len(msg) < 2:
                        if self.roomLock:
                            self.sendMsg('room lock enabled for this server', playerId)
                        else:
                            self.sendMsg('room lock NOT enabled for this server', playerId)
                    elif msg[1] == 'on':
                        if not self.roomLock:
                            self.roomLock = playerId
                            utils = serverApi.GetSystem('utils', 'utilsSystem')
                            utils.CreateAdminMessage('§l§6!!! %s enabled room lock for server %s' % (lobbyGameApi.GetPlayerNickname(playerId), lobbyGameApi.GetServerId()))
                        else:
                            self.sendMsg('room lock already on!', playerId)

                    elif msg[1] == 'off':
                        if self.roomLock:
                            self.roomLock = None
                            utils = serverApi.GetSystem('utils', 'utilsSystem')
                            utils.CreateAdminMessage('§l§6!!! %s disabled room lock for server %s' % (lobbyGameApi.GetPlayerNickname(playerId), lobbyGameApi.GetServerId()))
                        else:
                            self.sendMsg('room lock not enabled', playerId)

            mysqlPool.AsyncQueryWithOrderKey("roomlockCommand/CheckExecutorPerms", sql, (uid, time.time()), Cb)

        elif cmd in ['transfer', 'transf', 'trans']:
            print 'player using transfer'
            sql = 'SELECT * FROM perms WHERE uid=%s and 2<=type<=5 and (endDate<0 OR endDate>%s);'
            def Cb(args):
                if args:
                    if len(msg) != 2:
                        self.sendMsg("/transfer -h", playerId)
                        return
                    elif msg[1].lower() == '-h':
                        self.sendMsg('/transfer <serverId:INT[lobbyServer]>', playerId)
                        return
                    try:
                        serverId = int(msg[1])
                    except ValueError:
                        self.sendMsg("/transfer -h", playerId)
                        return

                    if len(msg[1]) != 4:
                        self.sendMsg("%s: %s: no such server" % (cmd, msg[1]), playerId)
                        return
                    elif msg[1][0] != '4':
                        self.sendMsg("%s: permission denied" % (cmd), playerId)
                        return
                    elif commonNetgameApi.GetServerType() != 'lobby':
                        self.sendMsg("%s: permission denied" % (cmd), playerId)
                        return


                    transData = {'position': [1, 2, 3]}
                    lobbyGameApi.TransferToOtherServerById(str(serverId), playerId, json.dumps(transData))
                    commonNetgameApi.AddTimer(2.0, lambda p: self.sendMsg("%s: %s: no such server" % (cmd, msg[1]), p), playerId)

                else:
                    self.sendMsg('%s: Operation not permitted' % cmd, playerId)
                    return
            mysqlPool.AsyncQueryWithOrderKey('zc98172098367198', sql, (uid, time.time()), Cb)

        elif cmd in ['hlaba', 'helperchan', 'helperlaba', 'hchan', 'hc']:
            sql = 'SELECT * FROM perms WHERE uid=%s AND type>=95'
            def Cb(args):
                if args:
                    msg = data['command'].replace('/hlaba ', '').replace('/helperchan ', '').replace('/helperlaba ', '').replace('/hchan ', '').replace('/hc ', '')
                    response = {
                        'nick': lobbyGameApi.GetPlayerNickname(playerId),
                        'msg': msg,
                        'sid': lobbyGameApi.GetServerId(),
                        'sname': commonNetgameApi.GetServerType()
                    }
                    self.NotifyToMaster("HlabaEvent", response)
                else:
                    self.sendMsg('%s: Operation not permitted' % (cmd,), playerId)
                    return
            mysqlPool.AsyncQueryWithOrderKey("a789dsb9as58a", sql, (uid,), Cb)