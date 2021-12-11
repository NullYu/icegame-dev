from common.mod import Mod
import client.extraClientApi as clientApi
from awesomeScripts.modCommon import modConfig

@Mod.Binding(name = modConfig.LobbyClientModName, version = "0.1")
class LobbyMod(object):
	def __init__(self):
		pass

	@Mod.InitClient()
	def initClient(self):
		print '===========================init_awesome_mod!==============================='
		self.client = clientApi.RegisterSystem(modConfig.Minecraft,modConfig.LobbyClientSystemName,modConfig.LobbyClientSystemClsPath)
		
	@Mod.DestroyClient()
	def destroyClient(self):
		pass
