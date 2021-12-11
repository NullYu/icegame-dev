# -*- coding: utf-8 -*-
#
import client.extraClientApi as clientApi
ClientSystem = clientApi.GetClientSystemCls()
import modCommon.playerData as playerData
from awesomeScripts import logger
from awesomeScripts.modCommon import modConfig

class AwesomeClient(ClientSystem):
	def __init__(self,namespace,systemName):
		print 'AwesomeClient', namespace,systemName
		ClientSystem.__init__(self,namespace,systemName)
		#self.mEventMgr = EventManger()  # 事件系统
		self.mSureUINode = None
		# 注册事件
		# 监听自定义事件，用于初始化玩家数据
		self.ListenForEvent(modConfig.Minecraft, modConfig.LobbyServerSystemName,
		                    modConfig.LoginResponseEvent, self, self.OnLoginResponse)
		self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
		                    'OnLocalPlayerStopLoading', self, self.OnOnLocalPlayerStopLoading)
		self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
		                    'UiInitFinished', self, self.OnUiInitFinished)
		self.my_player_data = None
	
	def OnOnLocalPlayerStopLoading(self,args):
		'''
		请求登录到服务端，获取玩家数据
		'''
		logger.info("OnOnLocalPlayerStopLoading : %s", args)
		playerId = clientApi.GetLocalPlayerId()
		loginData = {}
		loginData['id'] = playerId
		self.NotifyToServer(modConfig.LoginRequestEvent, loginData)

	def OnUiInitFinished(self, args):
		'''
		初始化UI
		'''
		print 'OnUiInitFinished', args
		self.InitUi()

	def OnLoginResponse(self, args):
		'''
		初始化玩家数据，然后开始客户端逻辑
		'''
		logger.info("OnLoginResponse : %s", args)
		player_info = args
		self.my_player_data = playerData.PlayerData()
		self.my_player_data.initPlayer(player_info['player_id'], player_info)

	def InitUi(self):
		#开发者在这里初始化ui，开始客户端操作。
		# 注册UI 详细解释参照:《UI API》
		clientApi.RegisterUI(modConfig.Minecraft, modConfig.SureUIName, modConfig.SureUIPyClsPath,
		                     modConfig.SureUIScreenDef)
		# 创建UI 详细解释参照《UI API》
		clientApi.CreateUI(modConfig.Minecraft, modConfig.SureUIName, {"isHud": 1})
		self.mSureUINode = clientApi.GetUI(modConfig.Minecraft, modConfig.SureUIName)
		if self.mSureUINode:
			self.mSureUINode.Init()
			print 'create ui success'
		else:
			logger.error("create ui %s failed!")
	
	def Destroy(self):
		'''
		卸下 mod时会执行Destroy 函数。用于清理现场。
		'''
		# 注销事件
		self.my_player_data = None