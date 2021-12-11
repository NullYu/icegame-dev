# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import math
import operator
import random
import datetime
import fbScript.fbConsts as c
import json
import lobbyGame.netgameConsts as netgameConsts
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.commonNetgameApi as commonNetgameApi

import apolloCommon.mysqlPool as mysqlPool

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

initScoreboard = False

scoreboard = {}

# 在modMain中注册的Server System类
class fbServerSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()
        lobbyGameApi.ShieldPlayerJoinText(True)

        self.scores = {}
        self.teams = {}
        self.scoreBuffer = 0
        self.voted = 0
        self.currentlyVoting = 0

        # 1 2 3 4 Red Yellow Blue Green

        self.waiting = []
        self.status = 0

        self.countdown = 180
        self.timer = 0
        self.buildTime = False
        self.isVoting = False

        self.consts = c

        self.theme = None

    ##############UTILS##############

    def playStartAnimation(self):
        for player in serverApi.GetPlayerList():
            commonNetgameApi.AddTimer(0.2, lambda p: self.sendTitle('§c§l开      战', 1, p), player)
            commonNetgameApi.AddTimer(0.4, lambda p: self.sendTitle('§c§l开     战', 1, p), player)
            commonNetgameApi.AddTimer(0.6, lambda p: self.sendTitle('§c§l开    战', 1, p), player)
            commonNetgameApi.AddTimer(0.8, lambda p: self.sendTitle('§c§l开   战', 1, p), player)
            commonNetgameApi.AddTimer(1.0, lambda p: self.sendTitle('§c§l开  战', 1, p), player)
            commonNetgameApi.AddTimer(1.2, lambda p: self.sendTitle('§c§l开 战', 1, p), player)
            commonNetgameApi.AddTimer(1.4, lambda p: self.sendTitle('§c§l开战', 1, p), player)
            commonNetgameApi.AddTimer(1.4, lambda p: self.sendTitle('§6保护您的床！', 2, p), player)

    def rank(self, d):
        mComp = 0
        for item in d:
            if (not mComp in d or d[item] > d[mComp]) and item in self.teams:
                mComp = item
        return mComp

    def getIfLegalBreak(self, pos):
        for player in self.blocks:
            if pos in self.blocks[player]:
                return True
        return False

    def getCountInList(self, key, li):
        count = 0
        for item in li:
            if key == li[item]:
                count += 1
        return count

    def getMatchingList(self, key, object):
        ret = []
        for item in object:
            if key == object[item]:
                ret.append(item)
        return ret

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

    def getKeyFromUnqValue(self, value, dic):
        for key in dic:
            if dic[key] == value:
                return key

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

    def updateScoreboard(self):
        self.scoreboard(1, 1, "§3当前阶段：§r")
        self.scoreboard(1, 4, '" "')
        self.scoreboard(1, 5, "§e将在倒计时结束后自动开始")
        self.scoreboard(1, 6, "§c180§f秒")
        self.scoreboard(1, 7, '""')
        self.scoreboard(1, 8, "§7ICE-BW-%s" % (lobbyGameApi.GetServerId(),))

    def InitArena(self):
        print 'ARENA INIT!!!'
        lobbyGameApi.ResetServer()

    def setPos(self, playerId, pos):
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        re = comp.SetFootPos(pos)
        return re

    def dist(self, x1, y1, z1, x2, y2, z2):
        """
        运算3维空间距离，返回float
        """
        p = ((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) ** 0.5
        re = float('%.1f' % p)
        return re

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

    #################################

    def ListenEvents(self):
        self.ListenForEvent('fb', 'fbClient', 'VoteEvent', self, self.OnVote)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnScriptTickServer", self, self.OnScriptTickServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DamageEvent", self, self.OnDamage)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerAttackEntityEvent", self, self.OnPlayerAttackEntity)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerEntityTryPlaceBlockEvent", self, self.OnServerEntityTryPlaceBlock)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerPlayerTryDestroyBlockEvent", self, self.OnServerPlayerTryDestroyBlock)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self,
                            self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent",
                            self,
                            self.OnAddServerPlayer)

        lobbyGameApi.ChangePerformanceSwitch(netgameConsts.DisableSwitch.RecipesSyncOnLogin, True)


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
        comp.SetGameDifficulty(0)
        lobbyGameApi.ShieldPlayerJoinText(True)
        commonNetgameApi.AddRepeatedTimer(1.0, self.tick)
        commonNetgameApi.AddRepeatedTimer(1.0, self.BoardTick)

        comp = serverApi.GetEngineCompFactory().CreateBlockUseEventWhiteList(serverApi.GetLevelId())
        for i in range(16):
            comp.AddBlockItemListenForUseEvent("minecraft:bed:%s" % i)

        def b():
            args = {
                'sid': lobbyGameApi.GetServerId(),
                'value': 0
            }
            serverId = lobbyGameApi.GetServerId()
            print 'init recordsid'
            self.RequestToServiceMod("service_bw", "RecordSidEvent", args)
        commonNetgameApi.AddTimer(8.0, b)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("gameutils", "gameutilsClient", 'TestRequest', self, self.OnTestRequest)

    def OnDamage(self, data):
        data['damage'] = 0

    def OnScriptTickServer(self):
        for player in self.teams:
            comp = serverApi.GetEngineCompFactory().CreatePos(player)
            playerPos = comp.GetFootPos()
            relative = (self.teams[player]+1)*200

            if self.buildTime:
                relative = (self.teams[player]+1) * 200
                if self.dist(playerPos[0], playerPos[1], playerPos[2], relative, 4, 0) > 50:
                    self.setPos(player, (relative, 4, 15))
            elif self.currentlyVoting:
                relative = self.currentlyVoting+1*200
                if self.dist(playerPos[0], playerPos[1], playerPos[2], relative, 4, 0) > 50:
                    self.setPos(player, (relative, 4, 15))


        for player in serverApi.GetPlayerList():
            if self.status == 1 and player not in self.teams:
                self.sendCmd('/clear @s', player)

    def OnServerPlayerTryDestroyBlock(self, data):
        playerId = data['playerId']
        x = data['x']
        y = data['y']
        z = data['z']
        relative = (self.teams[playerId]+1) * 200

        print 'desblock rel=', relative, 'isBuildtime=', self.buildTime

        if x >= (relative + 15) or x <= (relative - 15) or z >= 30 or z <= -30 or y < 4 or not self.buildTime:
            data['cancel'] = True

    def OnPlayerAttackEntity(self, data):
        data['cancel'] = True

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        uid = data['uid']
        if playerId in self.waiting:
            self.waiting.pop(self.waiting.index(playerId))
        if playerId in self.teams:
            self.teams.pop(playerId)

    def OnServerEntityTryPlaceBlock(self, data):
        x = data['x']
        y = data['y']
        z = data['z']
        name = data['fullName']
        playerId = data['entityId']
        relative = (self.teams[playerId]+1)*200

        print 'placeblock data=' % data

        if x >= (relative + 15) or x <= (relative - 15) or z >= 30 or z <= -30 or y < 4 or not self.buildTime:
            data['cancel'] = True

    def OnAddServerPlayer(self, data):
        playerId = data['id']

        self.updateServerStatus(self.status)

        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        comp.SpawnItemToArmor({
            'itemName': 'minecraft:diamond_helmet',
            'count': 0,
            'auxValue': 0
        }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.HEAD)
        comp.SpawnItemToArmor({
            'itemName': 'minecraft:diamond_chestplate',
            'count': 0,
            'auxValue': 0
        }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.BODY)
        comp.SpawnItemToArmor({
            'itemName': 'minecraft:diamond_leggings',
            'count': 0,
            'auxValue': 0
        }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.LEG)
        comp.SpawnItemToArmor({
            'itemName': 'minecraft:diamond_boots',
            'count': 0,
            'auxValue': 0
        }, playerId, serverApi.GetMinecraftEnum().ArmorSlotType.FOOT)

        comp = serverApi.GetEngineCompFactory().CreateGame(playerId)
        comp.SetDisableHunger(True)
        self.sendCmd("/clear", playerId)
        self.setPos(playerId, c.lobbyPos)
        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        for i in range(36):
            comp.SpawnItemToPlayerInv({
                'itemName': 'minecraft:dirt',
                'count': 0
            }, playerId, i)
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        serverId = lobbyGameApi.GetServerId()

        if self.status == 0:
            def a():
                if self.status == 0:
                    self.sendMsg("§a您来的正是时候！请等待游戏开始。", playerId)
            commonNetgameApi.AddTimer(9.0, a)
            self.waiting.append(playerId)
            utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
            utilsSystem.SetPlayerSpectate(playerId, False)
        elif self.status >= 1:
            utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
            utilsSystem.SetPlayerSpectate(playerId, True)

    def BoardTick(self):
        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        do = utilsSystem.TextBoard
        if self.status == 0:
            for player in serverApi.GetPlayerList():
                self.sendCmd('/gamerule sendcommandfeedback false', player)
                self.sendCmd('/gamerule showdeathmessages false', player)
                do(player, True, """
§e§lICE§a_§bGAME§r§l -> §l§6速建大师§r

§7满%s人即可开始游戏§r
§l目前人数: §e%s人
§f倒计时: §c%s秒

§r§e在ICE_GAME体验速建大师
§l§4警告： §c建造违规违法内容可被永久封禁
§7%s
""" % (c.startCountdown, len(self.waiting), self.countdown, self.epoch2Datetime(time.time())))

        elif self.status == 1:
            for player in serverApi.GetPlayerList():
                if self.buildTime:
                    do(player, True, """§e§lICE§a_§bGAME§r§l -> §l§6速建大师§r

§l§a当前阶段： §f建造
§l§3建筑主题： §f%s

§r§e在ICE_GAME体验速建大师
§l§4警告： §c建造违规违法内容可被永久封禁
""" % self.theme)
                else:
                    do(player, True, """§e§lICE§a_§bGAME§r§l -> §l§6速建大师§r

§l§a当前阶段： §e评分
§l§b正在评分： §f%s§b的作品
§l§6已完成评分： §e%s/%s
§c点击左下角举报按钮检举违规作品!

§r§e在ICE_GAME体验速建大师
§l§4警告： §c建造违规违法内容可被永久封禁
""" % (self.getKeyFromUnqValue(self.currentlyVoting - 1, self.teams), self.voted, len(self.teams)))


    def tick(self):
        # per tick updates
        count = len(serverApi.GetPlayerList())

        if self.status == 0:
            print 'countdown=%s' % self.countdown
            self.timer = 0
            self.scoreboard(1, 6, "§c%s§f秒" % self.countdown)
            enough = c.enoughPlayers
            if count < c.startCountdown:
                pass
            elif c.startCountdown <= count <= enough:
                self.countdown -= 1
                for player in serverApi.GetPlayerList():
                    self.sendTitle("§e§l%s" % self.countdown, 1, player)
                    self.sendTitle("游戏即将开始", 2, player)
            if count == enough and self.countdown > 15:
                self.countdown = 15
            if self.countdown < 180 and count < c.startCountdown:
                self.sendMsgToAll("§c§l人数不够，倒计时取消！")
                self.countdown = 180
            if self.countdown == 0:
                print 'starting!'
                self.start()
                self.status = 1
        if self.status == 1:

            if self.buildTime:
                self.timer -= 1

            if self.timer == 0 and not self.isVoting:
                self.buildTime = False
                self.isVoting = True
                self.sendMsgToAll('§e时间到！ 即将开始投票环节')
                commonNetgameApi.AddTimer(4.0, self.StartVoting)

        self.updateServerStatus(self.status)

    def StartVoting(self):
        for player in serverApi.GetPlayerList():
            self.NotifyToClient(player, 'StartVotingEvent', None)
        self.voted = 0
        self.scoreBuffer = 0
        self.VoteRoutine()

    def OnVote(self, data):
        playerId = data['playerId']
        score = data['score']+1
        print 'onvote score=', score

        if score == 0:
            vkickSystem = serverApi.GetSystem('vkick', 'vkickSystem')
            vkickSystem.OnCommand({
                'playerId': playerId,
                'command': '/vk %s fbkick' % lobbyGameApi.GetPlayerNickname(self.getKeyFromUnqValue(self.currentlyVoting, self.teams)),
                'cancel': False
            })

        self.scoreBuffer += score
        self.voted += 1
        self.sendTitle('§a§l%s分' % score, 1, playerId)
        self.sendTitle('你的评价是', 2, playerId)

        if self.voted >= len(self.teams):
            try:
                self.scores[self.getKeyFromUnqValue(self.currentlyVoting, self.teams)] = round(self.scoreBuffer/float(len(serverApi.GetPlayerList())), 2)
            except:
                pass
            self.VoteRoutine()

    def VoteRoutine(self):
        self.voted = 0
        self.scoreBuffer = 0
        self.currentlyVoting += 1

        # Vote done
        if self.currentlyVoting > len(self.teams):
            self.Conclude()
            return

        for player in serverApi.GetPlayerList():
            self.NotifyToClient(player, 'StartVotingEvent', None)

        voteTarget = self.getKeyFromUnqValue(self.currentlyVoting - 1, self.teams)
        for player in self.teams:
            self.sendTitle('§6§l%s' % player, 1, player)
            self.sendTitle('§a正在评价', 2, player)

        relative = (self.teams[voteTarget]+1)*200
        print 'new vote started, rel=%s' % relative
        for player in serverApi.GetPlayerList():
            print 'setpos execute %s' % relative
            self.sendCmd('/tp %s 10 15' % relative, player)
            print 'setpos verif getpos %s' % serverApi.GetEngineCompFactory().CreatePos(player).GetPos()

        self.sendMsgToAll('§b正在评分§e%s的作品！ §l§6赶紧给TA打分吧!' % lobbyGameApi.GetPlayerNickname(voteTarget))

    def Conclude(self):
        self.sendMsgToAll('§a§l所有作品已评分完毕！ 即将结算。。。')

        def d():
            dic = self.scores

            # TODO Debug statement
            self.sendMsgToAll(dic)

            dsq = []
            for player in self.scores:
                if self.scores[player] < 1:
                    dsq.append(player)
            for player in dsq:
                dic.pop(player)

            print 'before_done, dic=%s, type=%s' % (dic, type(dic))
            sorted_x = sorted(dic.items(), key=operator.itemgetter(1))
            sorted_x.reverse()
            dic = sorted_x
            print 'done, dic=%s, type=%s' % (dic, type(dic))
            msg = "§e§l本次排名如下:\n§r§a"
            for tup in dic:
                msg += "第%s名 §b%s §e%s分§a\n" % (dic.index(tup) + 1, lobbyGameApi.GetPlayerNickname(tup[0]), tup[1])
            for player in dsq:
                msg += "§l§4DSQ §r§b%s§a\n" % lobbyGameApi.GetPlayerNickname(player)
            self.sendMsgToAll(msg)

            player = dic[1]
            self.sendTitle("§6§l最高分", 1, player)
            self.sendTitle("恭喜您获得最高分 ！！！", 2, player)
            self.sendMsg("§a+128NEKO +2CREDITS §f获得胜利的奖励", player)
            ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')
            ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(player), 128, 'fb win')
            ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(player), 2, 'fb win', True)
            utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
            utilsSystem.ShowWinBanner(player)

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
                self.InitArena()

            commonNetgameApi.AddTimer(17.0, b)
        commonNetgameApi.AddTimer(3.0, d)

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
            self.sendMsg("§3即将将您传送至game_bw-%s，请稍等片刻" % (sid,), playerId)
            def a():
                transData = {'position': [1, 2, 3]}
                lobbyGameApi.TransferToOtherServerById(playerId, sid, json.dumps(transData))
            commonNetgameApi.AddTimer(1.0, a)

    def start(self):
        # team assignment

        # ## Timer Set ## #
        serverType = commonNetgameApi.GetServerType()
        times = {
            # TODO Change debug section
            'game_900fb1': 900,
            'game_300fb1': 300,
            'game_60fb1': 10
        }

        self.timer = int(serverType[0:-3])
        self.scores = {}
        self.teams = {}
        self.theme = random.choice(c.themes)
        comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
        for player in self.waiting:
            self.scores[player] = 0
            self.teams[player] = self.waiting.index(player)
            self.sendTitle('§b§l%s' % self.theme, 1, player)
            self.sendTitle('§3本次建筑主题为', 2, player)

            self.sendCmd('/gamemode c', player)

            commonNetgameApi.AddTimer(3.0, lambda p: self.NotifyToClient(p, 'ShowStartScreen', {
                'theme': self.theme,
                'time': self.timer
            }), player)

        def a():
            musicSystem = serverApi.GetSystem('music', 'musicSystem')
            for player in serverApi.GetPlayerList():
                musicSystem.PlayMusicToPlayer(player, 'sfx.generic.start')
        commonNetgameApi.AddTimer(10.0, a)
        def b(): self.buildTime = True
        commonNetgameApi.AddTimer(11.0, b)

        self.waiting = []
        for player in self.teams:
            self.setPos(player, ((self.teams[player]+1)*200, 4, 15))
            print 'set pos of %s to %s' % (lobbyGameApi.GetPlayerNickname(player), (self.teams[player]+1)*200)
