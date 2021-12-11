# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import datetime
import apolloCommon.commonNetgameApi as commonNetgameApi
import math
import megaScript.megaConsts as c
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.mysqlPool as mysqlPool
cooldown = {}

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

# 在modMain中注册的Server System类
class megaSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        self.status = 0
        self.countdown = 180

        self.gracePeriod = True

        self.friendlyFires = {}

        self.consts = c
        lobbyGameApi.ShieldPlayerJoinText(True)

        self.teams = {}

        self.waiting = []
        self.timer = 0

        self.kills = {}

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
            commonNetgameApi.AddTimer(1.4, lambda p: self.sendTitle('战墙将在15分钟后倒塌', 2, p), player)

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

    def updateServerStatus(self, status):
        args = {
            'sid': lobbyGameApi.GetServerId(),
            'value': status,
            'count': len(serverApi.GetPlayerList())
        }
        serverId = lobbyGameApi.GetServerId()
        print 'init recordsid'
        self.RequestToServiceMod("service_bw", "RecordSidEvent", args)

    def getCountInList(self, key, li):
        count = 0
        for item in li:
            if key == li[item]:
                count += 1
        return count

    def WallsCollapse(self):
        for player in self.teams:
            self.sendTitle('§l§c墙塌了', 1, player)
            self.sendTitle('进入战场吧！', 2, player)

        self.gracePeriod = False

    def rank(self, d):
        mComp = 0
        for item in d:
            if (not mComp in d or d[item] > d[mComp]) and item in self.teams:
                mComp = item
        return mComp

    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self, self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self, self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerDieEvent", self, self.OnPlayerDie)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerPlayerTryDestroyBlockEvent", self, self.OnServerPlayerTryDestroyBlock)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerEntityTryPlaceBlockEvent", self, self.OnServerEntityTryPlaceBlock)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerRespawnFinishServerEvent", self, self.OnPlayerRespawnFinishServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerChatEvent", self, self.OnServerChat)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerAttackEntityEvent", self, self.OnPlayerAttackEntity)

        commonNetgameApi.AddTimer(1.0, self.tick)
        commonNetgameApi.AddTimer(1.0, self.boardTick)

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

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        uid = data['uid']
        if playerId in self.waiting:
            self.waiting.pop(self.waiting.index(playerId))
        if playerId in self.teams:
            self.teams.pop(playerId)

    def OnPlayerDie(self, data):
        playerId = data['id']
        attackerId = data['attacker']

        if self.gracePeriod or self.status != 1:
            return

        self.teams.pop(playerId)
        print 'onkill %s->%s' % (attackerId, playerId)
        if playerId in self.teams:
            print c.teamNames[self.teams[playerId]]
            playerNick = c.teamNames[self.teams[playerId]] + '§r§3' + lobbyGameApi.GetPlayerNickname(playerId) + "§7"
            if lobbyGameApi.GetPlayerNickname(attackerId):
                attackerNick = c.teamNames[self.teams[attackerId]] + '§r§3' + lobbyGameApi.GetPlayerNickname(
                    attackerId) + "§3"
            else:
                attackerNick = '§l§4神秘力量§r§7'

            print 'valid kill'

            if attackerId != '-1':
                self.sendMsgToAll("%s§7杀死了%s" % (attackerNick, playerNick))
                print 'kill'
                self.kills[attackerId] += 1

                self.sendCmd('/playsound note.harp', attackerId)

            else:
                self.sendMsgToAll("%s杀死了%s" % (attackerNick, playerNick))
                print 'kill'

    def OnPlayerRespawnFinishServer(self, data):
        playerId = data['playerId']
        self.sendTitle('§c§l您已被淘汰', 1, playerId)
        self.sendTitle('别气馁，您的队伍还有机会', 2, playerId)
        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        utilsSystem.SetPlayerSpectate(playerId, True)

    def OnServerPlayerTryDestroyBlock(self, data):
        x = data['x']
        y = data['y']
        z = data['z']
        wallWidth = c.width

        if self.gracePeriod and (abs(x) <= wallWidth or abs(y) <= wallWidth):
            data['cancel'] = True

    def OnServerEntityTryPlaceBlock(self, data):
        x = data['x']
        y = data['y']
        z = data['z']
        height = c.buildHeight

        if self.gracePeriod and y > height:
            data['cancel'] = True

    def OnPlayerAttackEntity(self, data):
        playerId = data['playerId']
        victimId = data['victimid']

        if not(playerId in self.teams and victimId in self.teams):
            data['cancel'] = True
            return
        if self.gracePeriod:
            data['cancel'] = True
            return

        if not self.gracePeriod and self.teams[playerId] == self.teams[victimId]:
            self.sendTitle('§c', 1, playerId)
            self.sendTitle('§c不要攻击您的队友！', 2, playerId)
            data['damage'] = math.floor(data['damage']/2)
            self.friendlyFires[playerId] += 1
            self.sendTitle('§c§l警告\n§f再攻击%s次队友将导致你被踢出' % (3-self.friendlyFires[playerId],), 3, playerId)

            if self.friendlyFires[playerId] >= 3:
                lobbyGameApi.TryToKickoutPlayer(playerId, '§l§f您攻击队友的次数太多了\n\n§r§e多次恶意攻击队友将导致惩罚！')

    def OnServerChat(self, data):
        playerId = data['playerId']
        nickname = data['username']
        msg = data['message']

        data['cancel'] = True

        if not commonNetgameApi.CheckWordsValid(msg):
            self.sendMsg('§3不允许发送该消息，请检查', playerId)
            return

        replaceSystem = serverApi.GetSystem('replaceWords', 'replaceWordsSystem')
        if playerId in replaceSystem.db:
            db = replaceSystem.db[playerId]
        else:
            db = None

        if self.status == 0:
            msg = db[0] + db[1] + "§r§3" + nickname + ": §7" + db[2] + msg
            self.sendMsgToAll(msg)
        elif self.status >= 1:
            if playerId in self.teams:
                isShout = bool(msg[0] == '!' or msg[0] == '！')
                teamName = c.teamNames[self.teams[playerId]]

                if isShout:
                    if self.gracePeriod:
                        self.sendMsg('§c暂时不可以发送全体消息', playerId)
                        return
                    else:
                        msg = db[0] + db[1] + "§r§b[全体]%s§r§3" % teamName + nickname + ": §7" + db[2] + msg
                        self.sendMsgToAll(msg)
                else:
                    msg = db[0] + db[1] + "§r§b[队伍]§3" + nickname + ": §7" + db[2] + msg
                    for player in self.teams:
                        if self.teams[player] == self.teams[playerId]:
                            self.sendMsg(msg, player)
            else:
                msg = "[观战]§3" + nickname + ": §7" + msg
                self.sendMsgToAll(msg)

    # main ticking logic
    def tick(self):
        count = len(serverApi.GetPlayerList())

        if self.status == 0:
            print 'countdown=%s' % self.countdown
            self.timer = 0
            self.scoreboard(1, 6, "§c%s§f秒" % self.countdown)
            if count < c.startCountdown:
                pass
            elif c.startCountdown <= count <= 40:
                self.countdown -= 1
                for player in serverApi.GetPlayerList():
                    self.sendTitle("§e§l%s" % self.countdown, 1, player)
                    self.sendTitle("游戏即将开始", 2, player)
            if count == 40 and self.countdown > 15:
                self.countdown = 15
            if self.countdown < 180 and count < c.startCountdown:
                self.sendMsgToAll("§c§l人数不够，倒计时取消！")
                self.countdown = 180
            if self.countdown == 0:
                print 'starting!'
                self.start()
                self.status = 1

        elif self.status == 1:
            self.timer += 1

            if self.timer and self.timer % 60 == 0 and self.timer < 900:
                for player in self.teams:
                    self.sendTitle('§6§l%s分钟' % ((900-self.timer)/60,), 1, player)
                    self.sendTitle('战墙倒塌倒计时', 2, player)
            elif 900 > self.timer >= 885:
                for player in self.teams:
                    self.sendTitle('§c§l%s秒' % (900-self.timer,), 1, player)
                    self.sendTitle('战墙即将倒塌，做好准备', 2, player)

            if self.timer == 900:
                self.WallsCollapse()

        mTeamBuffer = None
        for player in self.teams:
            if mTeamBuffer != self.teams[player] and mTeamBuffer:
                mIsWin = False
                break
            else:
                mIsWin = True
            mTeamBuffer = self.teams[player]
        if mIsWin:
            self.win(mTeamBuffer)

    def win(self, team):
        teamName = c.teamNames[team]
        self.status = 2

        for player in self.teams:
            if self.teams[player] == team:
                self.sendTitle("§6§l胜利", 1, player)
                self.sendTitle("恭喜您获得胜利！！！", 2, player)
                self.sendMsg("§a+128NEKO +16CREDITS §f获得胜利的奖励", player)

                ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')
                ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(player), 128, 'bw win')
                ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(player), 16, 'bw win', True)

        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        utilsSystem.ShowWinBanner(self.rank(self.kills))

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


    def start(self):
        mTeamAssign = 1
        self.timer = 0
        self.kills = {}
        self.friendlyFires = {}
        self.gracePeriod = True
        comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
        for player in self.waiting:
            self.kills[player] = 0
            self.teams[player] = mTeamAssign
            self.friendlyFires[player] = 0

            self.sendCmd('/gamemode s', player)
            self.sendMsg("您的队伍是：%s" % c.teamNames[mTeamAssign], player)
            self.sendMsg("分配队伍中，可能稍有卡顿，请不要退出！！！。我们将在未来修复该问题。", player)
            mTeamAssign += 1
            if mTeamAssign > c.teamsCount:
                mTeamAssign = 1
            self.balance[player] = 0

            def a(p):
                comp = serverApi.GetEngineCompFactory().CreateName(p)
                comp.SetPlayerPrefixAndSuffixName(c.teamPrefix[self.teams[p]], serverApi.GenerateColor('RED'), '',
                                                  serverApi.GenerateColor('RED'))
            commonNetgameApi.AddTimer(6.0, a, player)

        self.waiting = []
        for player in self.teams:
            teamPos = c.pos[self.teams[player]]
            self.setPos(player, teamPos)
            self.sendCmd('/spawpoint @s %s %s %s' % (teamPos[0], teamPos[1], teamPos[2]), player)

        self.playStartAnimation()

    def boardTick(self):
        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        do = utilsSystem.TextBoard
        if self.status == 0:
            for player in serverApi.GetPlayerList():
                self.sendCmd('/gamerule sendcommandfeedback false', player)
                self.sendCmd('/gamerule showdeathmessages false', player)
                do(player, True, """
§e§lICE§a_§bGAME§r§l -> §6超级§a战墙§r

§7满%s人即可开始游戏§r
§l目前人数: §e%s人
§f倒计时: §c%s秒

§r§e在ICE_GAME体验超级战墙【无凋零版】
§7%s
""" % (c.startCountdown, len(self.waiting), self.countdown, self.epoch2Datetime(time.time())))
        elif self.status == 1:
            if self.gracePeriod:
                for player in self.teams:
                    do(player, True, """
§e§lICE§a_§bGAME§r§l -> §6超级§a战墙§r
§b比赛已进行%s

§r§f您的队伍： %s
§r§f距离战墙倒塌： §6%s

§r§e在ICE_GAME体验超级战墙【无凋零版】
""" % (datetime.timedelta(seconds=self.timer), c.teamNames[self.teams[player]], datetime.timedelta(seconds=(900-self.timer))))
            else:
                for player in self.teams:

                    params = '§c'+str(self.getCountInList(1, self.teams))+' §e'+str(self.getCountInList(2, self.teams))+' §b'+str(self.getCountInList(3, self.teams))+' §a'+str(self.getCountInList(24, self.teams))

                    do(player, True, """
§e§lICE§a_§bGAME§r§l -> §6超级§a战墙§r
§b比赛已进行%s

§r§f您的队伍： %s
§r%s

§r§e在ICE_GAME体验超级战墙【无凋零版】
""" % (datetime.timedelta(seconds=self.timer), c.teamNames[self.teams[player]], params))

