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

hubConfirm = {}

##
exclude = ["transf", "trans", "transfer", "again", "stats", "vk", "votekick", "vkick", "reboot", "rank", "pvp", "rp", "rb", "mute", "report", "r", "ban", "stage", "eco", "sudo", "laba", "buglet", "xiaolaba", "testui", "admin", 'hlaba', 'helperchan', 'helperlaba', 'hchan', 'hc']
##

# 在modMain中注册的Server System类
class cmdSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self,
                            self.OnCommand)

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

    def sendMsg(self, msg, playerId):
        comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
        comp.NotifyOneMessage(playerId, msg, "§f")

    def forceSelect(self, slot, playerId):
        # print 'forceSelect called slot='+slot+' playerId='+playerId
        comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
        comp.ChangeSelectSlot(slot)

    #################################

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("lobbyutils", "lobbyutilsClient", 'TestRequest', self, self.OnTestRequest)


    def OnCommand(self, data):
        data['cancel'] = True
        playerId = data['entityId']
        msg = data['command'].split()
        cmd = msg[0].strip('/')

        if not(cmd == 'hub' or cmd == 'lobby'):
            hubConfirm[playerId] = 0

        if (cmd == 'hub' or cmd == 'lobby'):
            if commonNetgameApi.GetServerType() != 'lobby':
                if playerId not in hubConfirm or hubConfirm[playerId] == 0:
                    self.sendMsg("§e再次执行命令以确认。输入任何其他命令以取消。\nRe-issue command to confirm. Issue any other command to cancel.", playerId)
                    hubConfirm[playerId] = 1
                elif hubConfirm[playerId] == 1:
                    transData = {'position': [107, 153, 105]}
                    lobbyGameApi.TransferToOtherServer(playerId, 'lobby', json.dumps(transData))
                    hubConfirm[playerId] = 0
            else:
                self.sendMsg("§c您已经位于主城。", playerId)
        elif cmd == 'pvp':
            if commonNetgameApi.GetServerType() != 'game_practice':
                self.sendMsg('pvp: PVP toggle system: no such system', playerId)
        elif cmd in exclude:
            pass
        elif cmd == 'kill':
            comp = serverApi.GetEngineCompFactory().CreateHurt(playerId)
            comp.Hurt(1200, serverApi.GetMinecraftEnum().ActorDamageCause.EntityAttack, None, None, False)
        elif cmd == 'cmdhelp':
            self.sendMsg("""
            §b/cmdhelp §f- 显示当前页面
            §b/report /r §f- 举报
            §b/hub /lobby §f- 返回大厅
            §b/kill §f- 重开
            §b/sudo §f- 管理独立密码
            §b/eco §f- 管理钱包
            §b/vk §f- 投票踢出玩家
            §f使用§b/<命令> -h §f查看特定命令的帮助（若适用）
            """, playerId)
        elif cmd == 'credits':
            self.sendMsg("""
            §a§l鸣谢
            §r§e感谢你们对ICE_GAME网络服开发的付出。
            没有你们，服务器将不曾存在。
            §f“Lovely_小柒”——服主
            ”黑瞳“——技术支持
            “蔬菜”——多媒体支持
            ”MAX_THUK“——地图建设（已退职）
            ”Nightmare“——地图建设
            ”纸砚“——地图建设
            ”抽插“——地图建设
            ”一只灰漫君“——地图建设
            ”Nightmare“——地图建设
            ”小绿“——精神支持
            """, playerId)
            self.sendMsg("""
            ”SKA_GAME“——精神支持
            §lThe_Yrxs
            §r”Terr xx“——技术支持
            ”卡哇伊der大白“——技术支持
            """, playerId)

        elif cmd == 'ver' or cmd == 'version':
            self.sendMsg("ICE_GAME Update V0.1\nICE_GAME使用Vapu Server V114514 框架强力驱动", playerId)
        elif cmd == 'top' or cmd == 'rank':
            serverType = commonNetgameApi.GetServerType()
            if serverType == 'game_rush':
                neteaseRankSystem = serverApi.GetSystem("neteaseRank", "neteaseRankDev")
                neteaseRankSystem.OpenRankUI(lobbyGameApi.GetPlayerUid(playerId))
            else:
                self.sendMsg("%s: rank system not found in server" % (cmd,), playerId)
        elif cmd == 'ransom':
            try:
                flag = msg[1]
            except IndexError:
                self.sendMsg('§c命令无效', playerId)
                return

            uid = lobbyGameApi.GetPlayerUid(playerId)

            if flag == 'ffa':
                def RedisCb(args):
                    print 'rediscb args=%s' % args
                    if args and args>time.time():
                        sql = 'SELECT unsafe FROM sudo WHERE uid=%s;'

                        def Cb(args):
                            if args:
                                unsafe = args[0][0]
                                if unsafe:
                                    self.sendMsg('ransom: permission denied', playerId)
                                    return
                                else:
                                    sql = 'SELECT neko,high FROM eco WHERE uid=%s;'

                                    def Cb(args1):
                                        if args1:
                                            neko = args1[0][0]
                                            high = args1[0][1]
                                            ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')
                                            if neko >= 1024:
                                                ecoSystem.GivePlayerEco(uid, -1024, 'ffa ransom neko')
                                                redisPool.AsyncDelete('ffa-antilog-%s' % uid)
                                                self.sendMsg('§b成功支付1024NEKO', playerId)
                                            elif high >= 32:
                                                ecoSystem.GivePlayerEco(uid, -32, 'ffa ransom credits', True)
                                                redisPool.AsyncDelete('ffa-antilog-%s' % uid)
                                                self.sendMsg('§b成功支付32CREDITS', playerId)
                                            else:
                                                self.sendMsg('§c钱包余额不足，无法付款！', playerId)
                                                return

                                    mysqlPool.AsyncQueryWithOrderKey('vmxoz7mf0a8nsd', sql, (uid,), Cb)

                        mysqlPool.AsyncQueryWithOrderKey('vmxoz7mf0a8nsd', sql, (uid,), Cb)
                    else:
                        self.sendMsg('§c您当前无需支付赎金！', playerId)
                        return
                redisPool.AsyncGet("ffa-antilog-%s" % (uid,), RedisCb)



            else:
                self.sendMsg('§c命令无效', playerId)

        elif cmd == 'uid':
            self.sendMsg("%s的UID是 %s" % (lobbyGameApi.GetPlayerNickname(playerId), lobbyGameApi.GetPlayerUid(playerId)), playerId)
        elif cmd == 'spec':
            sql = 'select * from perms where type>94 and uid=%s;'
            def Cb(args):
                if args:
                    utilsSystem = serverApi.GetSystem("utils", "utilsSystem")
                    print 'utilsSystem=%s' % (utilsSystem,)

                    if msg[1] == 'on':
                        utilsSystem.SetPlayerSpectate(playerId, True)
                        self.sendMsg('now spectating', playerId)
                    elif msg[1] == 'off':
                        utilsSystem.SetPlayerSpectate(playerId, False)
                        self.sendMsg('no longer spectating', playerId)
                    else:
                        self.sendMsg('/spec on/off', playerId)
                else:
                    self.sendMsg("spec: Operation not permitted", playerId)
                    return
            mysqlPool.AsyncQueryWithOrderKey('a978ds9b8614128930', sql, (lobbyGameApi.GetPlayerUid(playerId),), Cb)
        elif cmd == 'listp':
            sql = 'SELECT * FROM perms WHERE type>94 AND uid=%s;'
            def Cb(args):
                if args:
                    if len(msg) > 3:
                        self.sendMsg("§einvalid command", playerId)
                        return
                    elif len(msg) == 1:
                        darken = False
                        self.sendMsg("§bNickname/PID/UID", playerId)
                        for player in serverApi.GetPlayerList():
                            if darken:
                                self.sendMsg("§7%s/%s/%s" % (lobbyGameApi.GetPlayerNickname(player), player, lobbyGameApi.GetPlayerUid(player)), playerId)
                                darken = False
                            else:
                                self.sendMsg("%s/%s/%s" % (
                                lobbyGameApi.GetPlayerNickname(player), player, lobbyGameApi.GetPlayerUid(player)),
                                             playerId)
                                darken = True
                    elif len(msg) >= 2:
                        flag = msg[1]
                        if flag == '-h':
                            self.sendMsg("""
                            §bPlayer UID utility
                            §r/listp list all uid in server
                            §7/listp -k [keyword] list player with KEYWORD in nickname
                            """, playerId)
                        elif flag == '-k':
                            if len(msg) < 3:
                                self.sendMsg("§einvalid command", playerId)
                                return
                            kw = msg[2]
                            match = 0
                            darken = False
                            self.sendMsg("§bNickname/PID/UID", playerId)
                            for player in serverApi.GetPlayerList():
                                if kw in lobbyGameApi.GetPlayerNickname(player):
                                    if darken:
                                        self.sendMsg("§7%s/%s/%s" % (
                                        lobbyGameApi.GetPlayerNickname(player), player, lobbyGameApi.GetPlayerUid(player)),
                                                     playerId)
                                        darken = False
                                    else:
                                        self.sendMsg("%s/%s/%s" % (
                                            lobbyGameApi.GetPlayerNickname(player), player,
                                            lobbyGameApi.GetPlayerUid(player)),
                                                     playerId)
                                        darken = True
                                    match += 1
                            self.sendMsg("§e查找了%s个玩家。其中，%s个符合条件。" % (len(serverApi.GetPlayerList()), match), playerId)
                        else:
                            self.sendMsg("§einvalid command", playerId)
                    else:
                        self.sendMsg("§einvalid command", playerId)

                else:
                    self.sendMsg("listp: Operation not permitted", playerId)
                    return
            mysqlPool.AsyncQueryWithOrderKey("89asd9hbuw34", sql, (lobbyGameApi.GetPlayerUid(playerId),), Cb)
        elif cmd in ['cos', 'cosmetics', 'cosmetic', 'shop']:
            cosSystem = serverApi.GetSystem('cos', 'cosSystem')
            cosSystem.EnterCosMgr(playerId)
        elif cmd == 'musictest':
            musicSystem = serverApi.GetSystem('music', 'musicSystem')
            if len(msg) != 2:
                self.sendMsg('/musictest <音乐名>', playerId)
                return
            if commonNetgameApi.GetServerType() != 'lobby':
                self.sendMsg('musictest: not in lobby', playerId)
                return

            li = ['music.mvp.4']
            if msg[1] not in li:
                self.sendMsg('musictest: %s: no such music' % msg[1], playerId)
                return
            musicSystem.PlayMusicToPlayer(playerId, msg[1])

        elif cmd == 'ping':
            sql = 'SELECT * FROM perms WHERE type>94 AND uid=%s;'
            def Cb(args):
                if args:

                    if len(msg) < 2:
                        self.sendMsg("which facility do you want to ping(test)?", playerId)
                        return

                    flag = msg[1]
                    uid = lobbyGameApi.GetPlayerUid(playerId)

                    if 'iac' in flag:
                        iacSystem = serverApi.GetSystem('iac', 'iacSystem')

                    if flag == 'iac.kick':
                        iacSystem.IacKick(uid, playerId)
                    elif flag == 'iac.ban':
                        iacSystem.IacBan(uid)
                    elif flag == 'iac.addvl':
                        iacSystem.AddVl(uid, 1)
                    elif flag == 'iac.verbose':
                        iacSystem.IacVerbose('test')
                        utils = serverApi.GetSystem('utils', 'utilsSystem')
                        utils.CreateAdminMessage('test')
                    elif flag == 'iac.announce':
                        iacSystem.AnnounceBan()
                    elif flag == 'draw.test':
                        print 'testing draw.test'
                        drawSystem = serverApi.GetSystem('draw', 'drawSystem')
                        drawSystem.ApiTestDraw(playerId)
                    elif flag == 'draw.open':
                        drawSystem = serverApi.GetSystem('draw', 'drawSystem')
                        drawSystem.OpenDrawUi(playerId)
                    elif flag == 'ffa.antilog':
                        ffaSystem = serverApi.GetSystem('ffa', 'ffaSystem')
                        ffaSystem.antilog[playerId] = time.time()+15
                    elif flag == 'builtin.movement':
                        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
                        comp.SetFootPos((105,187,122))
                    elif flag == 'builtin.item':
                        self.sendCmd('/give @s tnt', playerId)
                    elif flag == 'bws.test':
                        bwsSystem = serverApi.GetSystem('bws', 'bwsSystem')
                        bwsSystem.OpenBws(playerId, 8000)
                    elif flag == 'music.play':
                        musicSystem = serverApi.GetSystem('music', 'musicSystem')
                        musicSystem.PlayMusicToPlayer(playerId, msg[2])
                    elif flag == 'builtin.text':
                        utils = serverApi.GetSystem('utils', 'utilsSystem')
                        utils.TextBoard(playerId, True, msg[2])
                    elif flag == 'music.mvp.test':
                        utils = serverApi.GetSystem('utils', 'utilsSystem')
                        utils.ShowWinBanner(playerId)
                    elif flag == 'guns.give':
                        gunsSystem = serverApi.GetSystem('guns', 'gunsSystem')
                        gunsSystem.GiveGunToPlayer(int(msg[2]), playerId)
                    elif flag == 'dmg.test':
                        comp = serverApi.GetEngineCompFactory().CreateHurt(playerId)
                        comp.Hurt(2, serverApi.GetMinecraftEnum().ActorDamageCause.EntityAttack, playerId, None,
                                  False)
                    elif flag == 'fb.start.test':
                        fbSystem = serverApi.GetSystem('fb', 'fbSystem')
                        fbSystem.NotifyToClient(playerId, 'ShowStartScreen', {
                            'theme': 'test',
                            'time': 900
                        })
                    else:
                        self.sendMsg("ping: %s: no such facility" % (flag,), playerId)
                        return

                else:
                    self.sendMsg("ping: Operation not permitted", playerId)
                    return
            mysqlPool.AsyncQueryWithOrderKey('dasd89063431', sql, (lobbyGameApi.GetPlayerUid(playerId),), Cb)
        elif cmd == 'again':
            bwSystem = serverApi.GetSystem('bw', 'bwSystem')
            if bwSystem:
                self.RequestToServiceMod("bw", "RequestMatchmakingEvent", playerId, bwSystem.BwMatchmakingCallback, 2)
            else:
                self.sendMsg('again: bw: no such system', playerId)

        elif cmd == 'chmod':
            sql = 'SELECT * FROM perms WHERE uid=%s AND type>96 AND (endDate<0 OR endDate>%s);'
            def Cb(args):
                if args:
                    if not(3 < len(msg) < 5):
                        self.sendMsg("§einvalid command", playerId)
                        return

                    level = msg[1]
                    uid = msg[2]
                    if len(msg) == 4:
                        date = msg[3]
                    else:
                        date = -1

                    try:
                        int(level)
                        int(uid)
                        int(date)
                    except:
                        self.sendMsg("§einvalid arguments")
                        return
                    if date >= 0:
                        if date == 0:
                            self.sendMsg("§einvalid command")
                            return
                        endDate = int(math.floor(time.time()))+int(date)*86400
                    else:
                        endDate = -1

                    sql = 'SELECT * FROM sudo WHERE uid=%s;'
                    def Cb(args):
                        if args:
                            sql = 'INSERT INTO perms (uid, type, endDate) values (%s, %s, %s);'
                            mysqlPool.AsyncExecuteWithOrderKey('asd10nxcaoiusd', sql, (uid, level, endDate))
                            self.sendMsg('ok', playerId)
                        else:
                            self.sendMsg("§cno such player!", playerId)
                            return
                    mysqlPool.AsyncQueryWithOrderKey('asd98612351', sql, (uid,), Cb)

                else:
                    self.sendMsg("chmod: Operation not permitted", playerId)
                    return
            mysqlPool.AsyncQueryWithOrderKey('asmg7fd17341', sql, (lobbyGameApi.GetPlayerUid(playerId), time.time()), Cb)

        elif cmd == 'getpos':
            self.sendMsg("you are in %s" % (lobbyGameApi.GetServerId(),), playerId)
        else:
            self.sendMsg(cmd+": command not found", playerId)