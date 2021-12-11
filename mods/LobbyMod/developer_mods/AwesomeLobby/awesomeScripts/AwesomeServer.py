# -*- coding: utf-8 -*-
#
import server.extraServerApi as serverApi
ServerSystem = serverApi.GetServerSystemCls()
import lobbyGame.netgameApi as netgameApi
import modCommon.playerData as playerData
from awesomeScripts.modCommon.coroutineMgrGas import CoroutineMgr
from awesomeScripts.modCommon import modConfig
from awesomeScripts.modCommon.modConfig import TipType
from mod_log import engine_logger as logger
from awesomeScripts.mysqlOperation import MysqlOperation

class AwesomeServer(ServerSystem):
	def __init__(self, namespace, systemName):
		ServerSystem.__init__(self, namespace, systemName)
		logger.info('--------AwesomeServer====start!!!!!~~~~~')
		self.mysqlMgr = MysqlOperation()

		netgameApi.SetUseDatabaseSave(True, "awesome", 120)#定时存档，时间间隔是120s
		netgameApi.SetNonePlayerSaveMode(True)
		#主城模式打开
		netgameApi.SetCityMode(True)
		#设置为创造模式 0生存模式，1创造模式，2冒险模式
		netgameApi.SetLevelGameType(2)
		# 注册事件
		self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), modConfig.AddServerPlayerEvent, self, self.OnAddServerPlayer)
		self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), modConfig.savePlayerDataEvent,self, self.OnSavePlayerData)
		self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), modConfig.savePlayerDataOnShutDownEvent,self, self.OnSavePlayerData)
		self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), modConfig.DelServerPlayerEvent, self, self.OnDelServerPlayer)
		self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), modConfig.ServerWillShutDownEvent,self, self.OnServerWillShutDown)
		self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), modConfig.ServerChatEvent, self,self.OnServerChat)
		self.ListenForEvent(modConfig.Minecraft, modConfig.LobbyClientSystemName, modConfig.OnSureGameEvent, self, self.OnSureGame)
		self.ListenForEvent(modConfig.Minecraft, modConfig.LobbyClientSystemName, modConfig.OnCancelGameEvent, self, self.OnCancelGame)
		self.ListenForEvent(modConfig.Minecraft, modConfig.ServiceSystemName, modConfig.MatchResultEvent, self, self.OnMatchResultEvent)
		self.ListenForEvent(modConfig.Minecraft, modConfig.ServiceSystemName, modConfig.MatchNumEvent, self, self.OnMatchNum)
		self.ListenForEvent(modConfig.Minecraft, modConfig.MasterSystemName, modConfig.GetUserInfoRequestEvent, self, self.OnGetUserInfoRequest)
		self.ListenForEvent(modConfig.Minecraft, modConfig.MasterSystemName, modConfig.GetPlayerNumOfGameRequestEvent, self, self.OnGetPlayerNumOfGame)
		self.ListenForEvent(modConfig.Minecraft, modConfig.LobbyClientSystemName, modConfig.LoginRequestEvent, self, self.OnLoginRequest)
		# 玩家对象管理
		self.player_map = {}
		#玩家player id到uid的映射
		self.playerid2uid = {}
		
		self.transferPlayerQueue = []
		#玩家初始在dimension 4，需要创建dimension
		dimensionComp = self.CreateComponent(serverApi.GetLevelId(), "Minecraft", "dimension")
		dimensionComp.CreateDimension(4)

	def Destroy(self):
		'''
		服务器退出会调用Destroy函数，主要做清理工作
		'''
		# 清空内存数据
		self.player_map = {}
		self.playerid2uid = {}
		# 结束数据库线程池，确保相关异步任务全部执行完。
		self.mysqlMgr.Destroy()
	#-------------------------------------------------------------------------------------
	
	# 监听ServerChatEvent的回调函数
	def OnServerChat(self, args):
		#设置玩家操控所有指令
		logger.info("OnServerChat {}".format(args))
		if args["message"] == "op":
			username = args.get('username', '')
			commandComp = self.CreateComponent(serverApi.GetLevelId(), modConfig.Minecraft, "command")
			commandComp.SetCommand('op %s' % username)
	
	def OnAddServerPlayer(self, args):
		'''
		添加玩家的监听函数
		'''
		playerId = args.get('id','-1')
		uid = netgameApi.GetPlayerUid(playerId)
		self.playerid2uid[playerId] = uid
		logger.info("player login.uid: %s",uid)
		self.mysqlMgr.QueryPlayerData(playerId,uid,lambda data: self.QuerySinglePlayerCallback(playerId, uid, data))

	def QuerySinglePlayerCallback(self, player_id, uid, data):
		'''
		回调函数。若玩家存在，则注册玩家；否则记录玩家信息
		'''
		# 数据库请求返回时，玩家已经主动退出了
		if not self.playerid2uid.has_key(player_id):
			return
		if not data:# 找不到玩家数据，注册一个新玩家
			nickname = netgameApi.GetPlayerNickname(player_id)
			data = playerData.PlayerData.getNewPlayerInfo(uid, nickname)
			self.InsertPlayerData(player_id, uid)
		#记录玩家数据
		player = playerData.PlayerData()
		if isinstance(data,tuple):
			data = player.changeMysqlTupleToPlayerDict(data)
		player.initPlayer(player_id, data)
		#刷新玩家登录时间
		player.refreshLoginTime()
		self.player_map[uid] = player

	def OnLoginRequest(self, data):
		'''
		玩家登录逻辑
		'''
		player_id = data['id']
		uid = netgameApi.GetPlayerUid(player_id)
		# 设置玩家位置和维度
		comp = serverApi.GetEngineCompFactory().CreateDimension(player_id)
		comp.ChangePlayerDimension(4, (1395.664, 5.2, 51.441))
		CoroutineMgr.StartCoroutine(self._DoSendLoginResponseData(player_id, uid))

	def _DoSendLoginResponseData(self, player_id, uid):
		'''
		将玩家数据推送给客户端。若还没从db获取玩家数据，则延迟5帧再试
		'''
		if uid in self.player_map:
			player = self.player_map[uid]
			event_data = player.toSaveDict()
			event_data['player_id'] = player_id
			self.NotifyToClient(player_id, modConfig.LoginResponseEvent, event_data)
			return
		yield -5

	def InsertPlayerData(self, player_id, uid):
		'''
		把玩家数据插入db
		'''
		nickname = netgameApi.GetPlayerNickname(player_id)
		new_player_data = playerData.PlayerData.getNewPlayerInfo(uid, nickname)
		self.mysqlMgr.InsertPlayerData(player_id, uid, new_player_data)

	def Update(self):
		'''
		每帧执行。
		'''
		CoroutineMgr.Tick()

	def OnSavePlayerData(self, args):
		'''
		把玩家数据存档。这个函数一定要调用save_player_data_result函数，把存档状态告知引擎。
		'''
		uid = int(args["playerKey"])
		cpp_callback_idx = int(args["idx"])
		player_data = self.player_map.get(uid, None)
		if not player_data:
			#告知引擎，存档状态。注意传入回调函数id
			netgameApi.SavePlayerDataResult(cpp_callback_idx, True)
		def _SavePlayerCb(args):
			ret = args
			if ret:
				netgameApi.SavePlayerDataResult(cpp_callback_idx, True)
			else:
				netgameApi.SavePlayerDataResult(cpp_callback_idx, False)
		self.SavePlayerByUid(uid, _SavePlayerCb)

	def SavePlayerByUid(self, uid, cb = None):
		'''
		保存玩家数据
		'''
		player = self.player_map.get(uid, None)
		if not player:
			return
		player_dict = player.toSaveDict()
		self.mysqlMgr.SavePlayerByUid(uid,player_dict,cb)

	def OnDelServerPlayer(self, args):
		'''
		清除玩家内存数据。
		'''
		logger.info("OnDelServerPlayer {}".format(args))
		playerId = args.get('id','-1')
		logger.info("OnDelServerPlayer player id=%s"% playerId)
		uid = self.playerid2uid.get(playerId, None)
		if not uid:
			return
		self.SavePlayerByUid(uid)
		del self.playerid2uid[playerId]
		if uid in self.player_map:
			del self.player_map[uid]
		#玩家离线，把自己playerId在待传送队列里清掉
		if playerId in self.transferPlayerQueue:
			self.transferPlayerQueue.remove(playerId)
		#玩家离线，告诉server把自己从匹配队清掉
		request_data = {'uid': uid, 'player_id': playerId}
		self.RequestToService(modConfig.awesome_match, modConfig.RequestMatchCancel, request_data)
		

	def OnServerWillShutDown(self, args):
		logger.info("OnServerWillShutDown {}".format(args))
		# 即将关机，先给所有还在线玩家挂一个存档任务
		for uid, player in self.player_map.iteritems():
			self.SavePlayerByUid(uid)
		self.mysqlMgr.Destroy()

	def OnNpcTouched(self, npc_entity_id, player_entity_id, game_type):
		'''
		点击npc回调函数。
		'''
		print 'OnNpcTouched', npc_entity_id, player_entity_id, game_type
		uid = self.playerid2uid[player_entity_id]
		if game_type == 'gameA':
			logger.info("%s touch NPC gameA",player_entity_id)
			#请求gameA玩家人数
			request_data = {'game': 'gameA', 'player_id': player_entity_id,'uid': uid,'client_id':netgameApi.GetServerId()}
			self.NotifyToMaster(modConfig.GetPlayerNumOfGameEvent,request_data)
		elif game_type == 'gameB':
			logger.info("%s touch NPC gameB",player_entity_id)
			#请求gameB玩家人数
			request_data = {'game': 'gameB', 'player_id': player_entity_id, 'uid': uid,
							'client_id': netgameApi.GetServerId()}
			self.NotifyToMaster(modConfig.GetPlayerNumOfGameEvent, request_data)
		elif game_type == 'gameC':
			logger.info("%s touch NPC gameC",player_entity_id)
			# 请求gameC匹配队列人数
			request_data = {'uid': uid, 'player_id': player_entity_id, 'game': 'gameC'}
			self.RequestToService(modConfig.awesome_match, modConfig.RequestMatchNum, request_data)
			
	def OnGetPlayerNumOfGame(self,args):
		'''
		告诉客户端，显示玩家数量的提示页面
		'''
		logger.info("OnGetPlayerNumOfGame {}".format(args))
		self.NotifyToClient(args['player_id'], modConfig.SureEnterGameEvent, args)
	
	def OnMatchNum(self,args):
		'''
		告诉客户端，显示匹配队列人数的提示页面
		'''
		logger.info("OnMatchNum {}".format(args))
		self.NotifyToClient(args['player_id'], modConfig.SureMatchGameEvent, args)
		
	def OnSureGame(self,args):
		'''
		切服逻辑，如果是gameA和gameB则直接传去对应服，如果是gameC则加入匹配队列
		:param args:
		:return:
		'''
		logger.info("OnSureGame {}".format(args))
		if args['game'] == "gameA":
			netgameApi.TransferToOtherServer(args['playerId'], "gameA")
		elif args['game'] == "gameB":
			netgameApi.TransferToOtherServer(args['playerId'], "gameB")
		elif args['game'] == "gameC":
			playerId = args['playerId']
			uid = self.playerid2uid[playerId]
			levelcomp = self.CreateComponent(playerId, modConfig.Minecraft, "lv")
			playerLevel = levelcomp.GetPlayerLevel()
			if playerLevel >= 0:#大于0级才能匹配
				request_data = {'uid': uid, 'player_id': playerId,'game':args["game"]}
				self.RequestToService(modConfig.awesome_match, modConfig.RequestMatch, request_data)
				tipData = {'tipType' : TipType.matching} #1匹配中
				self.NotifyToClient(playerId, modConfig.MatchResultTip, tipData)
			else:
				tipData = {'tipType': TipType.levelNotEnough} #0等级不够
				self.NotifyToClient(playerId, modConfig.MatchResultTip, tipData)
			
	def OnCancelGame(self,args):
		'''
		取消匹配，暂时只有gameC取消匹配的功能
		:return:
		'''
		if args['game'] == "gameC":
			playerId = args['playerId']
			uid = self.playerid2uid[playerId]
			request_data = {'uid': uid, 'player_id': playerId,'game':args["game"]}
			self.RequestToService(modConfig.awesome_match, modConfig.RequestMatchCancel, request_data)

	def OnMatchResultEvent(self, args):
		'''
		处理匹配结果。切到指定服务器。
		'''
		logger.info("OnMatchResultEvent {}".format(args))
		playerId = args['player_id']
		desc_game = args['desc_game']
		if args['game'] == 'gameC':
			#如果是gameC则延时1S传送
			tipData = {'tipType': TipType.toTransfer}  # 2 即将传送
			self.NotifyToClient(playerId, modConfig.MatchResultTip, tipData)
			self.transferPlayerQueue.append(playerId)
			CoroutineMgr.StartCoroutine(self.Transfer2Server(playerId, desc_game))
		
	def Transfer2Server(self,playerId,descGame):
		'''
		把玩家传送至对应的服
		:return:
		'''
		yield -30#延迟30帧，也即1s
		#判断玩家是否在待传送队列里，若玩家中途下线，则不作处理
		if playerId in self.transferPlayerQueue:
			logger.info("%s go to %s", playerId,descGame)
			netgameApi.TransferToOtherServerById(playerId, descGame)
			self.transferPlayerQueue.remove(playerId)
	
	def OnGetUserInfoRequest(self, args):
		'''
		获取玩家数据。
		'''
		uid = args['uid']
		client_id = args['client_id']
		player_data = self.player_map.get(uid, None)
		if not player_data:
			self.mysqlMgr.QueryPlayerData(uid, uid, lambda data: self._OnGetUserInfoRequestCb(client_id, data))
		else:
			self._GetUserInfoResponse(client_id, player_data.toSaveDict())

	def _OnGetUserInfoRequestCb(self, client_id, record):
		'''
		回调函数，处理db操作结果，把玩家数据告知master。
		'''
		if record:
			player_data = playerData.PlayerData()
			if isinstance(record, tuple):
				record = player_data.changeMysqlTupleToPlayerDict(record)
			player_data.initPlayer(-1, record)
			self._GetUserInfoResponse(client_id, player_data.toSaveDict())
		else:
			self._GetUserInfoResponse(client_id, {})

	def _GetUserInfoResponse(self, client_id, player_info):
		'''
		玩家数据告知master。
		'''
		response_data = {'client_id' : client_id, 'user_info' : player_info}
		self.NotifyToMaster(modConfig.GetUserInfoResponseEvent, response_data)

