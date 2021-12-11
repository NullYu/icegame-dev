# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.commonNetgameApi as commonNetgameApi

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

cps = {}

# 在modMain中注册的Server System类
class gameutilsServerSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()
        lobbyGameApi.ShieldPlayerJoinText(True)

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

    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self,
                            self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DestroyBlockEvent",
                            self, self.OnServerPlayerTryDestroyBlock)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerAttackEntityEvent",
                            self,
                            self.OnPlayerAttackEntity)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerDieEvent",
                            self,
                            self.OnPlayerDie)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ActuallyHurtServerEvent",
                            self,
                            self.OnActuallyHurtServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AttackAnimBeginServerEvent",
                            self,
                            self.OnAttackAnimBeginServer)

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
        setdiff_result = comp.SetGameDifficulty(2)
        def a():
            del cps
            cps = {}
            global cps
        commonNetgameApi.AddRepeatedTimer(1, a)
        
    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("gameutils", "gameutilsClient", 'TestRequest', self, self.OnTestRequest)

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        uid = data['uid']

    def OnDestroyBlock(self, data):
        pos = (data['x'], data['y'], data['z'])
        playerId = data['playerId']
        name = data['fullName']
        aux = data['auxData']
        blockDict = {
            'name': name,
            'aux': aux
        }
        comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId)
        comp.SetBlockNew(pos, blockDict, 0, 0)

    def OnPlayerAttackEntity(self, data):
        pass
    def OnPlayerDie(self, data):
        playerId = data['id']
        attacker = data['attacker']

        comp = serverApi.GetEngineCompFactory().CreateCommand(serverApi.GetLevelId())
        comp.SetCommand("/summon lightning_bolt", playerId)

    def OnActuallyHurtServer(self, data):
        playerId = data['entityId']
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        playerPos = comp.GetPos()

    def OnAttackAnimBeginServer(self, data):
        playerId = data["id"]
        if playerId in cps:
            cps[playerId] += 1
            self.sendTitle("§l§bCPS: "+cps[playerId], 3, playerId)
        else:
            cps[playerId] = 1
            self.sendTitle("§l§bCPS: " + cps[playerId], 3, playerId)