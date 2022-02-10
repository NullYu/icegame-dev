# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import ujson as json
import datetime
import apolloCommon.commonNetgameApi as commonNetgameApi
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.mysqlPool as mysqlPool
import apolloCommon.redisPool as redisPool
redisPool.InitDB(30) #建立连接池
cooldown = {}

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

# 在modMain中注册的Server System类
class loginSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        self.timer = {}
        self.alreadyLogin = []

        self.mSetLoginServerTimer = None

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

    def forceSelect(self, slot, playerId):
        comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
        comp.ChangeSelectSlot(slot)

    def sendMsg(self, msg, playerId):
        comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
        comp.NotifyOneMessage(playerId, msg, "§f")

    def epoch2Datetime(self, epoch):
        ts = datetime.datetime.fromtimestamp(int(epoch)+0)
        return ts.strftime('%Y-%m-%d %H:%M:%S')

    #################################

    def ListenEvents(self):
        # events that should be directly canceled
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self, self.DirectCancel)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerChatEvent", self, self.DirectCancel)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerJoinMessageEvent", self, self.DirectCancel)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerAttackEntityEvent", self, self.DirectCancel)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerLeftMessageServerEvent", self, self.DirectCancel)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self, self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self, self.OnDelServerPlayer)
        self.ListenForEvent('login', 'loginClient', 'DoneLoading', self, self.OnDoneLoading)
        self.ListenForEvent('login', 'loginClient', 'LoginEvent', self, self.OnLogin)
        self.ListenForEvent('queue', 'queueMaster', 'SetAuthServerDone', self, self.OnSetAuthServerDone)

        commonNetgameApi.AddRepeatedTimer(1.0, self.tick)

        def a():
            self.NotifyToMaster("RegisterAuthServer", lobbyGameApi.GetServerId())
            print 'registering auth server...'
        self.mSetLoginServerTimer = commonNetgameApi.AddRepeatedTimer(10.0, a)

    def OnSetAuthServerDone(self, data):
        commonNetgameApi.CancelTimer(self.mSetLoginServerTimer)
        print 'SetAuthServerDone DONE!!!'

    def DirectCancel(self, data):
        data['cancel'] = True

        if data['message'] == 'queue' or data['message'] == 'surv':
            transData = {'position': [1, 2, 3]}
            lobbyGameApi.TransferToOtherServer(data['playerId'], 'queue_surv', json.dumps(transData))

    def tick(self):
        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        if not serverApi.GetPlayerList():
            return

        for player in serverApi.GetPlayerList():
            self.sendTitle('§l§eICE§a_§bGAME', 1, player)
            self.sendTitle('向前走登入大厅；点击身边的NPC进入纯净生存服', 2, player)
            if player in self.timer:
                msg = """§l§eICE§a_§bGAME
                
§b向前走进入大厅

点击身边的NPC进入 无规则生存服

§f您还可在登录服逗留§c%s§f秒。""" % self.timer[player]
                utilsSystem.TextBoard(player, True, msg)
                self.timer[player] -= 1

                if self.timer[player] <= 0:
                    lobbyGameApi.TryToKickoutPlayer(player, '§l§c登录失败§r\n§l为什么？§r您没有在规定的时间内完成登录操作。\n§6您不一定被封禁。请在进入后向前走以登录。\n§b若您被封禁，您可以访问§eicegame.net.cn/appeal§b申诉')
                    self.timer.pop(player)

            comp = serverApi.GetEngineCompFactory().CreatePos(player)
            pos = comp.GetPos()

            if abs(pos[0]) > 1 or abs(pos[2]) > 1:
                self.OnLogin(player)

    def OnDoneLoading(self, playerId):
        uid = serverApi.GetPlayerUid(playerId)
        self.timer[playerId] = 45

        return
        self.sendTitle('§l§eICE§a_§bGAME', 1, playerId)
        self.sendTitle('向前走登入大厅；点击身边的NPC进入纯净生存服', 2, playerId)

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        uid = data['uid']

        isPeUser = lobbyGameApi.IsPlayerPeUser(playerId)
        if not isPeUser:
            lobbyGameApi.TryToKickoutPlayer(playerId, """No admission to modpc 
            
Email service@icegame.xyz for whitelisting""")

        def Cb(t):
            return
            if t:
                if t > time.time():
                    lobbyGameApi.TryToKickoutPlayer(playerId, '§6与服务器断开连接')

        redisPool.AsyncGet("login-cd-%s" % uid, Cb)

        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        comp.SetFootPos((0, 4, 0))

        self.timer[playerId] = 45

        self.sendCmd('/effect @s invisibility 999 1 true', playerId)

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        if playerId in self.timer:
            self.timer.pop(playerId)
        if playerId in self.alreadyLogin:
            self.alreadyLogin.pop(self.alreadyLogin.index(playerId))

    def OnLogin(self, playerId):
        print 'ON LOGIN'
        if playerId in self.alreadyLogin:
            return

        uid = lobbyGameApi.GetPlayerUid(playerId)
        sql = 'SELECT id,startDate,endDate,reason FROM banData WHERE uid=%s AND (endDate<0 OR endDate>%s) AND valid=1;'
        self.alreadyLogin.append(playerId)
        def Cb(args):
            if args:
                data = args[0]
                id = data[0]
                startDate = data[1]
                endDate = data[2]
                if endDate < 0:
                    endDate = '永不'
                reason = data[3].encode('utf-8')

                msg1 = """§b该账户被§l§eICE§a_§bGAME§r§b封禁
BAN ID: §c§l%s§r§b
IGN: §f%s
§bUID: §f%s
§b原因: §f%s
§b开始日期: §f%s
§b解封日期: §f%s"""% (id, lobbyGameApi.GetPlayerNickname(playerId), uid, reason, self.epoch2Datetime(startDate), self.epoch2Datetime(endDate))

                msg2 = """§b若您认为该封禁不公平，您可以填写申诉表格：
§ficegame.net.cn/appeal

§e您也可以选择游玩生存服，点击身边的NPC进入。"""
                self.sendMsg(msg1, playerId)
                self.sendMsg(msg2, playerId)

                self.timer[playerId] = 7

                redisPool.AsyncSet('login-cd-%s' % uid, time.time()+15)

            else:
                self.LoginSuccess(playerId)
                return
        mysqlPool.AsyncQueryWithOrderKey('login%s' % uid, sql, (uid, time.time()), Cb)

    def LoginSuccess(self, playerId):

        transData = {'position': [1, 2, 3]}
        # TODO !!! Check for debug
        lobbyGameApi.TransferToOtherServer(playerId, 'lobby', json.dumps(transData))
