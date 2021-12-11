# -*- coding: utf-8 -*-

import client.extraClientApi as clientApi

ClientSystem = clientApi.GetClientSystemCls()

class ziClient(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),'OnLocalPlayerStopLoading', self, self.OnLocalPlayerStopLoading)

    def OnLocalPlayerStopLoading(self, data):
        comp = clientApi.GetEngineCompFactory().CreateTextBoard(data['playerId'])
        self.boardId = comp.CreateTextBoardInWorld("§b§lICE_GAME\n§f弓箭手作战\n§r§7游戏规则：\n努力击败对方所有敌人。击败所有敌人即可获得胜利\nBY Terrxx", (0.5, 0.4, 0.3, 1), (0, 0, 0, 0), True)
        comp.SetBoardPos(self.boardId, (0.5, 204, 0.5))
        print '=== zi init ==='

    def Destroy(self):
        pass