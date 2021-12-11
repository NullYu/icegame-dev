# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi
from mod.client.ui.screenNode import ScreenNode
from mod.client.ui.screenController import ViewBinder, ViewRequest

# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()


# 在modMain中注册的Client System类
class utilsClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        print '###__init__ utilsClient'
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent('utils', 'utilsSystem', 'SetPlayerSpectateEvent', self, self.OnSetPlayerSpectate)
        self.ListenForEvent('utils', 'utilsSystem', 'ShowBannerEvent', self, self.OnShowBanner)
        self.ListenForEvent('utils', 'utilsSystem', 'SetHideNameEvent', self, self.OnSetHideName)
        self.ListenForEvent('utils', 'utilsSystem', 'TextBoardEvent', self, self.OnTextBoard)
        self.ListenForEvent('utils', 'utilsSystem', 'StartSpecEvent', self, self.OnStartSpec)
        self.ListenForEvent('utils', 'utilsSystem', 'ChangeSpecTargetEvent', self, self.OnChangeSpecTarget)
        self.isSpectate = False
        self.isDoneLoading = False

    def OnSetHideName(self, isHide):
        print 'SET HIDE NAME isHide=%s' % isHide
        clientApi.HideNameTag(isHide)

    def OnGetIp(self, uid):
        response = {
            'uid': uid,
            'ip': clientApi.GetIP()
        }
        print 'CALL OnGetIp response=%s' % (response,)
        self.NotifyToServer("ReturnIpEvent", response)

    def OnUIInitFinished(self, args):
        self.isDoneLoading = True
        uiRegisterSuccess = clientApi.RegisterUI('utils', 'utilsUI', 'utilsScript.utilsClientUI.utilsScreen', 'utilsUI.main')
        print 'utilsUI Register UI success=%s' % (uiRegisterSuccess,)
        clientApi.CreateUI('utils', 'utilsUI', {'isHud': 1})
        self.utilsUINode = clientApi.GetUI('utils', 'utilsUI')
        if self.utilsUINode:
            self.utilsUINode.InitScreen()
            print 'utilsUINODE.InitScreen node=', str(self.utilsUINode)
        else:
            print 'FAILED TO utilsUINODE.InitScreen!!! utilsUINODE=', str(self.utilsUINode)


        self.NotifyToServer("PlayerLoadedEvent", clientApi.GetLocalPlayerId())

    def OnShowBanner(self, data):
        playerId = data['playerId']
        nickname = data['nickname']
        music = data['musicName']
        self.utilsUINode.ShowBanner(nickname, music, bool(music), playerId == clientApi.GetLocalPlayerId())

    def OnChangeSpecTarget(self, data):
        specTarget = data['playerId']
        camComp = clientApi.GetEngineCompFactory().CreateCamera(clientApi.GetLevelId())
        camComp.SetCameraBindActorId(specTarget)

        vcomp = clientApi.GetEngineCompFactory().CreatePlayerView(clientApi.GetLocalPlayerId())
        vcomp.SetPerspective(0)

    def OnStartSpec(self, data):
        isSpec = data['isSpec']
        if isSpec:
            specTarget = data['playerId']

            timerComp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
            timerComp.SetRenderLocalPlayer(False)

            camComp = clientApi.GetEngineCompFactory().CreateCamera(clientApi.GetLevelId())
            camComp.DepartCamera()
            camComp.SetCameraBindActorId(specTarget)

            vcomp = clientApi.GetEngineCompFactory().CreatePlayerView(clientApi.GetLocalPlayerId())
            vcomp.SetPerspective(0)

            comp = clientApi.GetEngineCompFactory().CreateOperation(clientApi.GetLevelId())
            comp.SetCanDrag(False)
            comp.SetCanJump(False)
            comp.SetCanMove(False)
            comp.SetCanOpenInv(False)
            comp.SetCanPause(False)
            comp.SetCanPerspective(False)

            clientApi.HideHudGUI(True)
            clientApi.HideInteractGui(True)

            self.utilsUINode.ShowSpecUi({
                'isSpec': True,
                'nickname': data['nickname']
            })

        else:
            camComp = clientApi.GetEngineCompFactory().CreateCamera(clientApi.GetLevelId())
            camComp.UnDepartCamera()
            camComp.SetCameraBindActorId(clientApi.GetLocalPlayerId())

            comp = clientApi.GetEngineCompFactory().CreateOperation(clientApi.GetLevelId())
            comp.SetCanDrag(True)
            comp.SetCanJump(True)
            comp.SetCanMove(True)
            comp.SetCanOpenInv(True)
            comp.SetCanPause(True)
            comp.SetCanPerspective(True)
            clientApi.HideHudGUI(False)
            clientApi.HideInteractGui(False)

            timerComp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
            timerComp.SetRenderLocalPlayer(True)

            self.utilsUINode.ShowSpecUi({
                'isSpec': False
            })

    def OnSetPlayerSpectate(self, args):
        self.isSpectate = args['value']
        noInteract = args['interact']

        clientApi.HideSlotBarGui(self.isSpectate)
        clientApi.HideChangePersonGui(self.isSpectate)
        clientApi.HideHealthGui(self.isSpectate)
        clientApi.HideArmorGui(self.isSpectate)
        clientApi.HideHungerGui(self.isSpectate)

        comp = clientApi.GetEngineCompFactory().CreateOperation(clientApi.GetLevelId())
        comp.SetCanAttack(not self.isSpectate)
        print 'setting CanAttack to %s' % (not self.isSpectate,)

        # NoInteract specifics
        if noInteract:
            comp.SetCanOpenInv(not self.isSpectate)
            comp.SetCanChat(not self.isSpectate)

    def OnTextBoard(self, data):

        if not self.isDoneLoading:
            return

        isShow = data['show']
        content = data['content']

        self.utilsUINode.TextBoard(isShow, content)

    def ReturnToServer(self, args):
        response = args
        response['playerId'] = clientApi.GetLocalPlayerId()
        self.NotifyToServer("ActionEvent", args)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
