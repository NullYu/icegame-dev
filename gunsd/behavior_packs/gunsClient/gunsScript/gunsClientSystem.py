# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi
import gunsScript.gunsClientConsts as c
from mod.client.ui.screenNode import ScreenNode
from mod.client.ui.screenController import ViewBinder, ViewRequest
# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()
compFactory = clientApi.GetEngineCompFactory()

# 在modMain中注册的Client System类
class gunsClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        # self.ListenForEvent('test', 'testSystem', 'ShowTestUiEvent', self, self.OnShowTestUi)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'UiInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent('guns', 'gunsSystem', 'LoadNewEquipmentEvent', self, self.OnLoadNewEquipment)

        self.showFirstSign = False
        self.c = c

    def OnUIInitFinished(self, args):
        uiRegisterSuccess = clientApi.RegisterUI('guns', 'gunsUI', 'gunsScript.gunsClientUI.gunsScreen', 'gunsUI.main')
        self.showFirstguns = True
        print 'Register UI success=%s' % (uiRegisterSuccess,)
        clientApi.CreateUI('guns', 'gunsUI', {'isHud': 1})
        self.mChillUINode = clientApi.GetUI('guns', 'gunsUI')
        if self.mChillUINode:
            self.mChillUINode.InitScreen()
            print 'gunsUINODE.InitScreen node=', str(self.mChillUINode)
        else:
            print 'FAILED TO gunsUINODE.InitScreen!!! gunsUINODE=', str(self.mChillUINode)

    def ShowGunsUI(self, args):
        print 'CALL OnShowSignUi', str(args)

        self.mChillUINode.ShowUi()

    def OnLoadNewEquipment(self, data):
        uiNode = self.mChillUINode

        uiNode.gunId = data['id']
        uiNode.ammo = data['ammo']
        uiNode.reserveAmmo = data['reserveAmmo']
        uiNode.maxAmmo = data['maxAmmo']
        uiNode.fireMode = data['firemode']

        if data['zoom']:
            uiNode.scopeType = 1
        elif data['scope']:
            uiNode.scopeType = 2
        else:
            uiNode.scopeType = 0

        uiNode.UpdateData()

    def ReturnToServer(self, args):
        response = args
        response['playerId'] = clientApi.GetLocalPlayerId()
        self.NotifyToServer("ClientActionEvent", args)

    def PlayMusicToPlayer(self, playerId, musicId):
        print 'CALL PlayMusicToPlayer playerId=%s musicId=%s type=%s' % (playerId, musicId, type)
        args = {
            'playerId': playerId,
            'musicId': musicId,
        }
        self.NotifyToClient(playerId, "PlayMusicEvent", args)

    def PlayMusic(self, musicId):
        print 'playing %s' % musicId
        playerId = clientApi.GetLocalPlayerId()
        musicClientSystem = clientApi.GetSystem("music", "musicClient")
        musicClientSystem.OnPlayMusic({
            'playerId': playerId,
            'musicId': musicId
        })
    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
