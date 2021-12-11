# -*- coding: utf-8 -*-

from common.mod import Mod
import server.extraServerApi as serverApi
import client.extraClientApi as clientApi
from mod_log import engine_logger as logger

@Mod.Binding(name="bow", version="0.1")
class LobbyServerMod(object):
    def __init__(self):
        pass

    @Mod.InitServer()
    def initServer(self):
        logger.info('init bow_game by Terrxx')
        self.lobbyServer = serverApi.RegisterSystem("bow", "bowSystem","bowScript.bowSystem.bowServerSys")

    @Mod.DestroyServer()
    def destroyServer(self):
        pass

    @Mod.InitClient()
    def initClient(self):
        self.lobbyClient = clientApi.RegisterSystem("bow", "ziClient","bowScript.ziClientSystem.ziClient")

    @Mod.DestroyClient()
    def destroyClient(self):
        pass