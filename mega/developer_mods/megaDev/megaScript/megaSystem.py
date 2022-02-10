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

        self.consts = c
        lobbyGameApi.ShieldPlayerJoinText(True)

        self.teams = {}

        self.waiting = []
        self.timer = 0

        self.kills = {}
        self.rff = {}

        self.containerStatus = {}
        self.legacyContainerStatus = {}
        self.containerProgress = {}

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
            self.sendTitle('占领所有敌方目标点', 2, player)

        for tup in c.wallPos:
            self.sendCmd('/fill %s %s %s %s %s %s air' % (tup[0][0], tup[0][1], tup[0][2], tup[1][0], tup[1][1], tup[1][2]), serverApi.GetPlayerList()[0])

        self.gracePeriod = False

    def rank(self, d):
        mComp = 0
        for item in d:
            if (not mComp in d or d[item] > d[mComp]) and item in self.teams:
                mComp = item
        return mComp

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

    def epoch2Datetime(self, epoch):
        ts = datetime.datetime.fromtimestamp(int(epoch)+0)
        return ts.strftime('%Y-%m-%d %H:%M:%S')

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
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnScriptTickServer", self, self.OnScriptTickServer)

        commonNetgameApi.AddRepeatedTimer(1.0, self.tick)
        commonNetgameApi.AddRepeatedTimer(1.0, self.boardTick)
        commonNetgameApi.AddRepeatedTimer(1.0, self.containerTick)

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

        for player in self.teams:
            if self.teams[player] == self.teams[playerId]:
                comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
                pos = comp.GetPos()
                self.sendMsg('§l§e死亡坐标: %s %s %s' % (int(pos[0]), int(pos[1]), int(pos[2])))

        if self.containerStatus[self.teams[playerId]] == 3:
            self.teams.pop(playerId)
            for player in serverApi.GetPlayerList():
                self.sendMsg('§l§6最终击杀:', player)
            for player in self.teams:
                self.sendTitle('§l%s VS %s' % (self.getCountInList(self.teams[player], self.teams), len(self.teams) - self.getCountInList(self.teams[player], self.teams)))

        # self.teams.pop(playerId)
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

            if not self.rff[playerId] and playerId != attackerId and self.teams[playerId] == self.teams[attackerId]:
                self.sendMsgToAll('§l%s的反向友伤已开启' % lobbyGameApi.GetPlayerNickname(attackerId))
                def a():
                    self.sendTitle('§l§4反向友伤已开启', 1, attackerId)
                    self.sendTitle('您对队友造成的伤害将被反弹', 2, attackerId)
                commonNetgameApi.AddTimer(1.0, a)
                self.rff[attackerId] = True

    def OnPlayerRespawnFinishServer(self, data):
        playerId = data['playerId']

        if playerId in self.teams:
            self.sendTitle('§6§l将在5秒后重生', 1, playerId)
            self.sendCmd('/effect @s blindness 5 1 true', playerId)
            self.NotifyToClient(playerId, 'StartNoMoveEvent', 5.0)
            self.setPos(playerId, c.pos[self.teams[playerId]])

        elif self.getCountInList(self.teams[playerId], self.teams) > 0:
            self.sendTitle('§c§l您已被淘汰', 1, playerId)
            self.sendTitle('别气馁，您的队伍还有机会', 2, playerId)
            utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
            utilsSystem.SetPlayerSpectate(playerId, True)
            self.setPos(playerId, c.spectatorPos)

        elif self.getCountInList(self.teams[playerId], self.teams) == 0:
            for player in self.teams:
                if self.teams[player] == self.teams[playerId]:
                    self.sendTitle('§4§l小队全灭', 1, playerId)
                    self.sendTitle('下次再接再厉!', 2, playerId)
            utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
            utilsSystem.SetPlayerSpectate(playerId, True)

            self.setPos(playerId, c.spectatorPos)

    def OnServerPlayerTryDestroyBlock(self, data):
        x = data['x']
        y = data['y']
        z = data['z']
        wallWidth = c.width

        if self.gracePeriod and (abs(x) <= wallWidth or abs(y) <= wallWidth):
            data['cancel'] = True

        nearContainer = False
        li = c.containerPos
        for key in li:
            pos = li[key]
            if abs(pos[0] - x) < 7 or abs(pos[1] - y) < 7 or abs(pos[2] - z) < 7:
                nearContainer = True
        if nearContainer:
            return

    def OnServerEntityTryPlaceBlock(self, data):
        x = data['x']
        y = data['y']
        z = data['z']
        height = c.buildHeight

        if self.gracePeriod and y > height:
            data['cancel'] = True

        if y > c.maxBuildHeight:
            data['cancel'] = True

        nearContainer = False
        li = c.containerPos
        for key in li:
            pos = li[key]
            if abs(pos[0]-x) < 7 or abs(pos[1]-y) < 7 or abs(pos[2]-z) < 7:
                nearContainer = True
        if nearContainer:
            return

    def OnPlayerAttackEntity(self, data):
        playerId = data['playerId']
        victimId = data['victimid']

        if not(playerId in self.teams and victimId in self.teams):
            data['cancel'] = True
            return
        if self.gracePeriod:
            data['cancel'] = True
            return

        if self.teams[playerId] == self.teams[victimId]:
            if not self.rff[playerId]:
                self.sendTitle('§c', 1, playerId)
                self.sendTitle('§c不要攻击您的队友！', 2, playerId)
            else:
                data['cancel'] = True
                comp = serverApi.GetEngineCompFactory().CreateHurt(playerId)
                comp.Hurt(8, serverApi.GetMinecraftEnum().ActorDamageCause.EntityAttack, playerId, None, False)

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

    def OnScriptTickServer(self):
        if self.status == 0:
            for player in serverApi.GetPlayerList():
                comp = serverApi.GetEngineCompFactory().CreatePos(player)
                pos = comp.GetPos()

                if pos[1] < c.lobbyHeightLimit:
                    self.setPos(player, c.lobbyPos)

        elif self.status == 1:
            if self.timer < c.prepPhaseDuration:
                for player in serverApi.GetPlayerList():
                    comp = serverApi.GetEngineCompFactory().CreatePos(player)
                    pos = comp.GetPos()

                    if pos[1] > c.buildHeight:
                        self.sendCmd('/tp @s ~ ~-1 ~', player)

    def containerTick(self):
        if self.status == 1:

            for key in c.containerPos:
                if self.containerStatus[key] == 3:
                    continue

                containerDefended = False
                teamsInContainer = []
                enemiesInContainer = 0

                containerPos = c.containerPos[key]

                for player in self.teams:
                    comp = serverApi.GetEngineCompFactory().CreatePos(player)
                    pos = comp.GetPos()
                    dist = self.dist(pos[0], pos[1], pos[2], containerPos[0], containerPos[1], containerPos[2])

                    if key == self.teams[player]:
                        containerDefended = True
                        break

                    if key not in teamsInContainer:
                        teamsInContainer.append(key)

                    if dist <= 5:
                        enemiesInContainer += 1

                # conclusion
                if (enemiesInContainer and containerDefended) or len(teamsInContainer) > 1:
                    self.containerStatus[key] = 2

                    if self.containerStatus[key] != self.legacyContainerStatus[key]:
                        for player in self.teams:
                            if self.teams[player] == key:
                                self.sendTitle('§l§e你的目标点正在被争夺', 1, player)
                                self.sendTitle('返回基地保护目标点！', 2, player)
                            elif self.teams[player] in teamsInContainer:
                                self.sendTitle('§l§e目标点正在被争夺', 1, player)
                                self.sendTitle('消灭目标点内的其他玩家', 2, player)

                elif enemiesInContainer and not containerDefended:
                    self.containerStatus[key] = 1
                    self.containerProgress[key] += 3 + enemiesInContainer

                    if self.containerStatus[key] != self.legacyContainerStatus[key]:
                        for player in self.teams:
                            if self.teams[player] == key:
                                self.sendTitle('§l§c你的目标点正在被占领', 1, player)
                                self.sendTitle('立刻返回基地保护目标点！', 2, player)
                            elif self.teams[player] in teamsInContainer:
                                self.sendTitle('§l§a开始占领目标点', 1, player)
                                self.sendTitle('消灭所有尝试干涉的玩家！', 2, player)

                else:
                    self.containerStatus[key] = 0
                    if self.containerProgress[key] != 0:
                        self.containerProgress[key] = 0

                    if self.containerStatus[key] != self.legacyContainerStatus[key]:
                        for player in self.teams:
                            if self.teams[player] == key:
                                self.sendTitle('§l§a目标点争夺已停止', 1, player)
                                self.sendTitle('防止敌人再次开始争夺！', 2, player)
                            elif self.teams[player] in teamsInContainer:
                                self.sendTitle('§l§c目标点争夺已停止', 1, player)

                if self.containerProgress[key] >= 100:
                    self.capturedContainer(key, teamsInContainer[0])

            for player in self.teams:
                response = {
                    'status': self.containerStatus[self.teams[player]],
                    'progress': self.containerProgress[self.teams[player]]
                }
                self.NotifyToClient(player, 'UpdateContainerStatusEvent', response)

                if self.containerStatus[self.teams[player]] == 1:
                    prog = int(round(self.containerProgress[self.teams[player]])) % 10
                    extras = "§l§c" + ("⏺" * prog) + '§7' + ("⏺" * (10 - prog))
                    self.sendTitle('§l§c目标点被占领§r %s §c- %s' % (extras, self.containerProgress[self.teams[player]]) + '%')

                elif self.containerStatus[self.teams[player]] == 2:
                    prog = int(round(self.containerProgress[self.teams[player]])) % 10
                    extras = "§l§c" + ("⏺" * prog) + '§7' + ("⏺" * (10 - prog))
                    self.sendTitle('§l§e目标点正在争夺§r %s §e- %s' % (extras, self.containerProgress[self.teams[player]]) + '%')

            self.legacyContainerStatus = self.containerStatus

    def capturedContainer(self, containerId, capturingTeam):
        self.containerStatus[containerId] = 3
        self.sendCmd('/setblock %s %s %s stained_glass 15' % (c.containerPos[0], c.containerPos[1]-1, c.containerPos[2]), serverApi.GetPlayerList()[0])

        for player in self.teams:
            if self.teams[player] == containerId:
                self.sendTitle("§c§l目标点已被敌方占领", 1, player)
                self.sendTitle("您将不再重生", 2, player)

            self.sendMsg('%s§r§7的目标点被%s§r§7占领了！' % (c.teamNames[containerId], c.teamNames[capturingTeam]), player)

    # main ticking logic
    def tick(self):
        count = len(serverApi.GetPlayerList())

        if self.status == 0:
            print 'countdown=%s' % self.countdown
            self.timer = 0
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

            if self.timer and self.timer % 60 == 0 and self.timer < c.prepPhaseDuration:
                for player in self.teams:
                    self.sendTitle('§6§l%s分钟' % ((c.prepPhaseDuration-self.timer)/60,), 1, player)
                    self.sendTitle('战墙倒塌倒计时', 2, player)
            elif c.prepPhaseDuration > self.timer >= c.prepPhaseDuration - 15:
                for player in self.teams:
                    self.sendTitle('§c§l%s秒' % (c.prepPhaseDuration-self.timer,), 1, player)
                    self.sendTitle('战墙即将倒塌，做好准备', 2, player)

            if self.timer == c.prepPhaseDuration:
                self.WallsCollapse()

            # self.sendCmd('/effect @a saturation 1 255 true', serverApi.GetPlayerList()[0])

            mTeamBuffer = None
            for player in self.teams:
                if mTeamBuffer != self.teams[player] and mTeamBuffer:
                    mIsWin = False
                    break
                else:
                    mIsWin = True
                mTeamBuffer = self.teams[player]
            if mIsWin and self.teams:
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
            self.rff[player] = False
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
        self.sendCmd('/time set day', serverApi.GetPlayerList()[0])

        for i in range(c.teamsCount):
            self.containerProgress[i+1] = 0
            self.containerStatus[i+1] = 0
            self.legacyContainerStatus = self.containerStatus

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

§r§e在ICE_GAME体验超级战墙【占领目标点】
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
§r§l§e利用这段时间搜集资源，准备迎战！

§r§e在ICE_GAME体验超级战墙【占领目标点】
""" % (datetime.timedelta(seconds=self.timer), c.teamNames[self.teams[player]], datetime.timedelta(seconds=(c.prepPhaseDuration-self.timer))))
            else:
                for player in self.teams:
                    extra = ""
                    for key in self.containerStatus:
                        status = self.containerStatus[key]
                        if status == 0:
                            extra += "%s: §l§a安全§r\n" % (c.teamNames[key])
                        elif status == 1:
                            extra += "%s: §l§c占领中 - §f%s" % (c.teamNames[key], self.containerProgress[key]) + "%§r\n"
                        elif status == 2:
                            extra += "%s: §l§e争夺中§n\n" % (c.teamNames[key])
                        elif status == 3:
                            extra += "%s: §l§6%s LEFT§r\n" % (c.teamNames[key], self.getCountInList(key, self.teams))

                    do(player, True, """
§e§lICE§a_§bGAME§r§l -> §6超级§a战墙§r
§b比赛已进行%s

§r§f您的队伍： %s
§r%s

§r§e在ICE_GAME体验超级战墙【占领目标点】
""" % (datetime.timedelta(seconds=self.timer), c.teamNames[self.teams[player]], extra))

