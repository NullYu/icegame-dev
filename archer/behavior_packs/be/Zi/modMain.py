# -*- coding: utf-8 -*-

from common.mod import Mod
import client.extraClientApi as clientApi


@Mod.Binding(name="zi", version="0.1")
class LobbyBehaviorMod(object):
    def __init__(self):
        pass

    @Mod.InitClient()
    def initClient(self):
        self.lobbyClient = clientApi.RegisterSystem("zi", "ziClient","Zi.ziClientSystem.ziClient")

    @Mod.DestroyClient()
    def destroyClient(self):
        pass