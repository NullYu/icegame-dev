# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import json
import math
import datetime
import random
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.commonNetgameApi as commonNetgameApi
import apolloCommon.mysqlPool as mysqlPool

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

initScoreboard = False

scoreboard = {}

# 在modMain中注册的Server System类
class tntrServerSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()
        self.consts = None
        lobbyGameApi.ShieldPlayerJoinText(True)

        self.countdown = 0
        self.timer = 0
        self.status = 0

        self.playing = []
        self.waiting = []

        type = commonNetgameApi.GetServerType()
        print 'server type is %s' % type
        if type == 'game_tntrT1':
            import tntrScript.tntrConsts1 as c
            self.consts = c

        # global c
        print 'self.consts = ', self.consts

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

    def sendMsgToAll(self, msg):
        for player in serverApi.GetPlayerList():
            self.sendMsg(msg, player)

    def sendCmdToAll(self, msg):
        for player in serverApi.GetPlayerList():
            self.sendCmd(msg, player)

    def scoreboard(self, mode, line, content='none'):
        # 1 = set
        # 2 = delete
        if serverApi.GetPlayerList():
            playerId = serverApi.GetPlayerList()[0]

            if mode == 1:
                if line in scoreboard.keys():
                    self.sendCmd("/scoreboard players reset %s main" % (scoreboard[line],), playerId)
                scoreboard[line] = content
                self.sendCmd("/scoreboard players set %s main %s" % (content, line), playerId)
            elif mode == 2:
                self.sendCmd("/scoreboard players reset %s main" % (scoreboard[line],), playerId)

    def updateServerStatus(self, status):
        args = {
            'sid': lobbyGameApi.GetServerId(),
            'value': status,
            'count': len(serverApi.GetPlayerList())
        }
        serverId = lobbyGameApi.GetServerId()
        print 'init recordsid'
        self.RequestToServiceMod("service_bw", "RecordSidEvent", args)

    def epoch2Datetime(self, epoch):
        ts = datetime.datetime.fromtimestamp(int(epoch)+0)
        return ts.strftime('%Y-%m-%d %H:%M:%S')

    def blockPosChange(self, pos):
        pos = list(pos)
        for i in range(3):
            if int(pos[i]) > 0:
                pos[i] = int(pos[i])
            else:
                pos[i] = math.floor(pos[i])
        pos = tuple(pos)
        return pos

    def getBlockBelow(self, playerId):
        # console warning suppressor
        try:
            comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
            footPos = comp.GetFootPos()
            comp = serverApi.GetEngineCompFactory().CreateBlockInfo(playerId)
            return comp.GetBlockNew(self.blockPosChange((footPos[0], footPos[1]-1, footPos[2])))
        except TypeError:
            pass

    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnScriptTickServer", self,
                            self.OnScriptTickServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerAttackEntityEvent", self, self.OnPlayerAttackEntity)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self,
                            self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent",
                            self,
                            self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerEntityTryPlaceBlockEvent",
                            self,
                            self.OnServerEntityTryPlaceBlock)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ActuallyHurtServerEvent",
                            self,
                            self.OnActuallyHurtServer)


        gameComp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        gameComp.SetCanBlockSetOnFireByLightning(False)
        gameComp.SetCanActorSetOnFireByLightning(False)

        comp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        ruleDict = {
            'option_info': {
                'natural_regeneration': True,  # 自然生命恢复
                'immediate_respawn': True  # 作弊开启
            },
            'cheat_info': {
                'always_day': True,  # 终为白日
                'mob_griefing': False,  # 生物破坏方块
                'keep_inventory': False,  # 保留物品栏
                'weather_cycle': False,  # 天气更替
                'mob_spawn': False,  # 生物生成
            }
        }
        comp.SetGameRulesInfoServer(ruleDict)
        comp.SetGameDifficulty(2)
        lobbyGameApi.ShieldPlayerJoinText(True)
        commonNetgameApi.AddRepeatedTimer(1.0, self.tick)
        commonNetgameApi.AddRepeatedTimer(1.0, self.boardtick)


    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("gameutils", "gameutilsClient", 'TestRequest', self, self.OnTestRequest)

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        uid = data['uid']
        if playerId in self.waiting:
            self.waiting.pop(self.waiting.index(playerId))
        if playerId in self.playing:
            self.Eliminate(playerId, True)

        self.updateServerStatus(self.status)
    def OnAddServerPlayer(self, data):
        playerId = data['id']
        comp = serverApi.GetEngineCompFactory().CreateGame(playerId)
        comp.SetDisableHunger(True)
        self.sendCmd("/clear", playerId)
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        comp.SetFootPos(self.consts.lobbyPos)
        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        for i in range(36):
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:dirt',
                'count': 0
            }, playerId, i)
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        serverId = lobbyGameApi.GetServerId()

        def a():
            if len(self.playing) == 0:
                self.sendMsg("§a您来的正是时候！请等待游戏开始。", playerId)
        commonNetgameApi.AddTimer(9.0, a)
        self.waiting.append(playerId)

    def OnServerEntityTryPlaceBlock(self, data):
        data['cancel'] = True

    def OnPlayerAttackEntity(self, data):
        if self.status == 1 and self.timer >= 30:
            return

        data['cancel'] = True

    def OnActuallyHurtServer(self, data):
        playerId = data['entityId']
        data['damage'] = 0

    def boardtick(self):
        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        do = utilsSystem.TextBoard
        if self.status == 0:
            for player in serverApi.GetPlayerList():
                self.sendCmd('/gamerule sendcommandfeedback false', player)
                self.sendCmd('/gamerule showdeathmessages false', player)
                do(player, True, """
§e§lICE§a_§bGAME§r§l -> §cTNT§e跑酷

§7满%s人即可开始游戏§r
§l目前人数: §e%s人
§f倒计时: §c%s秒

§r§e在ICE_GAME体验TNT跑酷
§7%s
""" % (self.consts.startCountdown, len(self.waiting), self.countdown, self.epoch2Datetime(time.time())))
        elif self.status == 1:
            for player in serverApi.GetPlayerList():
                do(player, True, """
§e§lICE§a_§bGAME§r§l -> §cTNT§e跑酷

§r§c§l努力活到最后！
§r§3比赛已进行§f%s
§e§l在00:30秒后可以击打其他玩家

§r§e在ICE_GAME体验TNT跑酷
""" % (datetime.timedelta(seconds=self.timer),))

    def tick(self):
        # per tick updates
        count = len(serverApi.GetPlayerList())

        if self.status == 0:
            print 'countdown=%s' % self.countdown
            self.timer = 0
            self.scoreboard(1, 6, "§c%s§f秒" % self.countdown)
            enough = self.consts.enoughPlayers
            if count < self.consts.startCountdown:
                pass
            elif self.consts.startCountdown <= count <= enough:
                self.countdown -= 1
                for player in serverApi.GetPlayerList():
                    self.sendTitle("§e§l%s" % self.countdown, 1, player)
                    self.sendTitle("游戏即将开始", 2, player)
            if count == enough and self.countdown > 15:
                self.countdown = 15
            if self.countdown < 180 and count < self.consts.startCountdown:
                self.sendMsgToAll("§c§l人数不够，倒计时取消！")
                self.countdown = 180
            if self.countdown == 0:
                print 'starting!'
                self.start()
                self.status = 1

        if self.status == 1:
            self.timer += 1

            if self.timer == 30:
                for player in self.playing:
                    self.sendTitle("§l00:30", 1, player)
                    self.sendTitle("§6§l玩家伤害已开启", 2, player)

        self.updateServerStatus(self.status)

    def start(self):
        self.timer = 0
        for player in self.waiting:
            self.playing.append(player)
            self.sendTitle("§e3秒后进入比赛，请找好位置", 1, player)
            self.sendCmd('/effect @s night_vision 9999 1 true', player)
        self.waiting = []

        def a():
            p1 = self.consts.lobbyLevel1
            p2 = self.consts.lobbyLevel2
            self.sendCmd('/fill %s %s %s %s %s %s air' % (
                p1[0], p1[1], p1[2], p2[0], p2[1]+4, p2[2]
            ), self.playing[0])
        commonNetgameApi.AddTimer(3.0, a)

        self.status = 1

    def blocktick(self):
        if self.status == 1 and len(self.playing) > 1 and self.timer > 4:
            for player in self.playing:
                comp = serverApi.GetEngineCompFactory().CreatePos(player)
                # xPos = int(round(comp.GetFootPos()[0]))
                # yPos = comp.GetFootPos()[1]-1
                # zPos = int(round(comp.GetFootPos()[2]))
                # self.sendCmd('/setblock %s %s %s air' % (xPos, yPos, zPos), player)

                xPos = comp.GetFootPos()[0]
                yPos = comp.GetFootPos()[1] - 1
                zPos = comp.GetFootPos()[2]
                def getDecimal(num):
                    return num - math.floor(num)

                self.sendCmd('/setblock %s %s %s air' % (xPos, yPos, zPos), player)
                if getDecimal(xPos) < 0.3:
                    self.sendCmd('/setblock %s %s %s air' % (xPos-1, yPos, zPos), player)
                elif getDecimal(xPos) > 0.7:
                    self.sendCmd('/setblock %s %s %s air' % (xPos+1, yPos, zPos), player)\

                if getDecimal(zPos) < 0.3:
                    self.sendCmd('/setblock %s %s %s air' % (xPos, yPos, zPos-1), player)
                elif getDecimal(zPos) > 0.7:
                    self.sendCmd('/setblock %s %s %s air' % (xPos, yPos, zPos+1), player)

    def eliminate(self, playerId):
        self.playing.pop(self.playing.index(playerId))
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        comp.SetPos(self.consts.spectatorPos)
        self.sendMsgToAll("%s §c§l已被淘汰，§r§c剩余§e%s§c名玩家" % (lobbyGameApi.GetPlayerNickname(playerId), len(self.playing)))

        if len(self.playing) == 1:
            self.win(self.playing[0])

    def BwMatchmakingCallback(self, suc, data):
        if not suc:
            print 'OnCallback timeout'
            return
        value = data['value']
        playerId = data['playerId']

        if value == 0:
            self.sendMsg("§c§l无法分配房间：§r没有开放的房间可供您加入。稍后将您传送回主城。", playerId)
            def a():
                transData = {'position': [1, 2, 3]}
                lobbyGameApi.TransferToOtherServer(playerId, 'lobby', json.dumps(transData))
            commonNetgameApi.AddTimer(3.0, a)
            return
        elif value == 1:
            sid = data['sid']
            self.sendMsg("§3即将将您传送至game_tntr-%s，请稍等片刻" % (sid,), playerId)
            def a():
                transData = {'position': [1, 2, 3]}
                lobbyGameApi.TransferToOtherServerById(playerId, sid, json.dumps(transData))
            commonNetgameApi.AddTimer(1.0, a)

    def win(self, player):
        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        utilsSystem.ShowWinBanner(player)
        self.sendTitle("§6§l胜利", 1, player)
        self.sendTitle("恭喜您获得胜利！！！", 2, player)
        self.sendMsg("§a+64NEKO §f获得胜利的奖励", player)
        ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')
        ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(player), 64, 'tntr win')

        def a():
            self.status = 0
            self.updateServerStatus(self.status)
            for p in serverApi.GetPlayerList():
                self.RequestToServiceMod("bw", "RequestMatchmakingEvent", {
                    'playerId': p,
                    'mode': commonNetgameApi.GetServerType()
                }, self.BwMatchmakingCallback, 2)

            self.countdown = 180

            rebootSystem = serverApi.GetSystem('reboot', 'rebootSystem')
            rebootSystem.DoReboot(False)

        commonNetgameApi.AddTimer(15.0, a)

        def b():
            lobbyGameApi.ResetServer()

        commonNetgameApi.AddTimer(17.0, b)

    def OnScriptTickServer(self):
        self.blocktick()

        if self.status == 1 and len(self.playing) > 1:
            for player in self.playing:
                pos = serverApi.GetEngineCompFactory().CreatePos(player).GetPos()
                if pos[1] <= -5:
                    self.eliminate(player)
