# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import random
import json
import datetime
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.redisPool as redisPool
import apolloCommon.commonNetgameApi as commonNetgameApi
import apolloCommon.mysqlPool as mysqlPool
import eventScript.eventConsts as c

mysqlPool.InitDB(30)

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()


##

# 在modMain中注册的Server System类
class eventSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        self.consts = c
        self.timeStamp = c.originalTimestamp
        self.enableFireworks = False

        self.currentMusic = 0
        self.celebrationStarted = False

        self.musicTimerObj = None

    def ListenEvents(self):
        self.ListenForEvent('event', 'eventClient', 'ActionEvent', self, self.OnClientAction)

        commonNetgameApi.AddRepeatedTimer(1.0, self.tick)

        pass
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

    def epoch2Datetime(self, epoch):
        ts = datetime.datetime.fromtimestamp(int(epoch))
        return ts.strftime('%Y-%m-%d %H:%M:%S')

    def sendMsg(self, msg, playerId):
        comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
        comp.NotifyOneMessage(playerId, msg, "§f")

    def sendMsgToAll(self, msg):
        for player in serverApi.GetPlayerList():
            self.sendMsg(msg, player)

    def generateRandomColorSymbol(self):
        sampleSpace = '123456789ceabdghf'
        return random.sample(sampleSpace, 1)[0]

    def OnClientAction(self, data):
        pass

    def tick(self):
        t = int(time.time() - self.timeStamp)
        shoutSystem = serverApi.GetSystem('shout', 'shoutSystem')

        if commonNetgameApi.GetServerType() == 'lobby' or True:

            # print t

            if -3600 <= t <= 0:
                for player in serverApi.GetPlayerList():
                    self.NotifyToClient(player, 'UpdateTimerEvent', t)

            if t == -3600:
                self.musicRoutine()

                self.sendMsgToAll("§l§c元旦§f庆典 §e将在§660§e分钟后开始！！！")
            elif t == -1800:
                self.sendMsgToAll("§l§c元旦§f庆典 §e将在§630§e分钟后开始！！！")
            elif t == -600:
                self.sendMsgToAll("§l§c元旦§f庆典 §e将在§610§e分钟后开始！！！")
            elif t == -180:
                self.sendMsgToAll("§l§c元旦§f庆典 §e将在§63§e分钟后开始！！！请尽快进入大厅服！")
            elif t == -60:
                self.sendMsgToAll("§l§c元旦§f庆典 §6将在§c60§6秒后开始！！！请尽快进入大厅服！")
            elif t == -51:
                self.currentMusic = 2
                self.musicRoutine()
            elif t == -10:
                self.sendMsgToAll("§l§c元旦§f庆典 §6将在§c10§6秒后开始！！！")
                self.sendMsgToAll("§l§c§o新年倒计时 10 秒")
            elif t == 0:
                def a():
                    self.startCelebration()
                    for player in serverApi.GetPlayerList():
                        self.sendMsg("§l§c§o%s" % -t, player)
                        self.sendTitle("§l§f新§c年§2快§f乐§c!§2!§f!", 1, player)
                commonNetgameApi.AddTimer(0.5, a)

            if 0 > t >= -10:
                for player in serverApi.GetPlayerList():
                    self.sendMsg("§l§%s%s" % (self.generateRandomColorSymbol(), -t), player)
                    self.sendTitle("§l§%s%s" % (self.generateRandomColorSymbol(), -t), 1, player)
                    self.sendTitle("§l§%s新年倒计时 %s 秒" % (self.generateRandomColorSymbol(), -t), 3, player)
                    self.sendTitle("§l新年倒计时", 2, player)

            if t >= 1:
                if t % 2 == 0:
                    for player in serverApi.GetPlayerList():
                        self.sendCmd('/summon fireworks_rocket ~%s~~%s' % (random.randint(0, 15), random.randint(0, 15)), player)
                        self.sendCmd('/summon fireworks_rocket ~%s~~%s' % (random.randint(0, 15), random.randint(0, 15)), player)
                else:
                    for player in serverApi.GetPlayerList():
                        self.sendCmd('/summon fireworks_rocket ~~~', player)
                        self.sendCmd('/summon fireworks_rocket ~~~', player)

        else:
            pass

    def musicRoutine(self):
        # this is a self calling function - call once to prime music loop
        # set self.currentMusic to -1 to stop music

        musicSystem = serverApi.GetSystem('music', 'musicSystem')
        musicList = c.musicList
        commonNetgameApi.CancelTimer(self.musicTimerObj)

        if self.currentMusic == -1:
            return

        self.currentMusic += 1
        if self.currentMusic > len(musicList):
            self.currentMusic = 1
        
        for player in serverApi.GetPlayerList():
            # musicSystem.StopBgm()
            musicSystem.PlayMusicToPlayer(player, musicList[self.currentMusic][0], True)
            self.sendMsg('§e正在播放 §l§b%s §r§e。祝各位新年快乐！' % musicList[self.currentMusic][2], player)

        delay = musicList[self.currentMusic][1]
        self.musicTimerObj = commonNetgameApi.AddTimer(delay, self.musicRoutine)

    def startCelebration(self):
        if self.celebrationStarted:
            return
        self.celebrationStarted = True

        # visuals - fireworks, game time, etc..
        musicSystem = serverApi.GetSystem('music', 'musicSystem')
        t = time.time() - self.timeStamp
        for player in serverApi.GetPlayerList():
            musicSystem.PlayMusicToPlayer(player, 'music.event.fireworks', True)
        self.sendCmd('/time set 18000', serverApi.GetPlayerList()[0])

        self.sendCmd('/time set 18000', serverApi.GetPlayerList()[0])

        # TODO remove debug true statement
        if commonNetgameApi.GetServerType() == 'lobby':
            self.sendMsgToAll("""§e亲爱的玩家，感谢您一年以来对ICE_GAME的支持。
在此，我们为您献上一份礼物，感谢您在2021年的付出：
§l§c2022§f元旦庆典 §r称号——永久
§l§b1024 CREDITS§r
§l§a庆典BGM中的一首 §rMVP音乐——永久（节后发放）
§e我们相信，在新的一年里，我们将做得更好。也希望各位玩家能满足新一年的目标！
最后，祝各位玩家§6§l新年快乐§r§e！！！！！
§rICE_GAME 01JAN2022 (2022.1.1) 已开服226天
""")
            ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')
            for player in serverApi.GetPlayerList():
                uid = lobbyGameApi.GetPlayerUid(player)
                ecoSystem.GivePlayerEco(uid, 1024, '21-22newyear', True)

                mysqlPool.AsyncExecuteWithOrderKey('sdhjxiuchzxiucasd', 'INSERT INTO items (uid, type, itemId, expire) VALUES (%s, "label", 50, -1);', (uid,))
                mysqlPool.AsyncExecuteWithOrderKey('sdhjxiuchzxiucasd', 'INSERT INTO items (uid, type, itemId, expire) VALUES (%s, "mvp", 14, -1);', (uid,))

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("lobbyutils", "lobbyutilsClient", 'TestRequest', self, self.OnTestRequest)
