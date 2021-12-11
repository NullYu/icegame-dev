# -*- coding: utf-8 -*-
#

from common.mod import Mod
import server.extraServerApi as serverApi
import logout
from awesomeScripts.modCommon import modConfig

'''
网络游戏进阶 demo mod。

通过mongo数据库，存取专属于脚本层的玩家存档
'''


@Mod.Binding(name = modConfig.LobbyServerModName, version = "0.1")
class LobbyMod(object):
	def __init__(self):
		pass
		
	@Mod.InitServer()
	def initServer(self):
		logout.info('===========================init_AwesomeServer_mod!===============================')
		self.server = serverApi.RegisterSystem(modConfig.Minecraft, modConfig.LobbyServerSystemName, modConfig.LobbyServerSystemClsPath)

	@Mod.DestroyServer()
	def destroyServer(self):
		logout.info('destroy_server===============')