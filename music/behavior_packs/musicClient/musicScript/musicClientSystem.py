# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi

# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()
compFactory = clientApi.GetEngineCompFactory()

# 在modMain中注册的Client System类
class musicClientSys(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        print "====musicClientSystem Init ===="
        # 定义一个event,下面可以通过这个event给服务端发送消息。
        self.ListenEvent()
        self.bMusicId = None

    def ListenEvent(self):
        self.ListenForEvent('music', 'musicSystem', 'PlayMusicEvent', self, self.OnPlayMusic)
        self.ListenForEvent('music', 'musicSystem', 'StopMusicEvent', self, self.OnStopMusic)

        data = 'ok'
        self.NotifyToServer('CheckClientConn', data)

    def OnPlayMusic(self, args, volume=1, stopOrigin=True):
        print 'CALL OnPlayMusic args=', str(args)
        playerId = clientApi.GetLocalPlayerId()
        musicId = args['musicId']
        auComp = compFactory.CreateCustomAudio(playerId)

        if 'music.beeper' not in musicId:
            auComp.StopCustomMusic("music.beeper.default", 0)
        auComp.DisableOriginMusic(stopOrigin)

        if self.bMusicId and not args['keepOrigin']:
            auComp.StopCustomMusicById(self.bMusicId, 0.5)

        comp = clientApi.GetEngineCompFactory().CreatePos(playerId)
        pos = comp.GetPos()
        self.bMusicId = auComp.PlayCustomMusic(musicId, pos, volume, 1, False, playerId)

    def OnStopMusic(self, args):
        playerId = clientApi.GetLocalPlayerId()
        auComp = compFactory.CreateCustomAudio(playerId)
        if self.bMusicId:
            auComp.StopCustomMusicById(self.bMusicId, 0.5)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
