# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import math
import apolloCommon.commonNetgameApi as commonNetgameApi
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.mysqlPool as mysqlPool
# import cosScript.cosConst as c
import json
import datetime
import random
import apolloCommon.redisPool as redisPool
redisPool.InitDB(30)

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()


# 在modMain中注册的Server System类
class partySystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        self.page = {}

        self.auth = {}
        self.pwdStatus = {}
        self.buffer = {}

        self.mSrcApplyStatus = None

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

    def sendMsg(self, msg, playerId, suppressHint=False):
        comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
        comp.NotifyOneMessage(playerId, msg, "§f")

    def epoch2Datetime(self, epoch):
        ts = datetime.datetime.fromtimestamp(int(epoch)+0)
        return ts.strftime('%Y-%m-%d %H:%M:%S')

    def getCountInStr(self, string, target):
        count = 0
        for chr in string:
            if chr == target:
                count += 1

        return count

    def RequestToService(self, args):
        self.RequestToServiceMod("service_party", "LobbyNodeCommEvent", args)

    def NotifyHasMsgToService(self, playerId):
        self.sendMsg('§l§7...]§e等待功能服通讯', playerId)

    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self,
                            self.OnCommand)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent",
                            self, self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent",
                            self, self.OnDelServerPlayer)

        self.ListenForEvent('partyService', 'partyService', 'ServiceCommEvent', self, self.OnServiceComm)

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        uid = lobbyGameApi.GetPlayerUid(playerId)

    def OnDelServerPlayer(self, data):
        playerId = data['id']

    def OnServiceComm(self, data):
        operation = data['operation']
        print 'onservicecomm rcv data=', data

        if operation == 'msg':
            uid = data['uid']
            content = data['content']
            playerId = lobbyGameApi.GetPlayerIdByUid(uid)
            if playerId:
                self.sendMsg(content, playerId)

        elif operation == 'searchForPlayer':
            subOperation = data['subOperation']
            nickname = data['targetNickname']
            srcUid = data['srcUid']

            if subOperation == 'makeParty':
                if lobbyGameApi.GetPlayerIdByUid(srcUid):
                    self.sendMsg('§e...]正在创建队伍', lobbyGameApi.GetPlayerIdByUid)

                targetUid = None
                for player in serverApi.GetPlayerList():
                    if nickname == lobbyGameApi.GetPlayerNickname(player):
                        targetUid = lobbyGameApi.GetPlayerUid(player)
                        break

                if targetUid:
                    response = {
                        'operation': 'searchForPlayer',
                        'subOperation': 'makeParty',
                        'targetUid': targetUid,
                        'srcUid': srcUid,
                        'srcNick': data['srcNick'],
                        'srcSid': data['srcSid'],
                        'targetSid': lobbyGameApi.GetServerId()
                    }
                    self.RequestToService(response)

            elif subOperation == 'msg':
                msg = data['content']
                uid = data['uid']
                self.sendMsg(msg, lobbyGameApi.GetPlayerIdByUid(srcUid))

    def OnCommand(self, data):
        playerId = data['entityId']
        uid = lobbyGameApi.GetPlayerUid(playerId)
        msg = data['command'].split()
        cmd = msg[0].strip('/')

        if not cmd in ['p', 'party', "pc", "partyc", "partychat", "pchat"]:
            return
        else:
            data['cancel'] = True

        if cmd == 'p' or cmd == 'party':
            if len(msg) < 2:
                self.sendMsg("§einvalid command", playerId)
                return

            helpmsg = """
            Commands:
/p [-m -make --make] [player]: request to make a team with player
/p [-a -apply --apply] [player | teamId]: request to join team. If target player is not in a team, then does the same as /p -m
/p [-p -pass --pass]: passes the last application
/p [-s -summon --summon]: requires PERM. Summons all team members to current server.
/p [-l -list --list]: lists all players in team
/p [-d -disband] [--confirm-disband-party]: requires PERM. disbands party
/p [-k -kick] [playerName]: requires PERM. kicks player
/pc /partychat /pchat /partyc [msg]: party chat
"""

            flag = msg[1]
            if flag in ['-h', '-help', '--help']:
                self.sendMsg(helpmsg, playerId)
                print 'send helpmsg'
                return

            elif flag in ['-m', '-make', '--make']:
                if len(msg) < 3:
                    self.sendMsg("§einvalid command", playerId)
                    return

                targetNickname = msg[2]
                response = {
                    'operation': 'makePartyInit',
                    'src': uid,
                    'srcNick': lobbyGameApi.GetPlayerNickname(playerId),
                    'targetNickname': targetNickname
                }
                self.RequestToService(response)
                self.NotifyHasMsgToService(playerId)

            elif flag in ['-p', '-pass', '--pass']:
                self.mSrcApplyStatus = None

                def Cb(args):
                    self.mSrcApplyStatus = args
                redisPool.AsyncGet("partyApply-%s" % uid, Cb)

                if not self.mSrcApplyStatus:
                    self.sendMsg('§c没有最近的申请。请注意申请过期时间。', playerId)
                    return
                else:
                    if len(msg) < 3:
                        self.sendMsg('§a你有未处理的申请', playerId)

                    elif msg[2] == 'true':
                        response = {
                            'operation': 'partyAccept',
                            'srcUid': self.mSrcApplyStatus,
                            'targetUid': uid
                        }
                        self.RequestToService(response)
                        self.NotifyHasMsgToService(playerId)

                    elif msg[2] == 'false':
                        response = {
                            'operation': 'partyDeny',
                            'srcUid': self.mSrcApplyStatus,
                            'targetUid': uid
                        }
                        self.RequestToService(response)
                        self.NotifyHasMsgToService(playerId)

            else:
                self.sendMsg("§einvalid command", playerId)

    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("report", "reportClient", 'TestRequest', self, self.OnTestRequest)
