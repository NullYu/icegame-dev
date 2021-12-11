# -*- coding: utf-8 -*-

import mod.client.extraClientApi as clientApi
ClientSystem = clientApi.GetClientSystemCls()
from awesomeModScripts.modCommon import modConfig
# 用来打印规范的log
from mod_log import logger

class FpsClientSystem(ClientSystem):

    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        logger.info("===== Client Listen =====")
        self.ListenEvent()
        # 获取客户端本地玩家的playerId
        self.mPlayerId = clientApi.GetLocalPlayerId()

    def ListenEvent(self):
        '''
        监听引擎和服务端脚本的事件
        '''
        #UI初始化框架完成，此时可以创建UI
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), modConfig.UiInitFinishedEvent, self, self.OnUIInitFinished)
	
    def UnListenEvent(self):
        '''
        取消监听引擎和服务端脚本事件
        '''
        self.UnListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), modConfig.UiInitFinishedEvent, self, self.OnUIInitFinished)

    def OnUIInitFinished(self, args):
        '''
        监听引擎初始化完成事件，在这个事件后创建我们的战斗UI
        '''
        logger.info("OnUIInitFinished : %s", args)

    # 被引擎直接执行的父类的重写函数，引擎会执行该Update回调，1秒钟30帧
    def Update(self):
        """
        Driven by system manager, Two tick way
        """
        pass

    # 在清楚该system的时候调用取消监听事件
    def Destroy(self):
        self.UnListenEvent()