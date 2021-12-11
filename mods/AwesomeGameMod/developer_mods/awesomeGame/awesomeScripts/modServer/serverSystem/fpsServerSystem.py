# -*- coding: utf-8 -*-

import server.extraServerApi as serverApi
ServerSystem = serverApi.GetServerSystemCls()
from awesomeScripts.modCommon import modConfig
# 用来打印规范格式的log
from mod_log import logger
import lobbyGame.netgameApi as netgameApi

class FpsServerSystem(ServerSystem):

    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        logger.info("===== Server Listen =====")
        # 玩家player id到uid的映射
        self.mPlayerid2uid = {}
        self.ListenEvent()
        # 设置为创造模式 0生存模式，1创造模式，2冒险模式
        netgameApi.SetLevelGameType(2)

    def ListenEvent(self):
        '''
        在类初始化的时候开始监听事件
        '''
        # 服务器开始监听事件，每个事件的详细介绍参考 MC开发者文档（http://mc.163.com/mcstudio/mc-dev/）
        #监听聊天事件,玩家发送聊天信息时触发
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), modConfig.ServerChatEvent, self, self.OnServerChat)
        #监听新增玩家事件，玩家加入时触发
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), modConfig.AddServerPlayerEvent, self, self.OnPlayerAdd)

    # 在Destroy中调用反注册一些事件
    def UnListenEvent(self):
        # 取消监听4个系统事件
        self.UnListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), modConfig.ServerChatEvent, self, self.OnServerChat)
        self.UnListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), modConfig.AddServerPlayerEvent, self, self.OnPlayerAdd)
        
    def OnNpcTouched(self, npc_entity_id, player_entity_id, gameType):
        '''
		点击npc回调函数。
		'''
        if gameType == 'lobby':
            # request_data = {'uid': uid, 'player_id': player_entity_id}
            # self.RequestToService('AwesomeMatch', 'RequestLobby', request_data)
            netgameApi.TransferToOtherServer(player_entity_id, "lobby")

	
    # ServerChatEvent的回调函数（响应函数）
    def OnServerChat(self, args):
        logger.info("ServerChatMessage : %s", args)
        # 这里使用了§这个符号来修改输入消息的用户名和信息
        # 具体参考https://minecraft-zh.gamepedia.com/index.php?title=%E6%A0%B7%E5%BC%8F%E4%BB%A3%E7%A0%81&variant=zh
        #args["username"] = "§l§e Hugo"
        #args["message"] = "§l§e HelloWorld!"
        playerId = args["playerId"]
        if args["message"] == "lobby":
            netgameApi.TransferToOtherServer(playerId, "lobby")

    # 这个Update函数是基类的方法，同样会在引擎tick的时候被调用，1秒30帧（被调用30次）
    def Update(self):
        """
        Driven by system manager, Two tick way
        """
        pass

    # AddServerPlayerEvent的回调函数，在服务器端加入玩家的时候被调用
    def OnPlayerAdd(self, data):
        logger.info("OnPlayerAdd : %s", data)
        playerId = data.get("id", "-1")
        if playerId == "-1":
            return
        uid = netgameApi.GetPlayerUid(playerId)
        self.mPlayerid2uid[playerId] = uid

    # 在清楚该system的时候调用取消监听事件
    def Destroy(self):
        self.UnListenEvent()
