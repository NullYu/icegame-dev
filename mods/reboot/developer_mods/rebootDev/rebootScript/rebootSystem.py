# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import apolloCommon.commonNetgameApi as commonNetgameApi
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.mysqlPool as mysqlPool

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

# 在modMain中注册的Server System类
class rebootSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()
        self.time = None

    ##############UTILS##############

    def sendCmd(self, cmd, playerId):
        comp = serverApi.GetEngineCompFactory().CreateCommand(serverApi.getLevelId())
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

    def sendAllMsg(self, msg, alertTwice=True):
        for player in serverApi.GetPlayerList():
            self.sendMsg(msg, player)
            if alertTwice:
                self.sendMsg(msg, player)
    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self,
                            self.OnCommand)
        if 'lobby' in commonNetgameApi.GetServerType():
            self.time = 1800

        def a():
            self.RebootLogic()

        commonNetgameApi.AddRepeatedTimer(1.0, a)

    def OnCommand(self, data):
        playerId = data['entityId']
        uid = lobbyGameApi.GetPlayerUid(playerId)
        msg = data['command'].split()
        cmd = msg[0].strip("/")
        if cmd == 'reboot':
            data['cancel'] = True

            sql = 'SELECT * FROM perms WHERE uid=%s AND type>95 AND (endDate<0 OR endDate>%s);'
            def Cb(args):
                if args:
                    self.ProcessReboot(playerId, msg)
                else:
                    self.sendMsg("reboot: Operation not permitted", playerId)
                    return
            mysqlPool.AsyncQueryWithOrderKey('asda89snd0a', sql, (uid, time.time()+0), Cb)

    def RebootLogic(self):
        if self.time:
            self.time -= 1
            if self.time == 900:
                self.sendAllMsg("§e[服务器]该子服将在15分钟后重启")
            elif self.time == 600:
                self.sendAllMsg("§e[服务器]该子服将在10分钟后重启")
            elif self.time == 300:
                self.sendAllMsg("§e[服务器]该子服将在5分钟后重启")
            elif self.time == 120:
                self.sendAllMsg("§e[服务器]该子服将在2分钟后重启")
            elif self.time == 60:
                self.sendAllMsg("§e[服务器]该子服将在1分钟后重启")
            elif self.time == 30:
                self.sendAllMsg("§e[服务器]该子服将在30秒后重启")
            elif self.time < 11:
                self.sendAllMsg("§e[服务器]该子服将在%s秒后重启" % (self.time,), False)
            if self.time <= 0:
                self.DoReboot()

    def DoReboot(self, transfer=True):
        def a():
            for player in serverApi.GetPlayerList():
                lobbyGameApi.TransferToOtherServer(player, 'lobby')
        if transfer:
            self.sendAllMsg('§3服务器重启，即将将您传送至另一个lobby服')
            commonNetgameApi.AddTimer(1.0, a)

        def b():
            lobbyGameApi.ResetServer()
        commonNetgameApi.AddTimer(1.0, b)

    def ProcessReboot(self, playerId, msg):
        if len(msg) == 1:
            self.sendMsg("reboot: Too dangerous to reboot without timer!", playerId)
            return

        flag = msg[1]
        if len(msg) >= 2:
            if self.time and msg[1] != '-s':
                self.sendMsg("§calready rebooting! use /reboot -s to stop.", playerId)
                return
            if flag == '-h':
                if len(msg) == 2:
                    self.sendMsg("§einvalid command", playerId)
                    return
                try:
                    self.time = int(msg[2])
                except ValueError:
                    if msg[2] == 'now':
                        self.DoReboot()
                        return
                    self.sendMsg("reboot: %s: Integer required" % msg[2], playerId)
                    return
            elif flag == '-s':
                if self.time:
                    self.sendMsg("no longer rebooting", playerId)
                    self.time = None
                    return
                else:
                    self.sendMsg("reboot: server not rebooting", playerId)
