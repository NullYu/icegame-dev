# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import math
import random
import datetime
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
class bwServerSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()
        self.consts = None
        lobbyGameApi.ShieldPlayerJoinText(True)

        self.beds = {}
        self.teams = {}

        # 1 2 3 4 Red Yellow Blue Green

        self.waiting = []
        self.status = 0

        self.blocks = {}

        self.balance = {}

        self.resTimer = 0
        self.countdown = 180
        self.timer = 0

        self.kills = {}

        self.armors = {}
        self.armorsTime = {}

        # ##Consts import
        type = commonNetgameApi.GetServerType()

        # bw4v4, bwBomb4v4
        if type in ['game_bw', 'game_bwBomb']:
            import bwScript.bw4Consts1 as c
            self.consts = c
        elif type in ['game_8bw1', 'game_8bw1Bomb']:
            import bwScript.bw8Consts1 as c
            self.consts = c
        elif type in ['game_2bw8', 'game_2bw8Bomb']:
            import bwScript.bw2Consts1 as c
            self.consts = c
        elif type in ['game_bwT3', 'game_bwBombT3']:
            import bwScript.bw4Consts3 as c
            self.consts = c

        global c
        print 'self.consts = ', self.consts

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
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnScriptTickServer", self, self.OnScriptTickServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerDieEvent", self, self.OnPlayerDie)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self, self.OnCommand)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DamageEvent", self, self.OnDamage)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerBlockUseEvent", self, self.OnServerBlockUse)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ExplosionServerEvent", self, self.OnExplosionServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerAttackEntityEvent", self, self.OnPlayerAttackEntity)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ActorAcquiredItemServerEvent", self, self.OnActorAcquiredItemServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerChatEvent", self, self.OnServerChat)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerRespawnFinishServerEvent", self, self.OnPlayerRespawnFinishServer)
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
        comp.SetGameDifficulty(2)
        lobbyGameApi.ShieldPlayerJoinText(True)
        commonNetgameApi.AddRepeatedTimer(1.0, self.tick)
        commonNetgameApi.AddRepeatedTimer(1.0, self.ResTick)
        commonNetgameApi.AddRepeatedTimer(1.0, self.ArmorTick)
        commonNetgameApi.AddRepeatedTimer(1.0, self.BoardTick)

        comp = serverApi.GetEngineCompFactory().CreateBlockUseEventWhiteList(serverApi.GetLevelId())
        for i in range(16):
            comp.AddBlockItemListenForUseEvent("minecraft:bed:%s" % i)

        def a():
            npcSystem = serverApi.GetSystem("neteaseNpc", "npcServer")
            identifier = "minecraft:npc"
            name = "§e§l物品商店"
            rot = (0, 180)
            for pos in c.shopPos['items']:
                npcSystem.RegisterExtraNpc(identifier, name, 0, pos, rot, self.NpcHit)
        commonNetgameApi.AddTimer(5.0, a)

        def b():
            args = {
                'sid': lobbyGameApi.GetServerId(),
                'value': 0
            }
            serverId = lobbyGameApi.GetServerId()
            print 'init recordsid'
            self.RequestToServiceMod("service_bw", "RecordSidEvent", args)
        commonNetgameApi.AddTimer(8.0, b)

    def OnCommand(self, data):
        playerId = data['entityId']
        cmd = data['command']

        if cmd == "/again":
            data['cancel'] = True
            if self.status == 1:
                if playerId not in self.teams:
                    self.sendMsg('§c您必须先完成本场游戏。', playerId)
            else:
                self.RequestToServiceMod("bw", "RequestMatchmakingEvent", {
                    'playerId': playerId,
                    'mode': commonNetgameApi.GetServerType()
                }, self.BwMatchmakingCallback, 2)
        else:
            self.sendMsg('§e当前不可再来一局。', playerId)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("gameutils", "gameutilsClient", 'TestRequest', self, self.OnTestRequest)

    def OnDamage(self, data):
        playerId = data['entityId']
        if playerId not in serverApi.GetPlayerList():
            return

        srcId = data['srcId']

        if data['cause'] in ['block_explosion', 'entity_explosion']:

            if 'Bomb' in commonNetgameApi.GetServerType():
                print 'tnt cancel damage'
                data['damage'] = 0
            vpos = serverApi.GetEngineCompFactory().CreatePos(srcId).GetPos()
            spos = serverApi.GetEngineCompFactory().CreatePos(playerId).GetPos()
            data['knock'] = False

            comp = serverApi.GetEngineCompFactory().CreateAction(playerId)
            comp.SetMobKnockback(spos[0] - vpos[0], spos[2] - vpos[2], 7.5, 3.0, 4.0)
        elif data['cause'] == 'fall' and 'Bomb' in commonNetgameApi.GetServerType():
            data['damage'] = 0

    def OnScriptTickServer(self):
        for player in self.teams:
            comp = serverApi.GetEngineCompFactory().CreatePos(player)
            playerPos = comp.GetFootPos()

            if self.status == 0 and playerPos[1] < 235:
                print 'over the edge'
                self.setPos(player, c.lobbyPos)

            if self.status == 1 and playerPos in c.levitationPos and commonNetgameApi.GetServerType().replace('Bomb', '') == 'game_bwT3':
                self.sendCmd('/effect @s levitation 5 12')

            if playerPos[1] < 10:
                comp = serverApi.GetEngineCompFactory().CreateHurt(player)
                comp.Hurt(9999, serverApi.GetMinecraftEnum().ActorDamageCause.EntityAttack, None, None, False)

            self.sendCmd('/clear @s bed', player)

        for player in serverApi.GetPlayerList():
            if self.status == 1 and player not in self.teams:
                self.sendCmd('/clear @s', player)

    def OnServerBlockUse(self, data):
        print 'blockuse data=%s' % data
        playerId = data['playerId']
        name = data['blockName']

        if name == 'minecraft:bed':
            data['cancel'] = True
            return

    def OnServerPlayerTryDestroyBlock(self, data):
        playerId = data['playerId']
        x = data['x']
        y = data['y']
        z = data['z']
        name = data['fullName']

        if self.status != 1:
            data['cancel'] = True
            print 'break outside game'
            return

        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        if utilsSystem and playerId in utilsSystem.spectating:
            data['cancel'] = True
            print 'spectator broke block'

        # TODO Destroy Cake
        if name == 'minecraft:bed':
            print 'broke bed data=%s' % data
            self.DestroyCake(playerId, (x, y, z))
            return
        elif not self.getIfLegalBreak((x, y, z)) or playerId not in self.blocks:
            data['cancel'] = True
            self.sendMsg('§c不能毁坏这个方块噢', playerId)
            data['spawnResources'] = False

            comp = serverApi.GetEngineCompFactory().CreateBlockInfo(playerId)
            blockDict = {
                'name': name,
                'aux': data['auxData']
            }
            comp.SetBlockNew((x, y, z), blockDict)
        else:
            self.blocks[playerId].pop(self.blocks[playerId].index((x, y, z)))

    def OnExplosionServer(self, data):
        blocks = data['blocks']
        for li in blocks:
            mIsLegal = False
            for key in self.blocks:
                if (li[0], li[1], li[2]) in self.blocks[key]:
                    mIsLegal = True
            if not mIsLegal or 'Bomb' in commonNetgameApi.GetServerType():
                li[3] = True

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
            msg = db[0]+db[1]+"§r§3"+nickname+": §7"+db[2]+msg
            self.sendMsgToAll(msg)
        elif self.status >= 1:
            if playerId in self.teams:
                isShout = bool(msg[0] == '!' or msg[0] == '！')
                teamName = c.teamNames[self.teams[playerId]]

                if isShout:
                    msg = db[0]+db[1]+"§r§b[全体]%s§r§3" % teamName+nickname+": §7"+db[2]+msg
                    self.sendMsgToAll(msg)
                else:
                    msg = db[0]+db[1]+"§r§b[队伍]§3"+nickname+": §7"+db[2]+msg
                    for player in self.teams:
                        if self.teams[player] == self.teams[playerId]:
                            self.sendMsg(msg, player)
            else:
                msg = "[观战]§3"+nickname+": §7"+msg
                self.sendMsgToAll(msg)

    def DestroyCake(self, playerId, pos):
        print 'bed break pos='+str(pos)

        for key in c.bedPos:
            if c.bedPos[key] == pos or c.bedPosD[key] == pos:
                bedPos = c.bedPos[key]
                team = key
                break

        if not (bedPos and team):
            self.sendMsg("Invalid bed break!!! Report to admin!!!", playerId)
            return

        teamName = c.teamNames[team]
        rivalTeam = self.teams[playerId]

        p = bedPos

        if team == rivalTeam:
            self.sendMsg('§c您不能摧毁您自己的床', playerId)
            print '/setblock %s %s %s bed %s' % (p[0], p[1], p[2], c.bedHeading[team])
            commonNetgameApi.AddTimer(0.01, lambda a: self.sendCmd('/kill @e[type=item, x=%s, y=67, z=%s, r=3]' % (p[0], p[2]), playerId), p)
            def a():
                self.sendCmd('/setblock %s %s %s bed %s' % (p[0], p[1], p[2], c.bedHeading[team]), playerId)
            commonNetgameApi.AddTimer(0.1, a)
            return

        self.sendMsgToAll("§l床被摧毁！§r§7{0}§r 的床被 §3{1} §r§f无情地破坏了！".format(teamName, c.teamNames[rivalTeam]))
        for player in self.teams:
            if self.teams[player] == team:
                self.sendTitle("§c§l床炸了！", 1, player)
                self.sendTitle("您将不能重生", 2, player)
                self.sendCmd('/playsound mob.wither.death', player)
            else:
                self.sendCmd('/playsound mob.enderdragon.growl', playerId)
        self.beds[team] = False

    def OnPlayerAttackEntity(self, data):
        playerId = data['playerId']
        victimId = data['victimId']

        if self.status != 1:
            data['cancel'] = True
            return
        if self.teams[playerId] == self.teams[victimId]:
            data['cancel'] = True
            self.sendTitle('§c', 1, playerId)
            self.sendTitle('§c不要攻击您的队友！', 2, playerId)
            return

    def TeamWipeout(self, team):
        teamName = c.teamNames[team]
        self.sendMsgToAll('§l团灭！§r§7%s 的全部成员已被淘汰' % teamName)

    def OnPlayerDie(self, data):
        playerId = data['id']
        attackerId = data['attacker']
        print 'onkill %s->%s' % (attackerId, playerId)
        if playerId in self.teams:
            print c.teamNames[self.teams[playerId]]
            playerNick = c.teamNames[self.teams[playerId]] + '§r§3' + lobbyGameApi.GetPlayerNickname(playerId) + "§7"
            if lobbyGameApi.GetPlayerNickname(attackerId):
                attackerNick = c.teamNames[self.teams[attackerId]] + '§r§3' + lobbyGameApi.GetPlayerNickname(attackerId) + "§3"
            else:
                attackerNick = '§l§4神秘力量§r§7'

            print 'valid kill'

            if playerId in self.armors and self.armors[playerId]:
                self.armors[playerId] = 0
            if attackerId in self.armors and self.armors[attackerId]:
                self.armors[attackerId] = self.armorsTime[attackerId]

            if attackerId != '-1':
                if self.beds[self.teams[playerId]]:
                    self.sendMsgToAll("%s§7杀死了%s" % (attackerNick, playerNick))
                    print 'kill'
                else:
                    self.sendMsgToAll("%s杀死了%s。 §6§l最终击杀！" % (attackerNick, playerNick))
                    self.teams.pop(playerId)
                    print 'final kill'
                self.kills[attackerId] += 1

                reward = self.balance[playerId]+250
                self.balance[attackerId] += reward
                self.sendTitle('§a§l+$%s §r击杀一名敌人的奖励' % reward, 3, attackerId)
                self.sendCmd('/playsound note.harp', attackerId)

            else:
                if self.beds[self.teams[playerId]]:
                    self.sendMsgToAll("%s杀死了%s" % (attackerNick, playerNick))
                    print 'kill'
                else:
                    self.sendMsgToAll("%s杀死了%s。 §6§l最终击杀！" % (attackerNick, playerNick))
                    self.teams.pop(playerId)
                    print 'final kill'
            self.balance[playerId] = 0
        else:
            print 'invalid kill. %s' % self.teams

    def OnPlayerRespawnFinishServer(self, data):
        playerId = data['playerId']

        if self.status == 0:
            lobbyGameApi.TryToKickoutPlayer(playerId, "removed from match")
            return

        if playerId in self.teams:
            self.sendCmd('/effect @s slowness 5 255 true', playerId)
            self.sendCmd('/effect @s blindness 5 1 true', playerId)
            self.setPos(playerId, c.pos[self.teams[playerId]])
            self.sendTitle('§c§l你死了！§r§7将在5秒后回到战场', 3, playerId)
        else:
            self.sendTitle('§c§l您已被淘汰', 1, playerId)
            utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
            utilsSystem.SetPlayerSpectate(playerId, True)

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        uid = data['uid']
        if playerId in self.waiting:
            self.waiting.pop(self.waiting.index(playerId))
        if playerId in self.teams:
            if self.getCountInList(self.teams[playerId], self.teams) < 1:
                # TODO Team elimination
                self.TeamWipeout(self.teams[playerId])
            self.teams.pop(playerId)


    def NpcHit(self, entityId, playerId):
        bwsSystem = serverApi.GetSystem('bws', 'bwsSystem')
        if bwsSystem and playerId in self.balance:
            bwsSystem.OpenBws(playerId, self.balance[playerId])
        else:
            self.sendMsg('§c抱歉，商店没有被加载!', playerId)

    def OnActorAcquiredItemServer(self, data):
        print 'player pickup itme=%s' % data
        playerId = data['actor']
        itemDict = data['itemDict']
        resNames = ['minecraft:iron_ingot', 'minecraft:gold_ingot', 'minecraft:diamond', 'minecraft:emerald']

        name = itemDict['itemName']
        count = itemDict['count']

        mProhibitList = [
            'iron_helmet',
            'iron_chestplate',
            'diamond_helmet',
            'diamond_chestplate',
            'diamond_leggings',
            'diamond_boots'
        ]

        if name.replace('minecraft:', '') in mProhibitList:
            for item in mProhibitList:
                self.sendCmd('/clear @s %s' % item, playerId)

        if not (data['acquireMethod'] == 1 and name in resNames):
            return

        if not playerId in self.teams:
            data['cancel'] = True
            return

        self.sendCmd('/playsound random.orb', playerId)
        name = name.replace('minecraft:', '')
        if playerId in self.balance and name in c.resValue:
            price = c.resValue[name]
            self.balance[playerId] += price*count
            self.sendTitle('§a§l+$%s §r§f拾取资源' % (price*count), 3, playerId)
            self.sendCmd('/clear @s %s' % name, playerId)
        elif not playerId in self.balance:
            self.sendTitle('res_pickup_fail:no balance account', 3, playerId)

            if self.status == 1:
                self.sendTitle('[FATAL]err_invalid_balance_account IN %s: -> err_invalid_game_status: -> server script process LOCKED! Rebooting in 10 seconds.\n脚本因错误/bug锁死！将在10秒后重启' % playerId)
            self.status = 2

            rebootSystem = serverApi.GetSystem('reboot', 'rebootSystem')
            rebootSystem.DoReboot(False)

            def a():
                self.InitArena()
            commonNetgameApi.AddTimer(2.0, a)

    def OnServerEntityTryPlaceBlock(self, data):
        x = data['x']
        y = data['y']
        z = data['z']
        name = data['fullName']
        playerId = data['entityId']

        print 'placeblock data=' % data

        if playerId not in self.balance:
            data['cancel'] = True
            self.sendMsg('§c这里不能放方块噢', playerId)
            return

        if name == 'minecraft:bed':
            data['cancel'] = True
            self.sendMsg('§c该床已被摧毁，不能重新放置', playerId)
            return

        teamPos = c.pos[self.teams[playerId]]
        dist = self.dist(x, y, z, teamPos[0], teamPos[1], teamPos[2])
        if dist <= 1:
            data['cancel'] = True
            self.sendMsg('§c这里不能放方块噢', playerId)
            return

        if name == 'minecraft:tnt':
            print 'tnt ignite!!!'
            comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
            comp.SetBlockNew((x, y, z), {
                'name': 'air'
            }, 0, 0)
            self.sendCmd('/summon tnt %s %s %s' % (x, y+0.50, z), playerId)
            commonNetgameApi.AddTimer(0.2, lambda p: self.sendCmd('/setblock %s %s %s air' % (x, y, z), p), playerId)
            # self.blocks[playerId].append((x, y, z))
            return

        self.blocks[playerId].append((x, y, z))
        print 'blocks is now %s' % self.blocks

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

    def ArmorTick(self):
        if self.status != 1:
            return
        for player in self.teams:
            if self.armors[player] >= 0:
                self.armors[player] -= 1

            if player in self.armors and self.armors[player] >= 1 and self.armors[player] <= self.armorsTime[player]:
                self.sendTitle('§e§l盔甲过期时间 §b%s秒§r§7/%s秒\n§a击杀一名敌人以重置时间！' % (self.armors[player], self.armorsTime[player]), 3, player)
            elif player in self.armors and self.armors[player] >= 1 and self.armors[player] > self.armorsTime[player]:
                self.sendTitle('§e§l盔甲过期时间 §b%s秒§r§7/%s秒\n§6盔甲计时超频中' % (self.armors[player], self.armorsTime[player]), 3, player)

            value = self.armors[player]
            if value == 60:
                self.sendMsg("§e§l您的盔甲还有60秒过期，击杀一名敌人以重置时间", player)
            elif value == 30:
                self.sendMsg("§6§l您的盔甲还有30秒过期，击杀一名敌人以重置时间", player)
            elif 1 < value <= 5:
                self.sendMsg("§c§l您的盔甲还有%s秒过期，击杀一名敌人以重置时间" % value, player)
            elif value == 1:
                self.sendMsg("§4§l您的盔甲已过期。若需要，请您重新购买", player)
                comp = serverApi.GetEngineCompFactory().CreateItem(player)
                comp.SpawnItemToArmor({
                    'itemName': 'minecraft:diamond_helmet',
                    'count': 0,
                    'auxValue': 0
                }, player, serverApi.GetMinecraftEnum().ArmorSlotType.HEAD)
                comp.SpawnItemToArmor({
                    'itemName': 'minecraft:diamond_chestplate',
                    'count': 0,
                    'auxValue': 0
                }, player, serverApi.GetMinecraftEnum().ArmorSlotType.BODY)
                comp.SpawnItemToArmor({
                    'itemName': 'minecraft:diamond_leggings',
                    'count': 0,
                    'auxValue': 0
                }, player, serverApi.GetMinecraftEnum().ArmorSlotType.LEG)
                comp.SpawnItemToArmor({
                    'itemName': 'minecraft:diamond_boots',
                    'count': 0,
                    'auxValue': 0
                }, player, serverApi.GetMinecraftEnum().ArmorSlotType.FOOT)
                for name in ['chainmail', 'iron', 'diamond']:
                    self.sendCmd('/clear @s %s_helmet' % name, player)
                    self.sendCmd('/clear @s %s_chestplate' % name, player)
                    self.sendCmd('/clear @s %s_leggings' % name, player)
                    self.sendCmd('/clear @s %s_boots' % name, player)

    def BoardTick(self):
        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        do = utilsSystem.TextBoard
        if self.status == 0:
            for player in serverApi.GetPlayerList():
                self.sendCmd('/gamerule sendcommandfeedback false', player)
                self.sendCmd('/gamerule showdeathmessages false', player)
                do(player, True, """
§e§lICE§a_§bGAME§r§l -> §c起床§f战争§r

§7满%s人即可开始游戏§r
§l目前人数: §e%s人
§f倒计时: §c%s秒

§r§e在ICE_GAME体验起床战争
§7%s
""" % (c.startCountdown, len(self.waiting), self.countdown, self.epoch2Datetime(time.time())))

        elif self.status == 1:
            for player in serverApi.GetPlayerList():
                if player in self.teams:
                    team = self.teams[player]
                else:
                    team = None

                extra = ""
                for item in c.teamNames:
                    condition = '§l'+'§aOK'*int(bool(self.beds[item]))*int(bool(self.getCountInList(item, self.teams)))+('§e%s LEFT' % self.getCountInList(item, self.teams))*int(bool(not self.beds[item]))*int(bool(self.getCountInList(item, self.teams)))+'§cDEAD'*int(bool(self.getCountInList(item, self.teams) == 0))
                    extra += '%s: %s§r\n' % (c.teamNames[item], condition)
                content = """
§e§lICE§a_§bGAME§r§l -> §c起床§f战争§r
§b比赛已进行%s

%s

§l§b余额: §r%s
§l§b击杀: §r%s

§r§e在ICE_GAME体验起床战争
""" % (datetime.timedelta(seconds=self.timer), extra,
        self.balance[player],
       self.kills[player]
       )
                do(player, True, content)
                print 'do for %s' % player

    def ResTick(self):
        comp = serverApi.GetEngineCompFactory().CreateItem(serverApi.GetLevelId())
        if self.status == 1:
            self.resTimer -= 1

            if self.resTimer % 1 == 0:
                for pos in c.resPos['iron']:
                    comp.SpawnItemToLevel({
                        'itemName': 'minecraft:iron_ingot',
                        'count': 1
                    }, 0, pos)

            # TODO Bomb bw adaptation
            if self.resTimer % 10 == 0 and 'Bomb' in commonNetgameApi.GetServerType() and self.timer > 120:
                for pos in c.resPos['iron']:
                    comp.SpawnItemToLevel({
                        'itemName': 'minecraft:tnt',
                        'count': 1
                    }, 0, pos)
            if self.resTimer % 10 == 0:
                for pos in c.resPos['gold']:
                    comp.SpawnItemToLevel({
                        'itemName': 'minecraft:gold_ingot',
                        'count': 1
                    }, 0, pos)
            if self.resTimer % 30 == 0:
                for pos in c.resPos['diamond']:
                    comp.SpawnItemToLevel({
                        'itemName': 'minecraft:diamond',
                        'count': 1
                    }, 0, pos)
            if self.resTimer % 120 == 0:
                for pos in c.resPos['emerald']:
                    comp.SpawnItemToLevel({
                        'itemName': 'minecraft:emerald',
                        'count': 1
                    }, 0, pos)

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

            self.timer += 1
            self.updateScoreboard()

            for player in serverApi.GetPlayerList():
                self.sendCmd('/kill @e[type=villager]', player)

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

            for player in self.teams:
                comp = serverApi.GetEngineCompFactory().CreatePos(player)
                pos = comp.GetPos()
                basePos = c.pos[self.teams[player]]
                if self.dist(pos[0], pos[1], pos[2], basePos[0], basePos[1], basePos[2]) <= 4.5 and self.beds[self.teams[player]]:
                    self.sendCmd('/effect @s regeneration 2 5 true', player)

            if self.timer > 20:
                for item in c.bedPos:
                    pos = c.bedPos[item]
                    heading = c.bedHeading[item]
                    comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
                    blockDict = comp.GetBlockNew(pos, 0)
                    name = blockDict['name']

                    if name != 'minecraft:bed' and self.beds[item]:
                        for player in serverApi.GetPlayerList():
                            self.sendCmd('/setblock %s %s %s bed %s' % (pos[0], pos[1], pos[2], heading), player)

        self.updateServerStatus(self.status)

        # -----------Individual checks-----------
        # Check to switch gamemode
        if serverApi.GetPlayerList():
            if self.status == 1:
                for player in serverApi.GetPlayerList():
                    if player in self.teams:
                        self.sendCmd('/gamemode 0', player)
                    else:
                        self.sendCmd('/gamemode 2', player)
            else:
                self.sendCmd('/gamemode 2 @a', serverApi.GetPlayerList()[0])

    def win(self, team):
        teamName = c.teamNames[team]
        self.status = 2

        totalList = []
        for player in serverApi.GetPlayerList():
            totalList.append((lobbyGameApi.GetPlayerNickname(player),))
        mysqlPool.AsyncExecutemanyWithOrderKey('bwconclusion', 'UPDATE bw SET total=total+1 WHERE uid=%s;', totalList)
        for player in self.teams:
            if self.teams[player] == team:
                self.sendTitle("§6§l胜利", 1, player)
                self.sendTitle("恭喜您获得胜利！！！", 2, player)
                self.sendMsg("§a+256NEKO §f获得胜利的奖励", player)
                mysqlPool.AsyncExecuteWithOrderKey('121doas9ps8dna9p8s', 'UPDATE bw SET win=win+1 WHERE uid=%s', (player))

                ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')
                ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(player), 256, 'bw win')

        winner = self.rank(self.kills)
        ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(winner), 8, 'bw mvp', True)
        self.sendMsg("§a+8CREDITS §f获得MVP的奖励", player)

        # handle win sql
        # sql = 'UPDATE total SET total=total+1 WHERE uid=%s;'
        # mysqlPool.AsyncExecuteWithOrderKey('121doas9ps8dna9p8s', sql, totalList)
        # sql = 'UPDATE total SET win=win+1 WHERE uid=%s;'
        # mysqlPool.AsyncExecuteWithOrderKey('121doas9ps8ddna9p8s', sql, winningTeam)
        # over

        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        utilsSystem.ShowWinBanner(winner)
        sql = 'UPDATE bw SET mvp=mvp+1 WHERE uid=%s AND total>=mvp;'
        mysqlPool.AsyncExecuteWithOrderKey('asd8912381das', sql, (lobbyGameApi.GetPlayerUid(winner),))

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
        mTeamAssign = 1
        self.timer = 0
        self.balance = {}
        self.kills = {}
        self.armorsTime = {}
        self.beds = {
            1: False,
            2: False,
            3: False,
            4: False
        }
        if '8bw1' in commonNetgameApi.GetServerType():
            self.beds[5] = False
            self.beds[6] = False
            self.beds[7] = False
            self.beds[8] = False
        comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
        for player in self.waiting:
            self.kills[player] = 0
            self.teams[player] = mTeamAssign

            self.armors[player] = None

            self.sendCmd('/gamemode s', player)
            self.sendMsg("您的队伍是：%s" % c.teamNames[mTeamAssign], player)
            self.sendMsg("分配队伍中，可能稍有卡顿，请不要退出！！！。我们将在未来修复该问题。", player)
            if 'Bomb' in commonNetgameApi.GetServerType():
                self.sendMsg("""§6============
§l§b炮爷起床战争
§rTNT无限量供应 - 使用您精湛的技术与走位摧毁敌人的床！
TNT将在游戏开始2分钟后在队伍基地资源点中开始生成，
请利用这段时间保护您的床。

小贴士：放完TNT倒数5秒再跳，别跳早了！
§r§6============""", player)
            mTeamAssign += 1
            if mTeamAssign > c.teamsCount:
                mTeamAssign = 1
            self.balance[player] = 0
            self.beds[self.teams[player]] = True

            def a(p):
                comp = serverApi.GetEngineCompFactory().CreateName(p)
                comp.SetPlayerPrefixAndSuffixName(c.teamPrefix[self.teams[p]], serverApi.GenerateColor('RED'), '',serverApi.GenerateColor('RED'))
            commonNetgameApi.AddTimer(6.0, a, player)

        self.waiting = []
        for player in self.teams:
            teamPos = c.pos[self.teams[player]]
            self.setPos(player, teamPos)
            self.sendCmd('/spawpoint @s %s %s %s' % (teamPos[0], teamPos[1], teamPos[2]), player)
            self.blocks[player] = []

        self.sendCmd('/kill @e[type=villager]', serverApi.GetPlayerList()[0])
        self.sendCmd('/kill @e[type=item]', serverApi.GetPlayerList()[0])
        self.playStartAnimation()
        def a():
            for pos in c.bedPos:
                p = c.bedPos[pos]
                heading = c.bedHeading[pos]
                if self.getMatchingList(pos, self.teams):
                    self.sendCmd('/setblock %s %s %s bed %s' % (p[0], p[1], p[2], heading), self.getMatchingList(pos, self.teams)[0])
        commonNetgameApi.AddTimer(3.0, a)
