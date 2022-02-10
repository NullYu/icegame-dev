# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import math
import json
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.redisPool as redisPool
import apolloCommon.commonNetgameApi as commonNetgameApi
import apolloCommon.mysqlPool as mysqlPool

mysqlPool.InitDB(30)

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()


##

# 在modMain中注册的Server System类
class utilsSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        self.spectating = []
        self.spectatingTarget = {}
        self.admins = []

        self.enderPearlCd = {}

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnScriptTickServer",
                            self,
                            self.OnScriptTickServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerJoinMessageEvent",
                            self,
                            self.OnPlayerJoinMessage)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerLeftMessageServerEvent",
                            self,
                            self.OnPlayerLeftMessageServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent",
                            self,
                            self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent",
                            self,
                            self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerWillShutDownEvent",
                            self,
                            self.OnServerWillShutDown)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerAttackEntityEvent",
                           self,
                           self.OnPlayerAttackEntity)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ActorUseItemServerEvent",
                            self,
                            self.OnActorUseItemServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DamageEvent",
                            self,
                            self.OnDamage)
        self.ListenForEvent('utils', 'utilsClient', 'ActionEvent', self, self.OnClientAction)
        self.ListenForEvent('utils', 'utilsClient', 'PlayerLoadedEvent', self, lambda p: self.BroadcastEvent("PlayerLoadedEvent", p))
        self.ListenForEvent('queue', 'queueMasterSystem', "ChooseDestination", self, self.ChooseDestination)

        def a():
            for player in self.enderPearlCd:
                if self.enderPearlCd[player] > 0:
                    self.enderPearlCd[player] -= 1
        commonNetgameApi.AddRepeatedTimer(1.0, a)

        comp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        suc = comp.SetDisableCommandMinecart(True)

    ##############UTILS##############

    def direction(self, x1, y1, x2, y2):
        def tan(num):  # 运算某一角度的反正切
            return math.atan(num) * 180 / math.pi

        try:
            a = tan(float(abs(y1 - y2)) / float(abs(x1 - x2)))  # 相对y轴角度
        except:
            a = 0
        # 分4种情况计算整体角度
        if x2 > x1 and y2 > y1:  # 第一象限
            return 90 - a
        elif x2 > x1 and y2 < y1:  # 第四象限
            return 90 + a
        elif x2 < x1 and y2 < y1:  # 第三象限
            return 270 - a
        elif x2 < x1 and y2 > y1:  # 第二象限
            return 270 + a
        # 4种特殊情况-正东南西北
        elif x2 == x1 and y2 > y1:  # 正北
            return 0
        elif x2 == x1 and y2 < y1:  # 正南
            return 180
        elif x2 < x1 and y2 == y1:  # 正西
            return 270
        elif x2 > x1 and y2 == y1:  # 正东
            return 90

    def dist(self, x1, y1, z1, x2, y2, z2):
        """
        运算3维空间距离，返回float
        """
        p = ((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) ** 0.5
        re = float('%.1f' % p)
        return re

    def sendCmd(self, cmd, playerId):
        comp = serverApi.GetEngineCompFactory().CreateCommand(serverApi.GetLevelId())
        comp.SetCommand(cmd, playerId)

    def SetHideName(self, playerId, isHide):
        self.NotifyToClient(playerId, "SetHideNameEvent", isHide)

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

    def OnActorUseItemServer(self, data):
        playerId = data['playerId']
        dict = data['itemDict']

        name = dict['itemName']
        if name == 'minecraft:ender_pearl':
            if self.enderPearlCd[playerId] <= 0:
                self.enderPearlCd[playerId] = 30
                return
            else:
                commonNetgameApi.AddTimer(0.05, lambda player: self.sendCmd('/kill @e[type=ender_pearl, r=7]', player), playerId)
                self.sendMsg('§3珍珠投掷冷却%s秒' % (self.enderPearlCd[playerId],), playerId)
                return

    def OnServerWillShutDown(self):
        print '********SHUTTING DOWN! GOODBYE!**************'
        for player in serverApi.GetPlayerList():
            lobbyGameApi.TryToKickoutPlayer(player, "§6服务器重启\n\n§r通常，重启需要§e5~10分钟§r时间。\n等不及了？加入我们的官方§bQQ群§r，与群友们畅谈生活！")

    def OnPlayerAttackEntity(self, data):
        playerId = data['playerId']
        victimId = data['victimId']

    def OnDamage(self, data):
        playerId = data['entityId']
        srcId = data['srcId']

        reason = data['cause']
        if reason != 'entity_attack':
            return

        vpos = serverApi.GetEngineCompFactory().CreatePos(srcId).GetPos()
        spos = serverApi.GetEngineCompFactory().CreatePos(playerId).GetPos()

        if playerId in serverApi.GetPlayerList():
            data['knock'] = False

            comp = serverApi.GetEngineCompFactory().CreateAction(playerId)
            if self.dist(vpos[0], vpos[1], vpos[2], spos[0], spos[1], spos[2]) < 3.15:
                comp.SetMobKnockback(spos[0]-vpos[0], spos[2]-vpos[2], 0.567, 0.3678, 0.718)
            else:
                # helicopter
                comp.SetMobKnockback(spos[0] - vpos[0], spos[2] - vpos[2], 0.426, 0.2105, 0.387)

    # hooked into ban api
    def GetIp(self, playerId):
        print 'utilsSystem CALL GetIp playerId=%s' % (playerId,)
        self.NotifyToClient(playerId, "GetIpEvent", playerId)

    def OnDelServerPlayer(self, args):
        playerId = args['id']
        uid = args['uid']

        if playerId in self.admins:
            self.admins.pop(self.admins.index(playerId))
        if playerId in self.enderPearlCd:
            self.enderPearlCd.pop(playerId)
        if playerId in self.spectatingTarget:
            self.spectatingTarget.pop(playerId)

    def OnAddServerPlayer(self, args):
        playerId = args['id']
        uid = lobbyGameApi.GetPlayerUid(playerId)

        print 'playerjoin args=%s' % args

        sql = 'SELECT endDate FROM perms WHERE uid=%s;'
        def Cb(args):
            if args:
                endDate = args[0][0]
                if 0 < endDate < time.time():
                    commonNetgameApi.AddTimer(5.0, lambda player: self.sendMsg("§c§l权限过期\n§r您有一个权限过期了，请查看", player))
                    mysqlPool.AsyncExecuteWithOrderKey('asdan0smd8a', 'DELETE FROM perms WHERE uid=%s;', (uid,))

        mysqlPool.AsyncQueryWithOrderKey('asd879n0s', sql, (uid,), Cb)

        if args['transferParam']:
            transParams = json.loads(args['transferParam'])

            if transParams['isAdmin'] and ('unranked' in commonNetgameApi.GetServerType()):
                self.SetPlayerSpectate(playerId, True)

        lobbyGameApi.ShieldPlayerJoinText(True)

        sql = 'SELECT * FROM perms WHERE uid=%s AND type>94;'
        def Cb(args):
            if args:
                print 'admin joined id=%s' % (playerId)
                self.admins.append(playerId)
        mysqlPool.AsyncQueryWithOrderKey('a78sd767av86s68at', sql, (lobbyGameApi.GetPlayerUid(playerId),), Cb)

        self.enderPearlCd[playerId] = 0

        sql = 'SELECT * FROM unrankedWin WHERE uid=%s;'

        def Cb(args):
            if not args:
                sql = 'INSERT INTO unrankedWin (uid, nickname, win, lose) VALUES (%s, %s, 0, 0);'
                mysqlPool.AsyncExecuteWithOrderKey('czxcnfmam871927n0e', sql,
                                                   (uid, lobbyGameApi.GetPlayerNickname(playerId)))
            else:
                length = len(args) - 1
                if length:
                    sql = 'DELETE FROM unrankedWin WHERE uid=%s LIMIT %s'
                    mysqlPool.AsyncExecuteWithOrderKey('1032145646321561', sql, (uid, length))

        mysqlPool.AsyncQueryWithOrderKey("asd7oabns6", sql, (uid,), Cb)

        sql = 'SELECT * FROM t1 WHERE uid=%s;'
        def Cb(args):
            if not args:
                sql = 'INSERT INTO t1 (uid, nickname, win, lose) VALUES (%s, %s, 0, 0);'
                mysqlPool.AsyncExecuteWithOrderKey('czxcnfmam871927n0e', sql, (uid, lobbyGameApi.GetPlayerNickname(playerId)))
        mysqlPool.AsyncQueryWithOrderKey("asdas7oabns6", sql, (uid,), Cb)

    def OnScriptTickServer(self):
        if self.spectating:
            for player in self.spectating:
                self.sendCmd("/effect @s invisibility 2 255 true", player)
                self.sendCmd("/effect @s instant_health 2 255 true", player)
                self.sendCmd("/effect @s weakness 2 255 true", player)

                if player in self.spectatingTarget:
                    try:
                        comp = serverApi.GetEngineCompFactory().CreateRot(serverApi.GetPlayerList()[self.spectatingTarget[player]])
                        sComp = serverApi.GetEngineCompFactory().CreateRot(player)
                        sComp.SetRot(comp.GetRot())
                    except IndexError:
                        pass

    def OnClientAction(self, args):
        action = args['action']
        playerId = args['playerId']

        if action == 'hub':
            if 'game' in commonNetgameApi.GetServerType():
                transData = {'position': [107, 153, 105]}
                lobbyGameApi.TransferToOtherServer(playerId, 'lobby', json.dumps(transData))
            else:
                self.sendMsg("hub: back to lobby: Operation not permitted", playerId)
        elif action == 'activity':
            value = args['value']
            if value == 1:
                regSystem = serverApi.GetSystem('reg', 'regSystem')
                if regSystem:
                    regSystem.OpenRegUi(playerId)
                else:
                    self.sendMsg('§e请您到主城再报名！', playerId)
        elif action == 'spec':
            operation = args['operation']
            if operation == 'prev':
                self.spectatingTarget[playerId] -= 1
                if self.spectatingTarget[playerId] < 0:
                    self.spectatingTarget[playerId] = len(serverApi.GetPlayerList() - 1)
                for i in range(len(serverApi.GetPlayerList())):
                    if self.spectatingTarget[playerId] in self.spectating:
                        self.spectatingTarget[playerId] -= 1
                    else:
                        break
                response = {
                    'index': self.spectatingTarget[playerId],
                    'playerId': serverApi.GetPlayerList(self.spectatingTarget[playerId]),
                    'nickname': lobbyGameApi.GetPlayerNickname(serverApi.GetPlayerList(self.spectatingTarget[playerId]))
                }
                self.NotifyToClient(playerId, 'ChangeSpecTargetEvent', response)
            elif operation == 'next':
                self.spectatingTarget[playerId] += 1
                if self.spectatingTarget[playerId] > len(serverApi.GetPlayerList()):
                    self.spectatingTarget[playerId] = 0
                for i in range(len(serverApi.GetPlayerList())):
                    if self.spectatingTarget[playerId] in self.spectating:
                        self.spectatingTarget[playerId] -= 1
                    else:
                        break
                response = {
                    'index': self.spectatingTarget[playerId],
                    'playerId': serverApi.GetPlayerList(self.spectatingTarget[playerId]),
                    'nickname': lobbyGameApi.GetPlayerNickname(serverApi.GetPlayerList(self.spectatingTarget[playerId]))
                }
                self.NotifyToClient(playerId, 'ChangeSpecTargetEvent', response)

    #################################

    # The UTILS mod is a collection of utilities aimed to be used as APIs.
    #
    # utils = serverApi.GetSystem("utils", "utilsSystem")
    #

    #################################Ss

    def CreateAdminMessage(self, msg):
        print 'adminmsg msg=%s' % (msg,)
        for player in self.admins:
            self.sendMsg(msg, player)

    def OnPlayerJoinMessage(self, data):
        data['cancel'] = True
        playerId = data['id']

        if 'game' in commonNetgameApi.GetServerType():
            for player in serverApi.GetPlayerList():
                self.sendMsg("§7[§a+§7] %s" % (lobbyGameApi.GetPlayerNickname(playerId)), player)

    def OnPlayerLeftMessageServer(self, data):
        data['cancel'] = True
        playerId = data['id']

        if 'game' in commonNetgameApi.GetServerType():
            for player in serverApi.GetPlayerList():
                self.sendMsg("§7[§c-§7] %s" % (lobbyGameApi.GetPlayerNickname(playerId)), player)

    def ToggleSpectate(self, playerId):
        if playerId in self.spectating:
            self.SetPlayerSpectate(playerId, True)
        else:
            self.SetPlayerSpectate(playerId, False)


    def SendPlayerToSurv(self, playerId):
        data = {
            'sid': lobbyGameApi.GetServerId(),
            'type': 'game_surv',
            'playerId': playerId
        }
        self.NotifyToMaster("ChooseDestination", data)

    def ChooseDestination(self, data):
        playerId = data['playerId']
        isQueue = data['value']

        if isQueue:
            transData = {'position': [1, 2, 3]}
            lobbyGameApi.TransferToOtherServer(playerId, 'queue_surv', json.dumps(transData))
        else:
            transData = {'position': [1, 2, 3]}
            lobbyGameApi.TransferToOtherServer(playerId, 'game_surv', json.dumps(transData))

    def ShowWinBanner(self, playerId, isTest=False, musicId=None):
        musicSystem = serverApi.GetSystem('music', 'musicSystem')
        uid = lobbyGameApi.GetPlayerUid(playerId)
        if not uid:
            print 'win banner for %s failed!!! player left early' % playerId
            return

        # check for mvp
        sql = 'SELECT itemId FROM items WHERE uid=%s AND type="mvp" AND inUse=1 AND (expire>%s OR expire<0);'
        def Cb(args):
            if args or (isTest and musicId):
                if args:
                    itemId = args[0][0]
                else:
                    itemId = musicId
                name = 'music.mvp.'+str(itemId)
                for player in serverApi.GetPlayerList():
                    musicSystem.PlayMusicToPlayer(player, name)
                data = {
                    'playerId': playerId,
                    'nickname': lobbyGameApi.GetPlayerNickname(playerId),
                    'musicName': musicSystem.mvpList[itemId]
                }
            else:
                data = {
                    'playerId': playerId,
                    'nickname': lobbyGameApi.GetPlayerNickname(playerId),
                    'musicName': None
                }
            for player in serverApi.GetPlayerList():
                self.NotifyToClient(player, 'ShowBannerEvent', data)

        mysqlPool.AsyncQueryWithOrderKey('xcvm8978na6s', sql, (uid, time.time()), Cb)

    def TextBoard(self, playerId, isShow, content=None):
        data = {
            'show': isShow,
            'content': content
        }
        self.NotifyToClient(playerId, 'TextBoardEvent', data)

    def SetPlayerSpectate(self, playerId, isSpectate, hasFreecam=False, lightning=False, noInteract=False):
        print 'CALL Setplayerspec'
        data = {
            'playerId': playerId,
            'value': isSpectate,
            'interact': noInteract,
            'freecam': hasFreecam
        }
        self.NotifyToClient(playerId, "SetPlayerSpectateEvent", data)

        if isSpectate:
            self.sendCmd("/clear @s", playerId)
            self.spectating.append(playerId)

            if lightning:
                self.sendCmd("/summon lightning", playerId)
            if not hasFreecam:
                print 'no freecam'
                for player in serverApi.GetPlayerList():
                    if player not in self.spectating:
                        self.spectatingTarget[playerId] = serverApi.GetPlayerList().index(player)
                        response = {
                            'isSpec': True,
                            'index': self.spectatingTarget[playerId],
                            'playerId': serverApi.GetPlayerList()[self.spectatingTarget[playerId]],
                            'nickname': lobbyGameApi.GetPlayerNickname(serverApi.GetPlayerList()[self.spectatingTarget[playerId]])
                        }
                        self.NotifyToClient(playerId, 'StartSpecEvent', response)
        else:
            print 'stop spec'

            if playerId in self.spectating:
                self.spectating.pop(self.spectating.index(playerId))
            if playerId in self.spectatingTarget:
                print 'stop spec client'
                self.spectatingTarget.pop(playerId)
                response = {
                    'isSpec': False
                }
                self.NotifyToClient(playerId, 'StartSpecEvent', response)

        comp = serverApi.GetEngineCompFactory().CreateFly(playerId)
        comp.ChangePlayerFlyState(isSpectate)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("lobbyutils", "lobbyutilsClient", 'TestRequest', self, self.OnTestRequest)
