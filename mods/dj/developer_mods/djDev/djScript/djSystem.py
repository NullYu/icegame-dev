# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import apolloCommon.commonNetgameApi as commonNetgameApi
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.mysqlPool as mysqlPool
import djScript.djConst as c

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

# 在modMain中注册的Server System类
class djSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()
        self.enable = True

        self.totalPlays = 0
        self.playingFree = None

        self.data = {}
        self.buyConf = {}

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
    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self, self.OnCommand)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerChatEvent", self, self.OnServerChat)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self, self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self, self.OnDelServerPlayer)

    def OnServerChat(self, data):
        playerId = data['playerId']
        if playerId in self.buyConf and self.buyConf[playerId]:
            self.buyConf[playerId] = False

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        self.buyConf[playerId] = False
        uid = lobbyGameApi.GetPlayerUid(playerId)
        sql = 'SELECT itemId FROM items WHERE uid=%s and type="music" and (expire<0 or expire>%s) and inUse=1;'

        def Cb(args):
            if args:
                mInsertionBuffer = []
                for item in args:
                    mInsertionBuffer.append(item[0])
                self.data[playerId] = mInsertionBuffer
                print 'search done, buffer=', self.data[playerId]
            else:
                self.data[playerId] = None

        mysqlPool.AsyncQueryWithOrderKey('da217e98ndas', sql, (uid, time.time()), Cb)

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        if playerId in self.buyConf:
            self.buyConf.pop(playerId)

    def OnCommand(self, data):
        playerId = data['entityId']
        cmd = data['command'].split()
        validCmd = ["/dj", "/music"]
        if cmd[0] in validCmd:
            data['cancel'] = True
            if not self.enable:
                self.sendCmd('dj: Operation not permitted', playerId)
                return

            ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')
            if not ecoSystem:
                self.sendMsg('§c出现错误：§fecoSystem: No such system [FATAL]', playerId)
                return

            flag = cmd[1]
            if flag.lower() == '-h':
                self.sendMsg("§bdj - 点歌器\n§r§l/dj (/music) -chlp [music#]\n§r/dj [-c cancel | -h help | -l list owned music | -p play [(listed) music ID] ]")
                return

            elif flag == '-l':
                if playerId in self.data:
                    self.sendMsg('§e注意： 若您获得了任何新的音乐，您必须重新进入服务器使其生效。')

                data = self.data[playerId]
                if data:
                    self.sendMsg('§b§l您拥有的音乐：', playerId)
                    for item in data:
                        if item in c.musicNames:
                            name = c.musicNames[item]
                        else:
                            name = '§c§l<!CONST ERR>§r'
                        self.sendMsg('%s %s' % (item, name), playerId)
                else:
                    self.sendMsg('§c您未拥有任何音乐！', playerId)

                self.sendMsg('§b§l当前的限免音乐：', playerId)
                data = c.freeMusics
                for musicId in data:
                    self.sendMsg('*%s %s' % (musicId, data[musicId]), playerId)
                self.sendMsg('§6在音乐ID前输入*以选中限免音乐 ', playerId)

            elif flag == '-p':
                if len(cmd) != 3:
                    self.sendMsg("§c无效的命令。使用/dj -h查看帮助。", playerId)
                    return
                elif self.totalPlays >= 5:
                    self.sendMsg("§c您来晚了，此房间的点歌次数已达到上限。下次好运！", playerId)
                    return

                isFree = False
                musicId = cmd[2]
                if musicId[0] == '*':
                    isFree = True
                    musicId = musicId[1:]
                try:
                    int(musicId)
                except ValueError:
                    self.sendMsg("§c无效的命令。使用/dj -h查看帮助。", playerId)
                    return
                musicId = int(musicId)

                if isFree:
                    musics = c.freeMusics
                else:
                    musics = self.data[playerId]
                if not musicId in musics:
                    self.sendMsg("§e该歌曲不存在，或您不曾拥有该歌曲。", playerId)
                    return

                if isFree:
                    if playerId in ecoSystem.bank:
                        bankData = ecoSystem.bank[playerId]
                        if self.totalPlays < 4:
                            price = c.freePricings[self.totalPlays]
                            bal = bankData[0]
                            if bal >= price:
                                ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(playerId), price, 'dj play')
                                musicSystem = serverApi.GetSystem('music', 'musicSystem')
                                uid = lobbyGameApi.GetPlayerUid(playerId)
                                name = 'music.dj.free.' + str(musicId)
                                for player in serverApi.GetPlayerList():
                                    musicSystem.PlayMusicToPlayer(player, name)
                                    self.sendTitle('§b§l《%s》' % musics[musicId], 1, player)
                                    self.sendTitle('来自§e%s§f的点歌（限免）' % lobbyGameApi.GetPlayerNickname(playerId), 2, player)
                                self.totalPlays += 1
                                self.playingFree = True
                            else:
                                self.sendMsg('§c§l钱包余额不足以购买。§r需要：§b%sNEKO§r， 拥有§b%s' % (price, bal), playerId)
                        else:
                            price = 16
                            bal = bankData[1]
                            if bal >= price:
                                ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(playerId), price, 'dj play')
                                musicSystem = serverApi.GetSystem('music', 'musicSystem')
                                uid = lobbyGameApi.GetPlayerUid(playerId)
                                name = 'music.dj.free.' + str(musicId)
                                for player in serverApi.GetPlayerList():
                                    musicSystem.PlayMusicToPlayer(player, name)
                                    self.sendTitle('§b§l《%s》' % musics[musicId], 1, player)
                                    self.sendTitle('来自§e%s§f的点歌（限免）' % lobbyGameApi.GetPlayerNickname(playerId), 2, player)
                                self.totalPlays += 1
                                self.playingFree = True
                            else:
                                self.sendMsg('§c§l钱包余额不足以购买。§r需要：§b%sCREDITS§r， 拥有§b%s' % (price, bal), playerId)
                    else:
                        self.sendMsg('§c§l!DATA[ecoSystem] ERR', playerId)
                else:
                    if playerId in ecoSystem.bank:
                        bankData = ecoSystem.bank[playerId]
                        if self.totalPlays == 0:
                            price = 1
                            bal = bankData[0]
                            if bal >= price:
                                ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(playerId), price, 'dj play')
                                musicSystem = serverApi.GetSystem('music', 'musicSystem')
                                uid = lobbyGameApi.GetPlayerUid(playerId)
                                name = 'music.dj.free.' + str(musicId)
                                for player in serverApi.GetPlayerList():
                                    musicSystem.PlayMusicToPlayer(player, name)
                                    self.sendTitle('§b§l《%s》' % musics[musicId], 1, player)
                                    self.sendTitle('来自§e%s§f的点歌' % lobbyGameApi.GetPlayerNickname(playerId), 2, player)
                                    self.totalPlays += 1
                            else:
                                self.sendMsg('§c§l钱包余额不足以购买。§r需要：§b%sNEKO§r， 拥有§b%s' % (price, bal), playerId)

                        elif self.playingFree and self.totalPlays < 5:
                            price = 128
                            bal = bankData[0]
                            if bal >= price:
                                ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(playerId), price, 'dj play')
                                musicSystem = serverApi.GetSystem('music', 'musicSystem')
                                uid = lobbyGameApi.GetPlayerUid(playerId)
                                name = 'music.dj.free.' + str(musicId)
                                for player in serverApi.GetPlayerList():
                                    musicSystem.PlayMusicToPlayer(player, name)
                                    self.sendTitle('§b§l《%s》' % musics[musicId], 1, player)
                                    self.sendTitle('来自§e%s§f的点歌' % lobbyGameApi.GetPlayerNickname(playerId), 2, player)
                            else:
                                self.sendMsg('§c§l钱包余额不足以购买。§r需要：§b%sNEKO§r， 拥有§b%s' % (price, bal), playerId)

                        elif not self.playingFree:
                            if self.totalPlays < 4:
                                price = c.freePricings[self.totalPlays]
                                bal = bankData[0]
                                if bal >= price:
                                    ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(playerId), price, 'dj play')
                                    musicSystem = serverApi.GetSystem('music', 'musicSystem')
                                    uid = lobbyGameApi.GetPlayerUid(playerId)
                                    name = 'music.dj.free.' + str(musicId)
                                    for player in serverApi.GetPlayerList():
                                        musicSystem.PlayMusicToPlayer(player, name)
                                        self.sendTitle('§b§l《%s》' % musics[musicId], 1, player)
                                        self.sendTitle('来自§e%s§f的点歌（限免）' % lobbyGameApi.GetPlayerNickname(playerId), 2,
                                                       player)
                                    self.totalPlays += 1
                                else:
                                    self.sendMsg('§c§l钱包余额不足以购买。§r需要：§b%sNEKO§r， 拥有§b%s' % (price, bal), playerId)
                            else:
                                price = 16
                                bal = bankData[1]
                                if bal >= price:
                                    ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(playerId), price, 'dj play')
                                    musicSystem = serverApi.GetSystem('music', 'musicSystem')
                                    uid = lobbyGameApi.GetPlayerUid(playerId)
                                    name = 'music.dj.free.' + str(musicId)
                                    for player in serverApi.GetPlayerList():
                                        musicSystem.PlayMusicToPlayer(player, name)
                                        self.sendTitle('§b§l《%s》' % musics[musicId], 1, player)
                                        self.sendTitle('来自§e%s§f的点歌（限免）' % lobbyGameApi.GetPlayerNickname(playerId), 2,
                                                       player)
                                    self.totalPlays += 1
                                else:
                                    self.sendMsg('§c§l钱包余额不足以购买。§r需要：§b%sCREDITS§r， 拥有§b%s' % (price, bal), playerId)

                    else:
                        self.sendMsg('§c§l!DATA[ecoSystem] ERR', playerId)

            else:
                self.sendMsg("§c无效的命令。使用/dj -h查看帮助。", playerId)
        else:
            if playerId in self.buyConf and self.buyConf[playerId]:
                self.buyConf[playerId] = False
            return

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("report", "reportClient", 'TestRequest', self, self.OnTestRequest)
