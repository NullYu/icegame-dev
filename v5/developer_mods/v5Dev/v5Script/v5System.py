# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import json
import random
import datetime
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.redisPool as redisPool
import apolloCommon.commonNetgameApi as commonNetgameApi
import apolloCommon.mysqlPool as mysqlPool

mysqlPool.InitDB(30)

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()


# ## ! ## #
u"""
    Special development instructions for this mod:
    Complete UI interfaces and test before moving on to main mod logics.
    Client content (especially UI) must be complete before testing of more complex server logics.
"""

##

# 在modMain中注册的Server System类
class v5SystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        # ------------------
        u"""
            Variables: PrepScreen and WeaponSelection related variables
        """

        self.selectionData = {
            0: {},
            1: {}
        }
        # Structure:
        # selectionData{
        #     team: {
        #         player: [weaponSelectionId, skillSelectionId]
        #     }
        # }

        self.teams = {}
        self.waiting = []
        # 0=t, 1=ct

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self, self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self, self.OnDelServerPlayer)
        self.ListenForEvent('hud', 'hudClient', "DisplayDeathDoneEvent", self, self.OnDisplayDeathDone)
        # self.ListenForEvent('utils', 'utilsClient', 'ActionEvent', self, self.OnClientAction)
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

    def getCountInDict(self, key, dic):
        ret = 0
        for item in dic:
            if dic[item] == key:
                ret += 1
        return ret

    def reset_selectionData(self):
        self.selectionData = {
            0: {},
            1: {}
        }

    # ################## UI INTERFACES #####################
    u"""
        This section contains UI interface functions.
        Complete development of this section before moving on to server code.
    """

    def ShowPrepSelectionScreen(self, isShow, playerLi=serverApi.GetPlayerList(), isUpdate=False):
        for player in playerLi:
            if player in self.teams:
                response = {
                    'isShow': isShow,
                    'isUpdate': isUpdate,
                    'selections': self.selectionData[self.teams[player]]
                }
                self.NotifyToClient(player, 'ShowPrepSelectionScreenEvent', response)

    # ################# SERVER CODE ###############
    u"""
        Starting in this section are the server codes
    """

    def OnAddServerPlayer(self, data):
        playerId = data['id']

    def OnDelServerPlayer(self, data):
        playerId = data['id']

    def start(self):
        for player in self.waiting:
            tCount = self.getCountInDict(0, self.teams)
            ctCount = self.getCountInDict(1, self.teams)
            if tCount == ctCount:
                self.teams[player] = random.randint(0, 1)
            elif tCount > ctCount:
                self.teams[player] = 1
            else:
                self.teams[player] = 0
