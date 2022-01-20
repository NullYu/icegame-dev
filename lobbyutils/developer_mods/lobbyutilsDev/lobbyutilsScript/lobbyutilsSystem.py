# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import datetime
import apolloCommon.mysqlPool as mysqlPool
import apolloCommon.commonNetgameApi as commonNetgameApi
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.launcherApi as launcherApi
import random

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

# 在modMain中注册的Server System类
class lobbyutilsSystem(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()
        self.isInit = False
        lobbyGameApi.ShieldPlayerJoinText(True)

        commonNetgameApi.AddRepeatedTimer(6.0, self.tick)

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

    def sendMsgToAll(self, msg):
        for player in serverApi.GetPlayerList():
            self.sendMsg(msg, player)

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self,
                            self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerPlayerTryDestroyBlockEvent", self, self.OnServerPlayerTryDestroyBlock)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerEntityTryPlaceBlockEvent", self, self.OnServerPlayerTryDestroyBlock)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerAttackEntityEvent",
                            self,
                            self.OnPlayerAttackEntity)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerDieEvent",
                            self,
                            self.OnPlayerDie)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ActuallyHurtServerEvent",
                            self,
                            self.OnActuallyHurtServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent",
                            self,
                            self.OnCommand)

        gameComp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        field = gameComp.AddBlockProtectField(0, (-500, 0, -500), (500, 255, 500))
        print 'add protect field=', field

        gameComp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        gameComp.SetCanBlockSetOnFireByLightning(False)
        gameComp.SetCanActorSetOnFireByLightning(False)

        comp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        ruleDict = {
            'option_info': {
                'natural_regeneration': False,  # 自然生命恢复
                'immediate_respawn': True,  # 作弊开启
                'show_coordinates': True,
                'show_death_messages': False
            },
            'cheat_info': {
                'always_day': True,  # 终为白日
                'mob_griefing': False,  # 生物破坏方块
                'keep_inventory': False,  # 保留物品栏
                'weather_cycle': False,  # 天气更替
                'mob_spawn': False,  # 生物生成
            }
        }
        setGameruleReturn = comp.SetGameRulesInfoServer(ruleDict)
        print 'Try to SetGameRule success=%s; gamerule is now=%s' % (setGameruleReturn, comp.GetGameRulesInfoServer())


    def epoch2Datetime(self, epoch):
        ts = datetime.datetime.fromtimestamp(int(epoch)+0)
        return ts.strftime('%Y-%m-%d-\n%H:%M:%S')

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("lobbyutils", "lobbyutilsClient", 'TestRequest', self, self.OnTestRequest)

    def tick(self):
        pass


    def OnAddServerPlayer(self, data):

        playerId = data['id']
        uid = data['uid']

        sql = 'SELECT * FROM goodrating WHERE uid=%s;'
        def Cb(args):
            if not args:
                print 'no data for player in goodrating'
                def callback(data):
                    print 'launcher cb %s' % data
                    stars = data['entity']['stars']
                    print 'stars for %s is %s' % (uid, stars)
                    if stars == 5:
                        def a():
                            self.sendMsg('§a§l感谢您为我们送上5星好评！§r作为一份心意，我们为您送上了一份小礼物——一个随机MVP音效，14天。§e现在使用/cos来装备该音效！', playerId)
                        commonNetgameApi.AddTimer(10.0, a)
                        sql = 'INSERT INTO items (uid, type, itemId, expire) VALUES (%s, "mvp", %s, %s);'
                        mysqlPool.AsyncExecuteWithOrderKey('zxc978qe09123123', sql, (uid, random.randint(1, 13), time.time()+1209600))
                        mysqlPool.AsyncExecuteWithOrderKey('zxc97s8qe09123123', 'INSERT INTO goodrating (uid) VALUES (%s)', (uid,))
                    elif stars < 0:
                        def a():
                            self.sendMsg('§b§l五星好评送好礼！§r我们新推出了一些新商品，例如MVP音效。目前，他们无法被购买。但是，您可以给我们五星好评，我们将会给您这个奖励（评价完毕后请重新进入游戏领取）!§e若您愿意叫您的朋友一同游玩，那就更好了！', playerId)
                        commonNetgameApi.AddTimer(10.0, a)
                launcherApi.GetPeGameUserStars(uid, callback)

        mysqlPool.AsyncQueryWithOrderKey('z98d7a09d8s', sql, (uid,), Cb)

        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        comp.SetFootPos((0, 176, 0))
        comp = serverApi.GetEngineCompFactory().CreateCommand(serverApi.GetLevelId())
        comp.SetCommand("/effect @s clear", playerId)  # 传送指令
        comp = serverApi.GetEngineCompFactory().CreateGame(playerId)
        comp.SetDisableHunger(True)
        comp = serverApi.GetEngineCompFactory().CreateGame(playerId)
        comp.SetDisableDropItem(True)
        comp = serverApi.GetEngineCompFactory().CreateGame(playerId)
        comp.SetHurtCD(3)
        comp = serverApi.GetEngineCompFactory().CreateAction(playerId)
        comp.SetMobKnockback(0.1, 0.1, 9, 0.1, 1.0)

        utils = serverApi.GetSystem("utils", "utilsSystem")
        utils.SetPlayerSpectate(playerId, False)

        print 'playerslist is not %s' % serverApi.GetPlayerList()

        textBoardSystem = serverApi.GetSystem("neteaseTextBoard", "neteaseTextBoardDev")

        self.sendCmd('/gamerule naturalregeneration false', playerId)

        if not self.isInit:
            self.sendCmd("/gamerule falldamage false", playerId)
            self.isInit = True

    def OnServerPlayerTryDestroyBlock(self, data):
        data['cancel'] = True
        if 'lobby' in commonNetgameApi.GetServerType():
            lobbyGameApi.TryToKickoutPlayer(data['playerId'], '§6与服务器断开连接')

    def OnServerPlayerTryDestroyBlock(self, data):
        data['cancel'] = True
        if 'lobby' in commonNetgameApi.GetServerType():
            lobbyGameApi.TryToKickoutPlayer(data['playerId'], '§6与服务器断开连接')

    def OnPlayerAttackEntity(self, data):
        playerId = data['playerId']
        victimId = data['victimId']

        # Points:
        # 81 149 79
        # 134 189 132
        #
        # Spawn: 107 153 105
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        playerPos = comp.GetPos()
        comp = serverApi.GetEngineCompFactory().CreatePos(victimId)
        victimPos = comp.GetPos()

        if (victimPos[1]>175 or playerPos[1]>175) and victimId in serverApi.GetPlayerList():
            data['cancel'] = True

    def OnPlayerDie(self, data):
        playerId = data['id']
        attacker = data['attacker']

        self.sendCmd('/kill @e[type=item]', attacker)

    def OnActuallyHurtServer(self, data):
        playerId = data['entityId']
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        playerPos = comp.GetPos()
        if playerPos[1] >= 175:
            data['damage'] = 0

    def OnCommand(self, data):
        # playerId = data['entityId']
        # cmd = data['command'].split()
        # print 'OnCommand cmd='+cmd+' playerId='+playerId
        #
        # if cmd[0] == "hub" or cmd[0] == "kill":
        #     data['cancel'] = True
        #     comp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        #     comp.KillEntity(playerId)

        pass