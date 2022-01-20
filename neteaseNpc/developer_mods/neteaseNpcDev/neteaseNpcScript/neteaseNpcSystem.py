# -*- coding: utf-8 -*-
#
import server.extraServerApi as serverApi

ServerSystem = serverApi.GetServerSystemCls()
import json
import npcManager
import lobbyGame.netgameApi as netgameApi
import apolloCommon.commonNetgameApi as commonNetgameApi


# -----------------------------------------------------------------------------------
class NpcServerSystem(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        print '--------NpcServer====start!!!!!~~~~~'
        self.mNpcMgr = npcManager.NpcManager(self)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "EntityBeKnockEvent", self,
                            self.OnNpcTouched)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerDieEvent", self,
                            self.OnPlayerDie)
        self.ListenForEvent("neteaseNpc", "npcClient", "ClickSureFromClientEvent", self, self.OnClickSureGame)

        if commonNetgameApi.GetServerType() == 'lobby':
            identifier = "minecraft:npc"
            rot = (0, 180)
            dimensionId = 0

            self.RegisterExtraNpc(identifier, "§l§2纯净生存服\n§r§6队列系统测试中\n§c漏洞补丁测试中", dimensionId, (105.5, 188, 123.5), rot,
                                  self.CbManhunt)
            self.RegisterExtraNpc(identifier, "§l§e起床战争§r§b点击进入大厅", dimensionId, (109.5, 188, 123.5), rot,
                                  self.CbBwEntrance)
            self.RegisterExtraNpc(identifier, "§l§e密室§d杀手§r§b[测试版]", dimensionId, (98.5, 188, 125.5), rot, self.CbMm)
            self.RegisterExtraNpc(identifier, "§l§cTNT§4跑酷§r§b[测试版]", dimensionId, (116.5, 188,125.5), rot, self.CbTntr)

            self.RegisterExtraNpc(identifier, "§l§b经典模式\n§r§e点击游玩", dimensionId, (1000.5, 202, 10.5), rot, self.CbBw)
            self.RegisterExtraNpc(identifier, "§l§6炮爷模式\n§r§b点击游玩", dimensionId, (995.5, 202, 9.5), rot, self.CbBwBomb)
            self.RegisterExtraNpc(identifier, "§l§e2队8人§c世纪大战§r§7[测试版]\n§r§b点击游玩", dimensionId, (1005.5, 202, 9.5),
                                  rot, self.CbBw2)

            self.RegisterExtraNpc(identifier, "§l§c返回主城", dimensionId, (1000.5, 201, -8.5), (180, 180), self.lobby)
            self.RegisterExtraNpc(identifier, "§l§6Duels§1Practice", dimensionId, (120.5, 188, 123.5), rot, self.CbDuelsEntrance)

    # lobby @ 107, 188, 105

    def CbT1(self, a, p):
        rankSystem = serverApi.GetSystem('rank', 'rankSystem')
        rankSystem.OnCommand({
            'cancel': None,
            'entityId': p,
            'command': '/rank t1'
        })

    def lobby(self, a, p):
        self.setPos(p, (107, 188, 105))

    def setPos(self, playerId, pos):
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        re = comp.SetFootPos(pos)
        return re

    def CbBwEntrance(self, a, p):
        self.setPos(p, (1000, 201, 0))

    def CbDuelsEntrance(self, a, playerId):
        menuSystem = serverApi.GetSystem('menu', 'menuSystem')
        menuSystem.NotifyToClient(playerId, 'OpenMenuEvent', 1)

    def CbManhunt(self, entityId, playerId):
        utilsSystem = serverApi.GetSystem('utils', 'utilsSystem')
        utilsSystem.SendPlayerToSurv(playerId)

    def CbBw(self, entityId, playerId):
        menuSystem = serverApi.GetSystem('menu', 'menuSystem')
        menuSystem.ApiRequestBwMatchmaking(playerId, 'game_bw')

    def CbBw2(self, entityId, playerId):
        menuSystem = serverApi.GetSystem('menu', 'menuSystem')
        menuSystem.ApiRequestBwMatchmaking(playerId, 'game_2bw8')

    def CbMm(self, a, p):
        menuSystem = serverApi.GetSystem('menu', 'menuSystem')
        menuSystem.ApiRequestBwMatchmaking(p, 'game_mm')

    def CbTntr(self, a, p):
        menuSystem = serverApi.GetSystem('menu', 'menuSystem')
        menuSystem.ApiRequestBwMatchmaking(p, 'game_tntr')

    def CbBwBomb(self, entityId, playerId):
        menuSystem = serverApi.GetSystem('menu', 'menuSystem')
        menuSystem.ApiRequestBwMatchmaking(playerId, 'game_bwBomb')

    def OnPlayerDie(self, args):
        '''
		玩家死亡，对话框消失
		'''
        playerId = args['id']
        data = {"playerId": playerId}
        self.NotifyToClient(playerId, "PlayerDieFromServerEvent", data)

    def OnNpcBeKnocked(self, entityId, playerId, gameType):
        print "OnNpcBeKnocked entityId={} playerId={} gameType={}".format(entityId, playerId, gameType)

    def RegisterExtraNpc(self, identifier, name, dimensionId, pos, rot, callbackFunc):
        self.mNpcMgr.RegisterExtraNpc(identifier, name, dimensionId, pos, rot, callbackFunc)

    def DeleteExtraNpc(self, entityId):
        npcData = self.mNpcMgr.GetNpcData(entityId)
        if not npcData:
            return
        self.DestroyEntity(entityId)

    def OnNpcTouched(self, args):
        '''
		点击npc回调函数。
		'''
        npcEntityId = args.get('entityId')
        npcData = self.mNpcMgr.GetNpcData(npcEntityId)
        playerId = args.get('srcId')
        if not npcData:
            return
        # 使用API注册的NPC
        if npcData.mKnockStyle == "onlyFunc":
            npcData.mDefinedCallback(npcData.mEntityId, playerId)
            return
        # 配置了回调指定mod的函数的NPC
        if npcData.mKnockStyle == "systemFunc":
            tarSystem = serverApi.GetSystem(npcData.mDefinedModName, npcData.mDefinedSystemName)
            if not tarSystem:
                return
            tarFunc = getattr(tarSystem, npcData.mDefinedFuncName, None)
            if not tarFunc or not callable(tarFunc):
                return
            args = [npcData.mEntityId, playerId]
            if npcData.mDefinedFuncArgs:
                args.extend(npcData.mDefinedFuncArgs)
            apply(tarFunc, args)
            return
        # 默认的实现转服逻辑的NPC
        if npcData.mIsTalk == True:
            data = {'aimServer': npcData.mTransferServerArgs, 'playerId': playerId, 'talkContent': npcData.mTalkContent,
                    "npcName": npcData.mName}
            self.NotifyToClient(playerId, "CheckSureFromServerEvent", data)
        else:
            netgameApi.TransferToOtherServer(playerId, npcData.mTransferServerArgs)

    def OnClickSureGame(self, args):
        '''
		客户端点击确定，切服
		'''
        server = args["aimServer"]
        netgameApi.TransferToOtherServer(args['playerId'], server)

    def Destroy(self):
        self.UnListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "EntityBeKnockEvent",
                              self, self.OnNpcTouched)
        self.UnListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerDieEvent", self,
                              self.OnPlayerDie)
        self.UnListenForEvent("neteaseNpc", "npcClient", "ClickSureFromClientEvent", self, self.OnClickSureGame)
