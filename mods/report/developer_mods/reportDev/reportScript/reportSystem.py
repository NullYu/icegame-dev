# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import json
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.mysqlPool as mysqlPool
import apolloCommon.commonNetgameApi as commonNetgameApi

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()


# 在modMain中注册的Server System类
class reportSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()
        self.cooldown = {}
        self.lastReportSid = []

        self.lastReportUid = 0

    ##############UTILS##############

    def dist(self, x1, y1, z1, x2, y2, z2):
        """
        运算3维空间距离，返回float
        """
        p = ((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) ** 0.5
        re = float('%.1f' % p)
        return re

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
    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self,
                            self.OnCommand)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self,
                            self.OnDelServerPlayer)
        self.ListenForEvent('report', 'reportMasterSystem', 'DisplayReportEvent', self, self.OnDisplayReport)
        self.ListenForEvent('report', 'reportMasterSystem', 'DisplayProcessReportEvent', self, self.OnDisplayProcessReport)

    def OnDelServerPlayer(self, data):
        playerId = data['id']

        if playerId in self.cooldown:
            del self.cooldown[playerId]

    def OnCommand(self, data):
        playerId = data['entityId']
        cmd = data['command'].split()
        if cmd[0] == "/report" or cmd[0] == "/r":
            data['cancel'] = True
            if len(cmd) < 2 or len(cmd) > 4:
                self.sendMsg("§c无效的命令。使用/r -h查看帮助。", playerId)
                return
            sel = cmd[1]
            players = serverApi.GetPlayerList()

            reason = "null"

            validSelectors = ['-a', '-n', '-p', '-r', '-h']
            if len(cmd) < 2 or not(sel in validSelectors):
                self.sendMsg("§c无效的命令。使用/r -h查看帮助。", playerId)
            elif sel == "-h" or sel == "-H":
                self.sendMsg("§breport - 玩家举报平台\n§r§l/report (/r) -ahnpr [selectorData] [reason]\n§r/report [-a all | -h help | -n [username] name | -p proximity | -r rival] [reason optional]\n§b访问t.im/howtoreport了解更多", playerId)
            elif playerId in self.cooldown and self.cooldown[playerId]-time.time() > 0:
                self.sendMsg("report: Operation not permitted", playerId)
            # elif len(players) < 2:
            #     self.sendMsg("§c无法举报，因为服务器内只有您自己。", playerId)
            elif sel == "-a":
                if len(cmd) > 2:
                    reason = cmd[2]

                self.sendMsg("§b§l举报成功。§r线上的管理人员已被召唤。", playerId)
                args = {
                    "type": 1,
                    "serverId": lobbyGameApi.GetServerId(),
                    "reporter": lobbyGameApi.GetPlayerNickname(playerId),
                    "reason": reason,
                }
                self.NotifyToMaster('SendReportEvent', args)
                self.cooldown[playerId] = time.time() + 60
            elif sel == "-n":
                if len(cmd) > 3:
                    reason = cmd[3]
                if not cmd[2]:
                    self.sendMsg("§c缺少玩家名。使用/r -n <玩家名> 进行举报", playerId)
                    return
                a = False
                for player in serverApi.GetPlayerList():
                    if lobbyGameApi.GetPlayerNickname(player) == cmd[2]:
                        a = player
                        break
                if not a:
                    self.sendMsg("§c无法举报玩家，因为该玩家不存在。", playerId)
                    return

                if playerId == cmd[2]:
                    self.sendMsg("§c无法举报玩家，因为该玩家是您自己。", playerId)
                else:
                    self.sendMsg("§b§l举报成功。§r线上的管理人员已被召唤。", playerId)
                    args = {
                        "type": 2,
                        "serverId": lobbyGameApi.GetServerId(),
                        "reporter": lobbyGameApi.GetPlayerNickname(playerId),
                        "reason": reason,
                        "target": cmd[2],
                        "targetUid": lobbyGameApi.GetPlayerUid(player)
                    }
                    self.NotifyToMaster('SendReportEvent', args)
                    self.cooldown[playerId] = time.time() + 60
            elif sel == "-p":
                if len(cmd) > 2:
                    reason = cmd[2]
                if len(serverApi.GetPlayerList()) < 2:
                    self.sendMsg("§c无法举报，因为没有离您最近的玩家。", playerId)
                    return

                bDist = 0
                bVictim = None

                comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
                s = comp.GetPos()
                for player in serverApi.GetPlayerList():
                    comp = serverApi.GetEngineCompFactory().CreatePos(player)
                    v = comp.GetPos()
                    if (self.dist(s[0], s[1], s[2], v[0], v[1], v[2]) < bDist or bDist == 0) and player != playerId:
                        bDist = self.dist(s[0], s[1], s[2], v[0], v[1], v[2])
                        bVictim = player
                self.sendMsg("§b§l举报成功。§r线上的管理人员已被召唤。", playerId)
                args = {
                    "type": 3,
                    "serverId": lobbyGameApi.GetServerId(),
                    "reporter": lobbyGameApi.GetPlayerNickname(playerId),
                    "reason": reason,
                    "target": lobbyGameApi.GetPlayerNickname(bVictim),
                    "targetUid": lobbyGameApi.GetPlayerUid(bVictim)
                }
                self.NotifyToMaster('SendReportEvent', args)
                self.cooldown[playerId] = time.time() + 60
            elif sel == "-r":
                if len(cmd) > 2:
                    reason = cmd[2]
                if not(len(players) > 2):
                    self.sendMsg("§c无法找到对手，因为服务器里有太多对手了。", playerId)
                else:
                    li = players
                    if playerId in li:
                        li.pop(playerId)
                    else:
                        self.sendMsg("§c未知错误：player(reporter) not in server player list", playerId)
                        return
                    args = {
                        "type": 4,
                        "serverId": lobbyGameApi.GetServerId(),
                        "reporter": lobbyGameApi.GetPlayerNickname(playerId),
                        "reason": reason,
                        "targetUid": lobbyGameApi.GetPlayerUid(cmd[2]),
                        "target": lobbyGameApi.GetPlayerNickname(li[0])
                    }
                    self.NotifyToMaster('SendReportEvent', args)
                    self.cooldown[playerId] = time.time() + 60

        elif cmd[0] in ['/rb', '/rp']:
            data['cancel'] = True

            sql = 'SELECT * FROM perms WHERE uid=%s AND type>94;'

            def Cb(args):
                if args:
                    if not self.lastReportSid:
                        self.sendMsg("§e目前没有未处理的举报", playerId)
                        return
                    if cmd[0] == '/rp':
                        print 'rp cmd issued'
                        data = {
                            'serverId': self.lastReportSid[0],
                            'handler': lobbyGameApi.GetPlayerNickname(playerId)
                        }
                        self.NotifyToMaster('ProcessReportEvent', data)

                        def a(info):
                            transData = {'isAdmin': True}
                            lobbyGameApi.TransferToOtherServerById(info[0], info[1], json.dumps(transData))

                        commonNetgameApi.AddTimer(2.0, a, (playerId, self.lastReportSid[0]))
                    elif cmd[0] == '/rb':
                        self.sendMsg("开发中", playerId)
                else:
                    self.sendMsg("%s: Operation not permitted" % (cmd,), playerId)

            mysqlPool.AsyncQueryWithOrderKey("ad89sbansma7c", sql, (lobbyGameApi.GetPlayerUid(playerId),), Cb)

    def OnDisplayReport(self, args):
        print 'ondisplayreport args=%s' % (args,)
        type = args['type']
        sid = args['serverId']
        reporter = args['reporter']
        reason = args['reason']
        if 'target' in args.keys():
            target = args['target']
            uid = args['targetUid']
            self.lastReportUid = uid
        else:
            target = "NULL"
            uid = "NULL"

        self.lastReportSid.append(sid)

        msg = "§l§6NEW REPORT!!! §rtype=%s server=%s reporter=%s reason=%s target=%s#%s\n§a使用/rp快捷处理，使用/rb以作弊为由封禁上个被举报的玩家" % (type, sid, reporter, reason, target, uid)
        utils = serverApi.GetSystem('utils', 'utilsSystem')
        utils.CreateAdminMessage(msg)

    def OnDisplayProcessReport(self, args):
        sid = args['serverId']
        handler = args['handler']

        if sid in self.lastReportSid:
            self.lastReportSid.pop(self.lastReportSid.index(sid))
            utils = serverApi.GetSystem('utils', 'utilsSystem')
            utils.CreateAdminMessage("§a%s处理了位于server-%s的举报" % (handler, sid))

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("report", "reportClient", 'TestRequest', self, self.OnTestRequest)
