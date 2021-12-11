# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import json
import random
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.redisPool as redisPool
import apolloCommon.commonNetgameApi as commonNetgameApi
import apolloCommon.mysqlPool as mysqlPool
mysqlPool.InitDB(30)

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()
initServerRule = False

# 在modMain中注册的Server System类
class deathmsgSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self,
                            self.OnAddServerPlayer)
        # self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerDieEvent",
        #                     self,
        #                     self.OnPlayerDie)

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

    def sendMsgToAll(self, msg):
        for player in serverApi.GetPlayerList():
            self.sendMsg(msg, player)
    #################################

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("lobbyutils", "lobbyutilsClient", 'TestRequest', self, self.OnTestRequest)

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        uid = data['uid']

        if not initServerRule:
            print '=====iniServerRule====='
            comp = serverApi.GetEngineCompFactory().CreateCommand(serverApi.GetLevelId())
            comp.SetCommand("/gamerule showdeathmessages false", playerId)

            initServerRule = True
            global initServerRule

    def OnPlayerDie(self, data):
        playerId = data['id']
        attackerId = data['attacker']
        playerNick = "§4"+lobbyGameApi.GetPlayerNickname(playerId)+"§3"
        attackerNick = "§4" + lobbyGameApi.GetPlayerNickname(attackerId) + "§3"

        killMsg = [
            "%s被%s击杀了！" % (playerNick, attackerNick),
            "%s向%s发起挑战，%s输得很惨" % (playerNick, attackerNick, playerNick),
            "%s被%s终结啦！" % (playerNick, attackerNick),
            "%s在遭到%s的追杀后根本停不下来" % (playerNick, attackerNick),
            "%s在经历%s的打压下四脚朝天" % (playerNick, attackerNick),
            "%s见到%s手上的利刃，绝望地闭上了眼睛" % (playerNick, attackerNick),
            "%s-.- .. .-.. .-.. . -..%s" % (attackerNick, playerNick),
            "%s还不是%s的对手" % (playerNick, attackerNick)
        ]
        suicideMsg = [
            "%s放弃了生命" % (playerNick,),
            "%s去了二次元" % (playerNick,),
            "%s感受到了游戏的特性" % (playerNick,),
            "%s在欢笑声中打出gg" % (playerNick,)
        ]

        if 'lobby' and 'practice' not in commonNetgameApi.GetServerType():
            if attackerId != '-1':
                self.sendMsgToAll(random.choice(killMsg))
            else:
                self.sendMsgToAll(random.choice(suicideMsg))