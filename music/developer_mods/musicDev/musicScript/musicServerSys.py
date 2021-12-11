# -*- coding: utf-8 -*-
import mod.server.extraServerApi as serverApi
import apolloCommon.commonNetgameApi as commonNetgameApi
import apolloCommon.mysqlPool as mysqlPool
import lobbyGame.netgameApi as lobbyGameApi
import musicScript.musicConst as c

ServerSystem = serverApi.GetServerSystemCls()
mysqlPool.InitDB(30)

####################
enableReplace = False


#########################

class musicServerSystem(ServerSystem):
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        # 初始时调用监听函数监听事件
        # 第一个参数是namespace，表示客户端名字空间，第二个是客户端System名称，第三个是监听事件的名字，第五个参数是回调函数（或者监听函数）
        self.ListenEvents()

        self.mvpList = c.mvp

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
        comp.NotifyOneMessage(playerId, msg, "f")

    def sendMsgToAll(self, msg):
        for player in serverApi.GetPlayerList():
            self.sendMsg(msg, player)

    def ListenEvents(self):
        self.ListenForEvent('music', 'musicClient', 'CheckClientConn', self, self.ClientConn)

    def ClientConn(self, args):
        print 'CALL ClientConn CLIENT STATUS GREEN! args=%s' % (args,)


    # ###Music API ### #

    def PlayMusicToPlayer(self, playerId, musicId):
        print 'CALL PlayMusicToPlayer playerId=%s musicId=%s type=%s' % (playerId, musicId, type)
        args = {
            'playerId': playerId,
            'musicId': musicId,
        }
        self.NotifyToClient(playerId, "PlayMusicEvent", args)

    def StopBgm(self):
        for player in serverApi.GetPlayerList():
            self.NotifyToClient(player, "StopMusicEvent", None)

    def Destroy(self):
        # self.UnListenForEvent("q", "qClient", 'TestRequest', self, self.OnTestRequest)
        pass
