# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import apolloCommon.commonNetgameApi as commonNetgameApi
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.mysqlPool as mysqlPool
import apolloCommon.redisPool as redisPool
redisPool.InitDB(30)
cooldown = {}

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

# 在modMain中注册的Server System类
class iacSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        self.uids = {}

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

    def dist(self, x1, y1, z1, x2, y2, z2):
        """
        运算3维空间距离，返回float
        """
        p = ((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) ** 0.5
        re = float('%.1f' % p)
        return re
    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerPlayerTryDestroyBlockEvent", self,self.OnServerPlayerTryDestroyBlock)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerEntityTryPlaceBlockEvent", self,self.OnServerEntityTryPlaceBlock)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ActuallyHurtServerEvent", self,self.OnActuallyHurtServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerAttackEntityEvent", self,self.OnPlayerAttackEntity)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self,self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self,self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerInventoryOpenScriptServerEvent", self,self.OnPlayerInventoryOpenScriptServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnScriptTickServer", self,self.ScriptTick)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerCheatSpinAttackServerEvent", self,self.OnPlayerCheatSpinAttackServer)

        self.ListenForEvent('iac', 'iacMasterSystem', 'IacBanEvent', self, self.OnIacBan)
        self.ListenForEvent('iac', 'iacMasterSystem', 'GlobalKickServerEvent', self, self.OnGlobalKickServer)
        self.ListenForEvent('iacBeh', 'iacClient', 'ClientVlEvent', self, self.OnClientVl)

        def a():
            self.CheckVl()
        commonNetgameApi.AddRepeatedTimer(6.0, a)

        def b():
            self.DecayVl()
        commonNetgameApi.AddRepeatedTimer(19.0, b)

        def c():
            self.AnnounceBan()
        commonNetgameApi.AddRepeatedTimer(900.0, b)

        comp = serverApi.GetEngineCompFactory().CreateItemBanned(serverApi.GetLevelId())

        items = [
            'minecraft:bedrock',
            'minecraft:command_block',
            'minecraft:command_block_minecart',
            'minecraft:dragon_egg',
            'minecraft:netherite_helmet',
            'minecraft:netherite_chestplate',
            'minecraft:netherite_leggings',
            'minecraft:netherite_boots',
            'minecraft:netherite_sword'
        ]
        for item in items:
            comp.AddBannedItem(item)
        print('banned items:%s' % comp.GetBannedItemList())
    ##############API################

    def ScriptTick(self):
        if serverApi.GetPlayerList() and commonNetgameApi.GetServerType() not in ['lobby', 'game_bw', 'game_bwBomb']:
            self.sendCmd('/kill @e[type=tnt]', serverApi.GetPlayerList()[0])

    def CheckVl(self):
        for player in serverApi.GetPlayerList():
            uid = lobbyGameApi.GetPlayerUid(player)
            def Cb(args):
                print 'checkvl args=%s' % (args,)
                if args:
                    vl = int(args)
                    if vl >= 60:
                        print 'IAC BAN'
                        self.IacBan(uid)
                else:
                    return
            redisPool.AsyncGet('iac-vl-%s'%(uid,), Cb)

    def OnPlayerInventoryOpenScriptServer(self, data):
        playerId = data['playerId']

        if data['isCreative']:
            self.AddVl(lobbyGameApi.GetPlayerUid(playerId), 61)
            self.IacKick(lobbyGameApi.GetPlayerUid(playerId), playerId)

    def DecayVl(self):
        for player in serverApi.GetPlayerList():
            uid = lobbyGameApi.GetPlayerUid(player)

            def Cb(args):
                if args and args > 0:
                    def b(args):
                        return
                    def a(conn):
                        conn.incrby('iac-vl-%s' % (uid,), -1)
                    redisPool.AsyncFuncWithKey(a, "iac-api-%s" % (uid,), b)
            redisPool.AsyncGet('iac-vl-%s' % (uid,), Cb)

    def AnnounceBan(self):
        sql = 'SELECT count(*) FROM banData WHERE startDate>%s OR startDate=0;'
        def Cb(args):
            if args:
                totalCount = args[0][0]
                sql = 'SELECT count(*) FROM banData WHERE startDate>%s AND reason="iac assertion";'
                def Cb(args):
                    if args:
                        iacCount = args[0][0]
                        manualCount = totalCount-iacCount

                        for player in serverApi.GetPlayerList():
                            self.sendMsg('[§l§cIAC作弊封禁公示§r] 在过去的7日内，§4§l%s§r名纪狗被封禁。这包括§4§l%s§r名纪狗被IAC系统封禁，还有§4§l%s§r名不幸撞上了管理员。' % (totalCount, iacCount, manualCount), player)
                mysqlPool.AsyncQueryWithOrderKey('asdahqsd78', sql, (time.time() - 633660,), Cb)
        mysqlPool.AsyncQueryWithOrderKey('asdao9nsdao9s', sql, (time.time()-633660,), Cb)

    def OnGlobalKickServer(self, uid):
        playerId = lobbyGameApi.GetPlayerIdByUid(uid)
        if playerId in serverApi.GetPlayerList():
            lobbyGameApi.TryToKickoutPlayer(playerId, '§6与服务器断开连接')

    def OnIacBan(self, data):
        uid = data['uid']
        nickname = data['nickname']
        playerId = lobbyGameApi.GetPlayerIdByUid(uid)
        if uid:
            self.IacKick(uid, playerId)
            utils = serverApi.GetSystem('utils', 'utilsSystem')
            utils.CreateAdminMessage('§cIAC-BAN: §r%s-%s: §a%s was banned' % (commonNetgameApi.GetServerType().encode('utf-8'), lobbyGameApi.GetServerId(), lobbyGameApi.GetPlayerNickname(playerId).encode('utf-8')))

        for player in serverApi.GetPlayerList():
            pass
            # self.sendMsg("§7[§l§c🚫§r§7] §r%s被IAC反作弊永久封禁" % (nickname,), player)

    def IacVerbose(self, msg):
        utils = serverApi.GetSystem('utils', 'utilsSystem')
        utils.CreateAdminMessage('§cIAC-VERBOSE: §r%s-%s: §a%s' % (commonNetgameApi.GetServerType().encode('utf-8'), lobbyGameApi.GetServerId(), msg.encode('utf-8')))

    def AddVl(self, uid, vl):
        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        playerId = lobbyGameApi.GetPlayerIdByUid(uid)
        if utilsSystem and playerId:
            if playerId in utilsSystem.admins:
                return

        data = {
            'uid': uid,
            'vl': vl
        }
        self.NotifyToMaster("ApiAddVlEvent", data)

    def IacKick(self, uid, playerId):
        if playerId in serverApi.GetPlayerList():
            def ClearAntilog():
                redisPool.AsyncDelete('ffa-antilog-%s' % (uid,))
            commonNetgameApi.AddTimer(2.0, ClearAntilog)
            lobbyGameApi.TryToKickoutPlayer(playerId, '§6与服务器断开连接')

    def IacBan(self, uid):
        data = {
            'uid': uid,
            'sid': lobbyGameApi.GetServerId(),
            'nickname': lobbyGameApi.GetPlayerNickname(lobbyGameApi.GetPlayerIdByUid(uid))
        }
        self.NotifyToMaster("RecIacBanEvent", data)

        if lobbyGameApi.GetPlayerIdByUid(uid):
            self.IacKick(uid, lobbyGameApi.GetPlayerIdByUid(uid))

    def OnClientVl(self, data):
        playerId = data['playerId']
        vl = data['vl']
        uid = lobbyGameApi.GetPlayerUid(playerId)

        print 'clientvl data=%s' % (data,)
        if 'alertType' in data:

            alertType = data['alertType']
            if alertType == 'fakeTap':
                self.IacVerbose("%s:combat.faketap/autoclick" % (lobbyGameApi.GetPlayerNickname(playerId, ),))
                self.AddVl(uid, 2)
            elif alertType == 'highjump' and data['height'] > 10 and data['time'] > 6:
                utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
                if utilsSystem:
                    if playerId in utilsSystem.admins:
                        return
            self.IacVerbose("%s:movement.highjump§f height=%s fallTime=%s" % (lobbyGameApi.GetPlayerNickname(playerId, ), data['height'], data['time']))
            self.AddVl(uid, 1)
            # elif alertType == 'joystickTest':
            #     self.IacVerbose("[DEBUG] Wow! %s tapped non F11" % playerId)

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        uid = lobbyGameApi.GetPlayerUid(playerId)

        self.uids[playerId] = uid

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        uid = lobbyGameApi.GetPlayerUid(playerId)

        if playerId in self.uids:
            self.uids.pop(playerId)

    ##############DETECTIONS##################

    # blatant.blockBreak
    def OnServerPlayerTryDestroyBlock(self, data):
        playerId = data['playerId']
        if 'lobby' in commonNetgameApi.GetServerType():
            data['cancel'] = True
            self.AddVl(lobbyGameApi.GetPlayerUid(playerId), 60)
            self.IacVerbose("%s:blatant.blockBreak" % (lobbyGameApi.GetPlayerNickname(playerId,)))

        comp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        gameType = comp.GetPlayerGameType(playerId)

        if gameType == 2:
            data['cancel'] = True
            self.AddVl(lobbyGameApi.GetPlayerUid(playerId), 60)
            self.IacVerbose("%s:blatant.adventure->blockBreak" % (lobbyGameApi.GetPlayerNickname(playerId, )))

    # blatant.blockPlace
    def OnServerEntityTryPlaceBlock(self, data):
        playerId = data['entityId']
        name = data['fullName']
        print 'placeblock name=%s' % (name,)
        if name == 'minecraft:bedrock' or name == 'minecraft:command_block':
            data['cancel'] = True
            print 'bedrock!!!'
            self.AddVl(lobbyGameApi.GetPlayerUid(playerId), 60)
            self.IacVerbose("%s:blatant.blockPlace:bedrock" % (lobbyGameApi.GetPlayerNickname(playerId, )))

    # blatant.instakill
    def OnActuallyHurtServer(self, data):
        srcId = data['srcId']
        playerId = data['entityId']

        if srcId in serverApi.GetPlayerList():
            comp = serverApi.GetEngineCompFactory().CreateItem(srcId)

            response = {
                'playerId': srcId,
            }
            self.NotifyToClient(srcId, "ServerAttackEvent", response)

            holding = comp.GetEntityItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0)
            if holding['extraId'] == 'legal32k':
                return

            if data['damage'] > 50:
                self.AddVl(lobbyGameApi.GetPlayerUid(playerId), 25)
                self.IacVerbose("%s:blatant.instakill" % (lobbyGameApi.GetPlayerNickname(playerId, )))

                data['damage'] = 5

    # combat.reach, combat.killauraA
    def OnPlayerAttackEntity(self, data):
        playerId = data['playerId']
        victimId = data['victimId']

        print '%s att %s' % (playerId, victimId)

        comp = serverApi.GetEngineCompFactory().CreateGame(playerId)
        fov = comp.CanSee(playerId, victimId, 8.0, True, 180.0, 180.0)
        comp = serverApi.GetEngineCompFactory().CreatePos(victimId)
        v = comp.GetPos()
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        s = comp.GetPos()

        dist = self.dist(v[0], v[1], v[2], s[0], s[1], s[2])

        if not fov and dist >= 2.25:
            self.AddVl(lobbyGameApi.GetPlayerUid(playerId), 2)
            self.IacVerbose("%s:combat.killauraA" % (lobbyGameApi.GetPlayerNickname(playerId, )))
            pass

        if dist >= 7:
            self.AddVl(lobbyGameApi.GetPlayerUid(playerId), 1)
            self.IacVerbose("%s:combat.reach" % (lobbyGameApi.GetPlayerNickname(playerId, )))
            data['cancel'] = True
            pass

    #combat.killauraB
    def OnPlayerCheatSpinAttackServer(self, data):
        playerId = data['playerId']
        if data['isStart']:
            self.AddVl(lobbyGameApi.GetPlayerUid(playerId), 5)
            self.IacVerbose("%s:combat.killauraB:start" % (lobbyGameApi.GetPlayerNickname(playerId, )))
        else:
            self.AddVl(lobbyGameApi.GetPlayerUid(playerId), 10)
            self.IacVerbose("%s:combat.killauraB:end" % (lobbyGameApi.GetPlayerNickname(playerId, )))

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("report", "reportClient", 'TestRequest', self, self.OnTestRequest)
