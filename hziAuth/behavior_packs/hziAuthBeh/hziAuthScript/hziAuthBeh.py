# -*- coding: utf-8 -*-
# @Author : uni_kevin(可乐)
import logging
import math

import mod.client.extraClientApi as clientApi

ClientSystem = clientApi.GetClientSystemCls()
EngineNamespace = clientApi.GetEngineNamespace()
EngineSystemName = clientApi.GetEngineSystemName()

class HziAuthBeh(ClientSystem):

    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        self.needReg = False
        self.mustAuth = True
        self.tick = 0
        self.ListenForEvent('HziAuth', 'HziAuthDev', 'AuthInit', self, self.AuthInit)
        self.ListenForEvent('HziAuth', 'HziAuthDev', 'SendRequest', self, self.SendRequest)
        self.ListenForEvent('HziAuth', 'HziAuthDev', 'AuthRequest', self, self.AuthRequest)
        self.ListenForEvent(EngineNamespace, EngineSystemName, 'UiInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent(EngineNamespace, EngineSystemName, 'OnScriptTickClient', self, self.OnScriptTickClient)

    def OnScriptTickClient(self):
        if self.tick < 30:
            self.tick += 1
            return
        else:
            self.tick = 0
        uiNode = clientApi.GetTopScreen()
        if self.needReg and (not uiNode or uiNode.__class__.__name__ != 'HziAuthUI'):
            clientApi.PushScreen('HziAuth', 'HziAuth')

    def AuthInit(self, e):
        self.needReg = e['needReg']
        self.mustAuth = e['mustAuth']
        # self.UnListenAllEvents()

    def SendRequest(self, e):
        uiNode = clientApi.GetUI('HziAuth', 'HziAuth')
        if uiNode:
            uiNode.SendRequest(e)

    def AuthRequest(self, e):
        uiNode = clientApi.GetUI('HziAuth', 'HziAuth')
        if uiNode:
            uiNode.AuthRequest(e)

    def OnUIInitFinished(self, e):
        clientApi.RegisterUI('HziAuth', 'HziAuth', 'hziAuthScript.hziAuthUI.HziAuthUI', 'hzi_auth.main')
        self.NotifyToServer('OnUIInitFinished', {'client': clientApi.GetLocalPlayerId()})
