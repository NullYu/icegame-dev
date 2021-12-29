# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import apolloCommon.commonNetgameApi as commonNetgameApi
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.mysqlPool as mysqlPool
cooldown = {}

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

# 在modMain中注册的Server System类
class shoutSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

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
    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self,
                            self.OnCommand)
        self.ListenForEvent('shout', 'shoutMasterSystem', 'DisplayBugletEvent', self, self.OnDisplayBuglet)
        self.ListenForEvent('shout', 'shoutMasterSystem', 'DisplayAnnounceBanEvent', self, self.OnDisplayAnnounceBan)
        self.ListenForEvent('shout', 'shoutMasterSystem', 'DisplayGlobalMsgEvent', self, self.OnDisplayGlobalMsg)

    def OnDisplayBuglet(self, data):
        print 'CALL OnDisplayBuglet data=%s' % (data,)
        name = data['name']
        msg = data['msg']
        serverType = data['serverType']
        serverId = data['serverId']

        for player in serverApi.GetPlayerList():
            self.sendMsg("§6§l小喇叭 §e%s§r§e§l@%s-%s: §r§f§l%s" % (name, serverType, serverId, msg), player)

    def OnDisplayAnnounceBan(self, data):
        nickname = data['nickname']
        reason = data['reason']
        sid = data['sid']

        for player in serverApi.GetPlayerList():
            self.sendMsg('§a§l%s@%s 因 %s 被封禁' % (nickname, sid, reason), player)

    def OnDisplayGlobalMsg(self, msg):
        for player in serverApi.GetPlayerList():
            self.sendMsg(msg, player)

    def OnCommand(self, data):
        playerId = data['entityId']
        cmd = data['command'].split()
        validCmd = ["/laba", "/xiaolaba", "/buglet"]
        if cmd[0] in validCmd:
            data['cancel'] = True
            msg = data['command'].replace('/laba ', '').replace('/xiaolaba ', '').replace('/buglet ', '')
            msgOk = commonNetgameApi.CheckWordsValid(msg)
            if not msgOk:
                self.sendMsg("§3不允许发送该消息，请检查", playerId)
                return
            elif len(cmd) <= 1:
                self.sendMsg("§c无效的命令。使用/laba <信息> 发送喇叭", playerId)
                return

            uid = lobbyGameApi.GetPlayerUid(playerId)
            sql = "SELECT * FROM sudo WHERE uid=%s AND password!='0' AND unsafe=0;"
            def Cb(args):
                if args:
                    sql = "SELECT * FROM eco WHERE uid=%s AND high>=2;"
                    def Cb(args):
                        if args:
                            self.sendMsg("§b成功使用§e2 CREDITS§b发送了一条小喇叭", playerId)
                            data = {
                                "value": 1,
                                "name": lobbyGameApi.GetPlayerNickname(playerId),
                                "uid": uid,
                                "msg":msg,
                                "serverType": commonNetgameApi.GetServerType(),
                                "serverId": lobbyGameApi.GetServerId()
                            }
                            self.NotifyToMaster("SendBugletEvent", data)
                            ecoSystem = serverApi.GetSystem("eco", "ecoSystem")
                            ecoSystem.GivePlayerEco(uid, -2, 'buglet use', True)
                        else:
                            self.sendMsg("§c§l哦唷，钱包余额不足！\n§r因钱包余额不足付款被取消，本次付款不被记录。", playerId)
                    mysqlPool.AsyncQueryWithOrderKey('123795', sql, (uid,), Cb)
                else:
                    self.sendMsg("§c§l您没有设置独立密码或处于不安全状态，暂时不能收付款。\n§r使用§b/sudo§r查看独立密码状态", playerId)
            mysqlPool.AsyncQueryWithOrderKey('OnCommand/VerifySudo', sql, (uid,), Cb)
        else:
            return

    def sendGlobalMsg(self, msg):
        self.NotifyToMaster("SendGlobalMsgEvent", msg)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("report", "reportClient", 'TestRequest', self, self.OnTestRequest)
