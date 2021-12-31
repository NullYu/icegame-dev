# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import math
import random
import datetime
import json
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.commonNetgameApi as commonNetgameApi
import mmScript.mmConsts as c
import apolloCommon.mysqlPool as mysqlPool

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

initScoreboard = False

scoreboard = {}

# 在modMain中注册的Server System类
class mmServerSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()
        self.consts = c
        lobbyGameApi.ShieldPlayerJoinText(True)

        self.waiting = []
        self.status = 0
        self.playing = {}
        self.timer = 0
        self.kills = {}
        self.countdown = 180

        self.detectiveLastSeen = ()
        self.bowShotCooldown = 0

        self.arenaIsInit = False
        self.init = False

    ##############UTILS##############

    def playStartAnimation(self):
        for player in serverApi.GetPlayerList():
            commonNetgameApi.AddTimer(0.2, lambda p: self.sendTitle('§d§l开      战', 1, p), player)
            commonNetgameApi.AddTimer(0.4, lambda p: self.sendTitle('§d§l开     战', 1, p), player)
            commonNetgameApi.AddTimer(0.6, lambda p: self.sendTitle('§d§l开    战', 1, p), player)
            commonNetgameApi.AddTimer(0.8, lambda p: self.sendTitle('§d§l开   战', 1, p), player)
            commonNetgameApi.AddTimer(1.0, lambda p: self.sendTitle('§d§l开  战', 1, p), player)
            commonNetgameApi.AddTimer(1.2, lambda p: self.sendTitle('§d§l开 战', 1, p), player)
            commonNetgameApi.AddTimer(1.4, lambda p: self.sendTitle('§d§l开战', 1, p), player)
            commonNetgameApi.AddTimer(1.4, lambda p: self.sendTitle('§e不要被杀手刺中！', 2, p), player)

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

    def board(self, player, msg):
        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        utilsSystem.TextBoard(player, True, msg)

    def InitArena(self):
        print 'ARENA INIT!!!'



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
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self, self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self, self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ActorAcquiredItemServerEvent", self, self.OnActorAcquiredItemServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DamageEvent", self, self.OnDamage)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerRespawnFinishServerEvent", self, self.OnPlayerRespawnFinishServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerChatEvent", self, self.OnServerChat)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerAttackEntityEvent", self, self.OnPlayerAttackEntity)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ActorUseItemServerEvent", self, self.OnActorUseItemServer)


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
                'mob_griefing': True,  # 生物破坏方块
                'keep_inventory': False,  # 保留物品栏
                'weather_cycle': False,  # 天气更替
                'mob_spawn': False,  # 生物生成
            }
        }
        comp.SetGameRulesInfoServer(ruleDict)
        comp.SetGameDifficulty(2)
        lobbyGameApi.ShieldPlayerJoinText(True)
        commonNetgameApi.AddRepeatedTimer(1.0, self.tick)
        commonNetgameApi.AddRepeatedTimer(1.0, self.BoardTick)
        commonNetgameApi.AddRepeatedTimer(0.5, self.BowCDTick)
        gameComp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        gameComp.SetCanBlockSetOnFireByLightning(False)
        gameComp.SetCanActorSetOnFireByLightning(False)

        def b():
            args = {
                'sid': lobbyGameApi.GetServerId(),
                'value': 0
            }
            serverId = lobbyGameApi.GetServerId()
            print 'init recordsid'
            self.RequestToServiceMod("service_sw", "RecordSidEvent", args)
        commonNetgameApi.AddTimer(8.0, b)

    def OnAddServerPlayer(self, data):
        playerId  = data['id']
        if self.status == 0:
            self.waiting.append(playerId)
            commonNetgameApi.AddTimer(6.0, lambda p: self.sendMsg('§a您来的正是时候！请等待游戏开始', p), playerId)
            self.setPos(playerId, c.lobbyPos)
            utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
            utilsSystem.SetPlayerSpectate(playerId, False)
        elif self.status == 1:
            utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
            utilsSystem.SetPlayerSpectate(playerId, True)


    def OnDelServerPlayer(self, data):
        playerId = data['id']
        if playerId in self.waiting:
            self.waiting.pop(playerId)
        if playerId in self.playing:
            self.playing.pop(playerId)

    def OnPlayerRespawnFinishServer(self, data):
        playerId = data['playerId']
        if self.status == 0:
            self.sendMsg('§c§l请不要在密室杀手中尝试/kill命令！', playerId)
        elif self.status == 1:
            if playerId in self.playing:
                role = self.playing[playerId]
                if role == 1:
                    self.sendMsgToAll('§e§l现任侦探放弃了游戏!')
                    self.sendMsg('§4§l警告： §r§c您主动放弃了游戏。继续消极比赛您将受到惩罚。', playerId)
                    self.Elim(playerId, 4)
                    self.DropBow(playerId)
                elif role == 2:
                    self.sendMsgToAll('§e§l杀手放弃了游戏!')
                    self.sendMsg('§4§l警告： §r§c您主动放弃了游戏。继续消极比赛您将受到惩罚。', playerId)
                    self.Elim(playerId, 4)
                    self.sendMsgToAll("§l§e杀手已落网。§r§b侦探§f和平民获得胜利。")
                    print 'status set to 2, line 239'
                    self.status = 2

                    ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')
                    for player in self.playing:
                        if self.playing != 2:
                            self.sendTitle("§6§l胜利", 1, player)
                            self.sendTitle("恭喜您获得胜利！！！", 2, player)
                            self.sendMsg("§a+32NEKO §f获得胜利的奖励", player)
                            ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(player), 32, 'mm win')
                    try:
                        self.sendMsg('§c+0NEKO §f杀手放弃比赛前未能逮捕杀手', self.getMatchingList(1, self.playing))
                    except:
                        pass

                    def a():
                        self.status = 0
                        self.InitArena()
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
                elif role == 3:
                    self.sendMsg('§4§l警告： §r§c您主动放弃了游戏。继续消极比赛您将受到惩罚。', playerId)
                    self.Elim(playerId, 4)

    def OnActorAcquiredItemServer(self, data):
        playerId = data['actor']
        itemName = data['newItemName']

        if itemName == "minecraft:bow" and data["acquireMethod"] == 1 and playerId in self.playing and self.playing[playerId] != 1:
            self.sendTitle("§a§l您成为了新的侦探！", 1, playerId)
            self.sendMsgToAll("§2侦探之弓已被捡起")
        else:
            self.sendCmd("/clear", playerId)
            comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
            pos = comp.GetPos()
            itemDict = {
                'itemName': 'minecraft:bow',
                'count': 1,
            }
            comp = serverApi.GetEngineCompFactory().CreateItem(serverApi.GetLevelId())
            comp.SpawnItemToLevel(itemDict, 0, pos)

    def OnServerChat(self, data):
        playerId = data['playerId']
        username = data['username']
        msg = data['message']
        data['cancel'] = True
        msgNew = '§3%s: §7%s' % (username, msg.strip('§'))

        if self.status != 1:
            self.sendMsgToAll(msgNew)
        else:
            if playerId in self.playing:
                role = self.playing[playerId]
                if role == 1:
                    self.sendMsgToAll('§b§l►§r'+msgNew)
                elif role == 2:
                    self.sendMsgToAll('§c§l►§r§3%s: §7%s' % ('⬛'*len(username), msg.strip('§')))
                else:
                    count = 0
                    comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
                    posSrc = comp.GetPos()
                    for player in serverApi.GetPlayerList():
                        comp = serverApi.GetEngineCompFactory().CreatePos(player)
                        posTar = comp.GetPos()
                        if self.dist(posSrc[0], posSrc[1], posSrc[2], posTar[0], posTar[1], posTar[2]) <= 10 or player not in self.playing:
                            self.sendMsg(('§f§l►§r§3%s: §7%s' % ('⬛'*len(username), msg.strip('§'))), player)
                            count += 1
                    self.sendMsg('§6平民发言仅能被10格内的玩家看到。\n§b§l%s§r名玩家看到了您的信息' % count, playerId)
            else:
                self.sendMsg('§e观战者不能发言。', playerId)

    def OnPlayerAttackEntity(self, data):
        playerId = data['playerId']
        victimId = data['victimId']
        data['damage'] = 0

        if self.status != 1:
            data['cancel'] = True
            return

        if victimId in self.playing:
            role = self.playing[victimId]

        if playerId not in self.playing or victimId not in self.playing or self.playing[playerId] != 2:
            data['cancel'] = True
            return

        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        carried = comp.GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0)
        if self.playing[playerId] == 2 and carried and carried["itemName"] == 'minecraft:iron_sword':
            self.sendTitle("§b", 1, playerId)
            self.sendTitle("§a干得漂亮！", 2, playerId)
            self.Elim(victimId, 2)
        else:
            data['cancel'] = True

        # elif self.playing[playerId] == 1 or self.playing[playerId] == 3:
        #     if role == 2:
        #         # TODO Win: murder killed
        #         pass
        #     else:
        #         self.Elim(victimId, 1)
        #         self.Elim(playerId, 3)

        if role == 1:
            print '**DETECTIVE KILLED**'
            self.DropBow(victimId)

    def OnActorUseItemServer(self, data):
        playerId = data['playerId']
        item = data['itemDict']

        if self.status == 1 and playerId in self.playing and self.playing[playerId] == 1 and item["itemName"] == 'minecraft:bow':
            self.bowShotCooldown = 20

    def OnDamage(self, data):
        playerId = data['entityId']
        attackerId = data['srcId']
        print 'ondamage data=%s' % data

        if self.status == 1 and attackerId in self.playing and playerId in self.playing and self.playing[playerId] != 1 and data['cause'] == "projectile":
            print 'detective bow shot'

            if self.playing[playerId] == 2:
                self.Elim(playerId, 5)
                self.sendMsgToAll("§l§e杀手已落网。§r§b侦探§f和平民获得胜利。")
                print 'status set to 2, line 377'
                self.status = 2
                winner = attackerId

                utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
                utilsSystem.ShowWinBanner(winner)
                ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')
                for player in self.playing:
                    if self.playing != 2:
                        self.sendTitle("§6§l胜利", 1, player)
                        self.sendTitle("恭喜您获得胜利！！！", 2, player)
                        self.sendMsg("§a+32NEKO §f获得胜利的奖励", player)
                        ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(player), 32, 'mm win')
                self.sendMsg('§a+1CREDITS §f逮捕杀手的奖励', winner)
                ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(winner), 1, 'mm mvp', True)

                def a():
                    self.status = 0
                    self.InitArena()
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
            else:
                self.Elim(attackerId, 3)
                self.Elim(playerId, 1)

    def DropBow(self, victimId):
        self.sendMsgToAll('§cdl一名侦探被击杀了！§e10秒后选出新的侦探。 §r§b上一次侦探被看见时的坐标： %s' % str(self.detectiveLastSeen))
        # serverApi.GetEngineCompFactory().CreateItem(serverApi.GetLevelId()).SpawnItemToLevel({
        #     'itemName': 'minecraft:bow',
        #     'count': 1
        # }, 0, serverApi.GetEngineCompFactory().CreatePos(victimId).GetFootPos())
        self.sendCmd('/playsound random.totem @a', victimId)

        def a():
            print 'detective redeploying'
            eligibleList = self.playing.keys()
            for player in self.playing:
                if self.playing[player] == 2:
                    eligibleList.pop(eligibleList.index(player))
                    break

            target = random.choice(eligibleList)
            self.sendTitle("§l§b侦探已任命", 1, target)
            self.sendTitle("您是新的侦探。抓住杀手！", 2, target)
            self.sendCmd('/give @s bow', target)
            self.sendCmd('/give @s arrow', target)
        commonNetgameApi.AddTimer(10.0, a)

    def Elim(self, playerId, type):
        self.sendCmd('/playsound mob.skeleton.hurt @a', playerId)
        self.sendCmd('/clear', playerId)
        self.sendCmd('/effect @s blindness 3 1 true', playerId)
        self.sendCmd('/effect @s slowness 3 255 true', playerId)
        self.sendCmd('/effect @s invisibility 3 1 true', playerId)
        if type == 1:
            self.sendTitle("§l§c您被误杀了", 1, playerId)
            self.sendTitle("您已被淘汰", 2, playerId)
        elif type == 2:
            self.sendTitle("§l§c您被杀手刺中了", 1, playerId)
            self.sendTitle("您已被淘汰", 2, playerId)
        elif type == 3:
            self.sendTitle('§c§l误杀', 1, playerId)
            self.sendTitle('您因此失去了生命', 2, playerId)
        elif type == 4:
            self.sendTitle('§c§l失调', 1, playerId)
            self.sendTitle('您放弃了比赛', 2, playerId)
        else:
            self.sendTitle('§c§l落网', 1, playerId)
            self.sendTitle('您被侦探发现了', 2, playerId)

        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        utilsSystem.SetPlayerSpectate(playerId, True)

        self.playing.pop(playerId)

    def CheckForMurderWin(self):
        if len(self.playing) == 1 and self.status == 1:
            self.sendMsgToAll("§l§e所有玩家已阵亡。§r§c杀手§f获得胜利。")
            print 'status set to 2, line 466'
            self.status = 2
            winner = self.playing.keys()[0]

            utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
            utilsSystem.ShowWinBanner(winner)
            ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')
            self.sendTitle("§6§l胜利", 1, winner)
            self.sendTitle("恭喜您获得胜利！！！", 2, winner)
            self.sendMsg("§a+32NEKO +1CREDITS §f获得胜利的奖励", winner)
            ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(winner), 32, 'mm win')
            ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(winner), 1, 'mm mvp', True)

            def a():
                self.status = 0
                self.InitArena()
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

    def BwMatchmakingCallback(self, suc, data):
        if not suc:
            print 'OnCallback timeout'
            return
        else:
            print 'bwMatchmakingCallbackCALL'
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
            self.sendMsg("§3即将为您分配新的房间，请稍等片刻", playerId)
            def a():
                transData = {'position': [1, 2, 3]}
                lobbyGameApi.TransferToOtherServerById(playerId, sid, json.dumps(transData))
            commonNetgameApi.AddTimer(1.0, a)

    def BowCDTick(self):
        if self.status == 1 and self.bowShotCooldown > 0:
            detective = self.getMatchingList(1, self.playing)
            self.bowShotCooldown -= 1
            if self.bowShotCooldown <= 0:
                self.bowShotCooldown = 0
                self.sendTitle('§l§a准备就绪', 3, detective)
                self.sendCmd('/give @s arrow', detective)
                return
            else:
                msg = "§l§6弓箭冷却\n>§b"+("⬛"*self.bowShotCooldown)+"§6<"
                self.sendTitle(msg, 3, detective)

        elif self.status != 1:
            self.bowShotCooldown = 0

    def BoardTick(self):
        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        do = utilsSystem.TextBoard
        if self.status == 0:
            for player in serverApi.GetPlayerList():
                self.sendCmd('/gamerule sendcommandfeedback false', player)
                self.sendCmd('/gamerule showdeathmessages false', player)
                do(player, True, """
§e§lICE§a_§bGAME§r§l -> §e密室§d杀手§r

§7满%s人即可开始游戏§r
§l目前人数: §e%s人
§f倒计时: §c%s秒

§r§e在ICE_GAME体验密室杀手
§7%s
""" % (c.startCountdown, len(self.waiting), self.countdown, self.epoch2Datetime(time.time())))
        elif self.status == 1:
            for player in serverApi.GetPlayerList():
                do(player, True, """
§e§lICE§a_§bGAME§r§l -> §e密室§d杀手§r
§b比赛已进行%s§r

§e§l场上还剩§b%s§e名玩家
§r§c杀手必须在 §l§d%s §r§c内淘汰所有玩家

§r§e在ICE_GAME体验密室杀手
""" % (datetime.timedelta(seconds=self.timer), len(self.playing), datetime.timedelta(seconds=(300-self.timer))))

    def tick(self):
        # per tick updates
        count = len(serverApi.GetPlayerList())
        print 'status is', self.status

        if self.status == 0:
            for player in serverApi.GetPlayerList():
                self.sendCmd('/gamemode a @s', player)

            print 'countdown=%s' % self.countdown
            enough = self.consts.enoughPlayers
            self.timer = 0
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
            if self.countdown == 8:
                self.InitArena()
            if self.countdown == 0:
                print 'starting!'
                self.start()
                self.status = 1
        elif self.status == 1:
            self.timer += 1
            self.CheckForMurderWin()

            if 3 < self.timer < 18:
                for player in self.playing:
                    self.sendTitle("§b", 1, player)
                    self.sendTitle("§l§4杀手将在%s秒后获得凶器" % (15-(self.timer-3)), 2, player)
            elif self.timer == 18:
                for player in self.playing:
                    self.sendTitle("§b", 1, player)
                    if self.playing[player] != 2:
                        self.sendTitle("§l§c杀手已获得凶器，快逃！", 2, player)

                murder = self.getMatchingList(2, self.playing)[0]
                self.sendCmd('/give @s iron_sword', murder)

            for player in serverApi.GetPlayerList():
                if 1 in self.playing.values() and player in self.playing and self.playing[player] == 2:
                    print 'checking detective fov'
                    comp = serverApi.GetEngineCompFactory().CreateGame(player)
                    if comp.CanSee(player, self.getMatchingList(3, self.playing), 1000.0, True, 180.0, 180.0):
                        print 'detective has been seen'
                        self.detectiveLastSeen = serverApi.GetEngineCompFactory().CreatePos(player).GetPos()

                if player not in self.playing or self.playing[player] != 2:
                    self.sendCmd('/effect @s weakness 1 255 true', player)
                if player not in self.playing:
                    self.sendCmd('/clear', player)

            if self.timer == 270:
                for player in serverApi.GetPlayerList():
                    self.sendTitle("§l00:30", 1, player)
                    self.sendTitle("§l§6坚持30秒即可获得胜利", 2, player)
                self.sendTitle("§l§c必须在30秒内淘汰所有玩家！", 2, self.getMatchingList(2, self.playing))

            if self.timer == 300:
                self.sendMsgToAll("§l§e杀手已落网。§r§b平民§f获得胜利。")
                print 'status set to 2, line 633'
                self.status = 2

                ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')
                for player in self.playing:
                    if self.playing == 3:
                        self.sendTitle("§6§l胜利", 1, player)
                        self.sendTitle("恭喜您获得胜利！！！", 2, player)
                        self.sendMsg("§a+32NEKO §f获得胜利的奖励", player)
                        ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(player), 32, 'mm win')
                self.sendMsg('§c+0NEKO §f时间结束前未能逮捕杀手', self.getMatchingList(1, self.playing))

                def a():
                    self.status = 0
                    self.InitArena()
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

        elif self.status == 2:
            for player in serverApi.GetPlayerList():
                self.sendCmd('/gamemode a @s', player)

        self.updateServerStatus(self.status)

        self.sendCmd('/effect @a saturation 5 255 true', serverApi.GetPlayerList()[0])

    def start(self):
        self.timer = 0
        for player in self.waiting:
            self.playing[player] = 3
            self.setPos(player, random.choice(c.startPos))

        self.waiting = []
        availableList = self.playing.keys()
        mSetDetectiveBuffer = random.choice(availableList)
        self.playing[mSetDetectiveBuffer] = 1
        availableList.pop(availableList.index(mSetDetectiveBuffer))
        self.playing[random.choice(availableList)] = 2

        for player in self.playing:
            role = self.playing[player]

            utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
            utilsSystem.SetHideName(player, True)

            comp = serverApi.GetEngineCompFactory().CreateGame(player)
            comp.SetDisableDropItem(True)
            if role == 1:
                self.sendTitle("§b§l侦探", 1, player)
                self.sendTitle("找出杀手，并使用弓箭将其击毙", 2, player)
                self.sendCmd('/give @s bow', player)
                self.sendCmd('/give @s arrow', player)
            elif role == 2:
                self.sendTitle("§c§l杀手", 1, player)
                self.sendTitle("杀死所有人，获得胜利", 2, player)
            else:
                self.sendTitle("§l平民", 1, player)
                self.sendTitle("收集金条购买弓箭，小心杀手！", 2, player)

            self.sendCmd('/playsound block.bell.hit', player)

