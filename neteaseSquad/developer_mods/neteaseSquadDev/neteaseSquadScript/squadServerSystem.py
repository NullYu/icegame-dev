# -*- coding: utf-8 -*-

import json
import lobbyGame.netgameApi as netgameApi
import logout
import neteaseSquadScript.squadConst as squadConst
import server.extraServerApi as serverApi

ServerSystem = serverApi.GetServerSystemCls()


class SquadServerSystem(ServerSystem):
	def __init__(self, namespace, systemName):
		ServerSystem.__init__(self, namespace, systemName)
		self.mSquadOnlinePlayers = {}

		self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), squadConst.AddServerPlayerEvent, self, self.OnAddServerPlayer)
		self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), squadConst.DelServerPlayerEvent, self, self.OnDelServerPlayer)
		self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), squadConst.AddLevelEvent, self, self.OnPlayerAddLevel)

		self.ListenForEvent(squadConst.ModName, squadConst.ClientSystemName, 'EnableUI', self, self.OnEnableUI)
		self.ListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SquadPlayerCheckEvent, self, self.OnSquadPlayerCheck)
		self.ListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SquadPlayerRecruitEvent, self, self.OnSquadPlayerRecruit)
		self.ListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SquadAppendPlayerEvent, self, self.OnSquadAppendPlayer)
		self.ListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SquadRejectPlayerEvent, self, self.OnSquadRejectPlayer)
		self.ListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SquadApplicantsClearEvent, self, self.OnSquadApplicantsClear)
		self.ListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SquadPlayerLeaveEvent, self, self.OnSquadPlayerLeave)
		self.ListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SquadApplyListEvent, self, self.OnSquadApplyList)
		self.ListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SquadRecruitListEvent, self, self.OnSquadRecruitList)
		self.ListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SquadRecruitmentApplyEvent, self, self.OnSquadRecruitmentApply)
		self.ListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.JoinSquadEvent, self, self.OnJoinSquad)
		self.ListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SetupSquadEvent, self, self.OnSetupSquad)
		self.ListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.DissolveSquadEvent, self, self.OnDissolveSquad)
		self.ListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SquadChiefTransferEvent, self, self.OnSquadChiefTransfer)
		self.ListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.KickSquadPlayerEvent, self, self.OnKickSquadPlayer)
		self.ListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.AssembleEvent, self, self.OnAssemble)
		self.ListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.ForwardEvent, self, self.OnForward)

		self.ListenForEvent(squadConst.ModName, squadConst.ServiceSystemName, squadConst.SquadPlayerDisconnectEvent, self, self.OnSquadPlayerDisconnect)
		self.ListenForEvent(squadConst.ModName, squadConst.ServiceSystemName, squadConst.SquadPlayerReconnectEvent, self, self.OnSquadPlayerReconnect)
		self.ListenForEvent(squadConst.ModName, squadConst.ServiceSystemName, squadConst.SquadPlayerUpdateEvent, self, self.OnSquadPlayerUpdate)
		self.ListenForEvent(squadConst.ModName, squadConst.ServiceSystemName, squadConst.SquadInvitePlayerEvent, self, self.OnSquadInvitePlayer)
		self.ListenForEvent(squadConst.ModName, squadConst.ServiceSystemName, squadConst.SquadRecruitmentApplyEvent, self, self.OnSomeoneApply)
		self.ListenForEvent(squadConst.ModName, squadConst.ServiceSystemName, squadConst.SetupSquadEvent, self, self.OnSomeoneSetupSquad)
		self.ListenForEvent(squadConst.ModName, squadConst.ServiceSystemName, squadConst.DissolveSquadEvent, self, self.OnSomeoneDissolveSquad)
		self.ListenForEvent(squadConst.ModName, squadConst.ServiceSystemName, squadConst.AssembleEvent, self, self.OnSquadAssemble)
		self.ListenForEvent(squadConst.ModName, squadConst.ServiceSystemName, squadConst.PreForwardEvent, self, self.OnPreForward)
		self.ListenForEvent(squadConst.ModName, squadConst.ServiceSystemName, squadConst.ForwardEvent, self, self.OnSomeoneForward)

	def Destroy(self):
		self.UnListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), squadConst.AddServerPlayerEvent, self, self.OnAddServerPlayer)
		self.UnListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), squadConst.DelServerPlayerEvent, self, self.OnDelServerPlayer)
		self.UnListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), squadConst.AddLevelEvent, self, self.OnPlayerAddLevel)

		self.UnListenForEvent(squadConst.ModName, squadConst.ClientSystemName, 'EnableUI', self, self.OnEnableUI)
		self.UnListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SquadPlayerCheckEvent, self, self.OnSquadPlayerCheck)
		self.UnListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SquadPlayerRecruitEvent, self, self.OnSquadPlayerRecruit)
		self.UnListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SquadAppendPlayerEvent, self, self.OnSquadAppendPlayer)
		self.UnListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SquadRejectPlayerEvent, self, self.OnSquadRejectPlayer)
		self.UnListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SquadApplicantsClearEvent, self, self.OnSquadApplicantsClear)
		self.UnListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SquadPlayerLeaveEvent, self, self.OnSquadPlayerLeave)
		self.UnListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SquadApplyListEvent, self, self.OnSquadApplyList)
		self.UnListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SquadRecruitListEvent, self, self.OnSquadRecruitList)
		self.UnListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SquadRecruitmentApplyEvent, self, self.OnSquadRecruitmentApply)
		self.UnListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.JoinSquadEvent, self, self.OnJoinSquad)
		self.UnListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SetupSquadEvent, self, self.OnSetupSquad)
		self.UnListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.DissolveSquadEvent, self, self.OnDissolveSquad)
		self.UnListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.SquadChiefTransferEvent, self, self.OnSquadChiefTransfer)
		self.UnListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.KickSquadPlayerEvent, self, self.OnKickSquadPlayer)
		self.UnListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.AssembleEvent, self, self.OnAssemble)
		self.UnListenForEvent(squadConst.ModName, squadConst.ClientSystemName, squadConst.ForwardEvent, self, self.OnForward)

		self.UnListenForEvent(squadConst.ModName, squadConst.ServiceSystemName, squadConst.SquadPlayerDisconnectEvent, self, self.OnSquadPlayerDisconnect)
		self.UnListenForEvent(squadConst.ModName, squadConst.ServiceSystemName, squadConst.SquadPlayerReconnectEvent, self, self.OnSquadPlayerReconnect)
		self.UnListenForEvent(squadConst.ModName, squadConst.ServiceSystemName, squadConst.SquadPlayerUpdateEvent, self, self.OnSquadPlayerUpdate)
		self.UnListenForEvent(squadConst.ModName, squadConst.ServiceSystemName, squadConst.SquadInvitePlayerEvent, self, self.OnSquadInvitePlayer)
		self.UnListenForEvent(squadConst.ModName, squadConst.ServiceSystemName, squadConst.SquadRecruitmentApplyEvent, self, self.OnSomeoneApply)
		self.UnListenForEvent(squadConst.ModName, squadConst.ServiceSystemName, squadConst.SetupSquadEvent, self, self.OnSomeoneSetupSquad)
		self.UnListenForEvent(squadConst.ModName, squadConst.ServiceSystemName, squadConst.DissolveSquadEvent, self, self.OnSomeoneDissolveSquad)
		self.UnListenForEvent(squadConst.ModName, squadConst.ServiceSystemName, squadConst.AssembleEvent, self, self.OnSquadAssemble)
		self.UnListenForEvent(squadConst.ModName, squadConst.ServiceSystemName, squadConst.PreForwardEvent, self, self.OnPreForward)
		self.UnListenForEvent(squadConst.ModName, squadConst.ServiceSystemName, squadConst.ForwardEvent, self, self.OnSomeoneForward)

	def Update(self):
		# timermanager.timerManager.tick()
		pass

	def OnEnableUI(self, data):
		"""
		?????????????????????/??????????????????
		"""
		playerId = data.get("playerId", "-1")
		uid = netgameApi.GetPlayerUid(playerId)
		if not uid:
			return
		import apolloCommon.commonNetgameApi as commonNetgameApi
		cfg = commonNetgameApi.GetModJsonConfig("neteaseSquadScript")
		if not cfg:
			print 'Nuthang'
			return
		self.NotifyToClient(playerId, 'EnableUI', {'flag': cfg.get('EnableUI', True)})

	def SquadServerRender(self, playerId, eventName, respData):
		"""
		?????????????????????????????????????????????????????????service?????????????????????????????????server???????????????????????????????????????????????????client
		"""
		print playerId, eventName, respData
		if eventName == squadConst.SquadPlayerUpdateEvent:
			if respData['code'] == squadConst.RespCodeSuccess:
				comp = self.CreateComponent(playerId, 'Minecraft', 'command')
				if respData['message']:
					alertSystem = serverApi.GetSystem("neteaseAlert", "neteaseAlertDev")
					if alertSystem:
						alertSystem.Alert(playerId, '{}???'.format(respData['message']), 2, 0.5, 0.8)
					else:
						comp.SetCommand('tellraw @s {"rawtext": [{"text": "%s"}]}' % '{}'.format(respData['message']), playerId)
				# if playerId not in self.mSquadOnlinePlayers:
				# 	self.mSquadOnlinePlayers[playerId] = respData['entity']['uid']
				self.mSquadOnlinePlayers[playerId] = respData['entity']['uid']
				self.NotifyToClient(playerId, eventName, respData['entity'])

				peaceSystem = serverApi.GetSystem("neteasePeace", "neteasePeaceDev")
				if peaceSystem:
					peaceSystem.UpdatePlayerId2Crew(playerId, 'squad' in respData['entity'] and {uid for uid in respData['entity']['squad']['members']})
		elif eventName in (squadConst.SquadPlayerRecruitEvent, squadConst.SetupSquadEvent, squadConst.DissolveSquadEvent, squadConst.SquadPlayerLeaveEvent, squadConst.SquadApplyListEvent, squadConst.SquadRecruitListEvent, squadConst.SquadApplicantsClearEvent, squadConst.SquadInvitePlayerEvent, squadConst.AssembleEvent):
			comp = self.CreateComponent(playerId, 'Minecraft', 'command')
			if respData['code'] == squadConst.RespCodeSuccess:
				if 'entity' in respData:
					self.NotifyToClient(playerId, eventName, respData['entity'])
				if respData['message']:
					alertSystem = serverApi.GetSystem("neteaseAlert", "neteaseAlertDev")
					if alertSystem:
						alertSystem.Alert(playerId, '??a{}???'.format(respData['message']), 2, 0.5, 0.8)
					else:
						comp.SetCommand('tellraw @s {"rawtext": [{"text": "%s"}]}' % '??a{}'.format(respData['message']), playerId)
			else:
				alertSystem = serverApi.GetSystem("neteaseAlert", "neteaseAlertDev")
				if alertSystem:
					alertSystem.Alert(playerId, '??c{}???'.format(respData['message']), 2, 0.5, 0.8)
				else:
					comp.SetCommand('tellraw @s {"rawtext": [{"text": "%s"}]}' % '??c{}'.format(respData['message']), playerId)
		elif eventName in (squadConst.SquadAppendPlayerEvent,):
			self.NotifyToClient(playerId, eventName, respData)
		elif eventName in (squadConst.SquadRecruitmentApplyEvent, squadConst.SquadPlayerDisconnectEvent, squadConst.SquadPlayerReconnectEvent):
			if respData['message']:
				comp = self.CreateComponent(playerId, 'Minecraft', 'command')
				alertSystem = serverApi.GetSystem("neteaseAlert", "neteaseAlertDev")
				if alertSystem:
					alertSystem.Alert(playerId, '{}???'.format(respData['message']), 2, 0.5, 0.8)
				else:
					comp.SetCommand('tellraw @s {"rawtext": [{"text": "%s"}]}' % '{}'.format(respData['message']), playerId)
			self.NotifyToClient(playerId, eventName, respData)
		elif eventName in (squadConst.JoinSquadEvent, squadConst.SquadChiefTransferEvent, squadConst.ForwardEvent):
			if respData['message']:
				comp = self.CreateComponent(playerId, 'Minecraft', 'command')
				alertSystem = serverApi.GetSystem("neteaseAlert", "neteaseAlertDev")
				if alertSystem:
					alertSystem.Alert(playerId, '{}???'.format(respData['message']), 2, 0.5, 0.8)
				else:
					comp.SetCommand('tellraw @s {"rawtext": [{"text": "%s"}]}' % '{}'.format(respData['message']), playerId)

	def OnSquadPlayerCheck(self, data):
		"""
		client????????????????????????server???????????????????????????
		"""
		print 'OnSquadPlayerCheck', data
		playerId = data.get("playerId", "-1")
		uid = netgameApi.GetPlayerUid(playerId)
		if not uid:
			print 'can not get uid by playerId: %s' % playerId
			logout.error('[neteaseSquad] can not get uid OnSquadPlayerCheck by playerId: %s' % playerId)
			return
		self.UpdateSquadPlayer(playerId, uid)

	def OnPlayerAddLevel(self, data):
		"""
		???????????????????????????service?????????????????????????????????service?????????????????????????????????
		"""
		print 'OnPlayerAddLevel', data
		playerId = data.get("id", "-1")
		uid = self.mSquadOnlinePlayers.get(playerId)
		if not uid:
			logout.warning('Not Available OnPlayerAddLevel')
			return
		if data.get('addLevel'):
			self.UpdateSquadPlayer(playerId, uid)

	def OnAddServerPlayer(self, data):
		"""
		?????????????????????????????????????????????????????????????????????????????????
		"""
		print 'OnAddServerPlayer', data
		playerId = data.get("id", "-1")
		uid = netgameApi.GetPlayerUid(playerId)
		if not uid:
			print 'can not get uid by playerId: %s' % playerId
			logout.error('[neteaseSquad] can not get uid by playerId: %s' % playerId)
			return
		self.UpdateSquadPlayer(playerId, uid)
		try:
			data = json.loads(data.get('transferParam'))
			if 'destination' in data:
				destination = json.loads(data['destination'])
				comp = self.CreateComponent(playerId, "Minecraft", "dimension")
				comp.ChangePlayerDimension(int(destination['dimensionId']), tuple(destination['pos']))
		except:
			print 'forward may fail'

	def UpdateSquadPlayer(self, playerId, uid):
		"""
		???????????????????????????service?????????????????????????????????service?????????????????????????????????
		"""
		comp = self.CreateComponent(playerId, "Minecraft", "name")
		name = comp.GetName()
		comp = self.CreateComponent(playerId, "Minecraft", "lv")
		lv = comp.GetPlayerLevel()
		print 'UpdateSquadPlayer', uid, name, lv
		if not (isinstance(name, str) and isinstance(lv, int) and uid):
			logout.error('UpdateSquadPlayer invalid uid: {} name: {} lv: {}'.format(uid, name, lv))
			return
		self.RequestToService(
			squadConst.ModName,
			squadConst.SquadPlayerUpdateEvent,
			{'uid': uid, 'name': name, 'lv': lv},
			lambda rtn, data: rtn and self.SquadServerRender(playerId, squadConst.SquadPlayerUpdateEvent, data)
		)

	def OnDelServerPlayer(self, data):
		"""
		??????????????????????????????/??????????????????service
		"""
		print 'OnDelServerPlayer', data
		playerId = data.get("id", "-1")
		uid = self.mSquadOnlinePlayers.pop(playerId, None)
		if uid:
			if data.get('isTransfer'):
				self.RequestToService(
					squadConst.ModName,
					squadConst.SquadPlayerServerSwitchEvent,
					{'uid': uid}
				)
			else:
				self.RequestToService(
					squadConst.ModName,
					squadConst.SquadPlayerDisconnectEvent,
					{'uid': uid}
				)

	def OnSquadApplicantsClear(self, data):
		"""
		client???????????????????????????????????????????????????????????????service
		"""
		print 'OnSquadApplicantsClear', data
		playerId = data.get("playerId")
		uid = self.mSquadOnlinePlayers.get(playerId)
		if not uid:
			logout.warning('Not Available OnSquadApplicantsClear')
			return
		self.RequestToService(
			squadConst.ModName,
			squadConst.SquadApplicantsClearEvent,
			{'uid': uid},
			lambda rtn, data: rtn and self.SquadServerRender(playerId, squadConst.SquadApplicantsClearEvent, data)
		)

	def OnSquadRejectPlayer(self, data):
		"""
		client??????????????????????????????????????????????????????????????????????????????service
		"""
		print 'OnSquadRejectPlayer', data
		playerId = data.get("playerId")
		chief = self.mSquadOnlinePlayers.get(playerId)
		if not chief:
			logout.warning('Not Available OnSquadRejectPlayer')
			return
		uid = data.get('uid')
		if not isinstance(uid, int) or uid == chief:
			print 'invalid chief: {} uid: {} OnSquadRejectPlayer'.format(chief, uid)
			return
		self.RequestToService(
			squadConst.ModName,
			squadConst.SquadRejectPlayerEvent,
			{'chief': chief, 'uid': uid}
		)

	def OnSquadAppendPlayer(self, data):
		"""
		client??????????????????????????????????????????????????????????????????????????????service
		"""
		print 'OnSquadAppendPlayer', data
		playerId = data.get("playerId")
		dealer = self.mSquadOnlinePlayers.get(playerId)
		if not dealer:
			logout.warning('Not Available OnSquadAppendPlayer')
			return
		uid = data.get('uid')
		if not isinstance(uid, int) or uid == dealer:
			print 'invalid chief: {} uid: {} OnSquadAppendPlayer'.format(dealer, uid)
			return
		self.SquadAppendPlayer(uid, dealer, dealer, lambda rtn, data: rtn and self.SquadServerRender(playerId, squadConst.SquadAppendPlayerEvent, data))

	def OnSquadPlayerRecruit(self, data):
		"""
		client?????????????????????????????????????????????????????????service
		"""
		print 'OnSquadPlayerRecruit', data
		playerId = data.get("playerId")
		uid = self.mSquadOnlinePlayers.get(playerId)
		if not uid:
			logout.warning('Not Available OnSquadPlayerRecruit')
			return
		label = data.get('label')
		if not isinstance(label, str):
			print 'invalid label: {} OnSquadPlayerRecruit'.format(label)
			return
		self.RequestToService(
			squadConst.ModName,
			squadConst.SquadPlayerRecruitEvent,
			{'uid': uid, 'label': label},
			lambda rtn, data: rtn and self.SquadServerRender(playerId, squadConst.SquadPlayerRecruitEvent, data)
		)
		self.NotifyChatSystem({"playerId":playerId, "uid":uid, "mes":label})
		
	def NotifyChatSystem(self, args):
		# ????????????
		playerId = args.get("playerId")
		uid = args.get("uid")
		mes = args.get("mes")
		
		levelComp = serverApi.CreateComponent(playerId, "Minecraft", "lv")
		playerLevel = levelComp.GetPlayerLevel()
		nickname = netgameApi.GetPlayerNickname(playerId)
		chatSystem = serverApi.GetSystem("neteaseChat", "neteaseChatDev")
		if chatSystem:
			chatDict = {"chatChannel": 0, "playerUid": uid, "nickName": nickname,
			            "playerLevel": playerLevel, "chatType": 2, "infoDict": {}, "mes": mes}
			chatSystem.OutPlayerChat(chatDict)
			chatDict["chatChannel"] = netgameApi.GetServerId()
			chatSystem.OutPlayerChat(chatDict)

	def OnSquadApplyList(self, data):
		"""
		client?????????????????????????????????????????????????????????????????????service
		"""
		print 'OnSquadApplyList', data
		playerId = data.get("playerId")
		uid = self.mSquadOnlinePlayers.get(playerId)
		if not uid:
			logout.warning('Not Available OnSquadApplyList')
			return
		self.RequestToService(
			squadConst.ModName,
			squadConst.SquadApplyListEvent,
			{'uid': uid},
			lambda rtn, data: rtn and self.SquadServerRender(playerId, squadConst.SquadApplyListEvent, data)
		)

	def OnSquadRecruitList(self, data):
		"""
		client??????????????????????????????????????????????????????????????????????????????service
		"""
		print 'OnSquadRecruitList', data
		playerId = data.get("playerId")
		uid = self.mSquadOnlinePlayers.get(playerId)
		if not uid:
			logout.warning('Not Available OnSquadRecruitList')
			return
		self.RequestToService(
			squadConst.ModName,
			squadConst.SquadRecruitListEvent,
			{'uid': uid},
			lambda rtn, data: rtn and self.SquadServerRender(playerId, squadConst.SquadRecruitListEvent, data)
		)

	def OnSquadRecruitmentApply(self, data):
		"""
		client??????????????????????????????????????????????????????????????????????????????service
		"""
		print 'OnSquadRecruitmentApply', data
		playerId = data.get("playerId")
		uid = self.mSquadOnlinePlayers.get(playerId)
		if not uid:
			logout.warning('Not Available OnSquadRecruitmentApply')
			return
		order = data.get('order')
		if not isinstance(order, int):
			print 'invalid order: {} OnSquadRecruitmentApply'.format(order)
			return
		self.RequestToService(
			squadConst.ModName,
			squadConst.SquadRecruitmentApplyEvent,
			{'uid': uid, 'order': order},
			lambda rtn, data: rtn and self.SquadServerRender(playerId, squadConst.SquadRecruitmentApplyEvent, data)
		)

	def OnSquadPlayerLeave(self, data):
		"""
		client????????????????????????????????????????????????????????????service
		"""
		print 'OnSquadPlayerLeave', data
		playerId = data.get("playerId")
		uid = self.mSquadOnlinePlayers.get(playerId)
		if not uid:
			logout.warning('Not Available OnSquadPlayerLeave')
			return
		self.RequestToService(
			squadConst.ModName,
			squadConst.SquadPlayerLeaveEvent,
			{'uid': uid},
			lambda rtn, data: rtn and self.SquadServerRender(playerId, squadConst.SquadPlayerLeaveEvent, data)
		)

	def OnJoinSquad(self, data):
		"""
		client??????????????????????????????????????????????????????????????????service
		"""
		print 'OnJoinSquad', data
		playerId = data.get("playerId")
		uid = self.mSquadOnlinePlayers.get(playerId)
		if not uid:
			logout.warning('Not Available OnJoinSquad')
			return
		order = data.get('order')
		if not isinstance(order, int):
			print 'invalid order: {} OnJoinSquad'.format(order)
			return
		self.RequestToService(
			squadConst.ModName,
			squadConst.JoinSquadEvent,
			{'uid': uid, 'order': order},
			lambda rtn, data: rtn and self.SquadServerRender(playerId, squadConst.JoinSquadEvent, data)
		)

	def OnForward(self, data):
		"""
		client?????????????????????????????????????????????????????????service
		"""
		print 'OnForward', data
		playerId = data.get("playerId")
		uid = self.mSquadOnlinePlayers.get(playerId)
		if not uid:
			logout.warning('Not Available OnForward')
			return
		self.RequestToService(
			squadConst.ModName,
			squadConst.ForwardEvent,
			{'uid': uid},
			lambda rtn, data: rtn and self.SquadServerRender(playerId, squadConst.ForwardEvent, data)
		)

	def OnSquadPlayerDisconnect(self, data):
		"""
		??????????????????????????????????????????service????????????client
		"""
		print 'OnSquadPlayerDisconnect', data
		playerId = netgameApi.GetPlayerIdByUid(data['entity']['uid'])
		if not playerId:
			print 'can not get playerId by uid: %s' % data['entity']['uid']
			return
		self.SquadServerRender(playerId, squadConst.SquadPlayerDisconnectEvent, data)

	def OnSquadPlayerReconnect(self, data):
		"""
		???????????????????????????????????????service????????????client
		"""
		print 'OnSquadPlayerReconnect', data
		playerId = netgameApi.GetPlayerIdByUid(data['entity']['uid'])
		if not playerId:
			print 'can not get playerId by uid: %s' % data['entity']['uid']
			return
		self.SquadServerRender(playerId, squadConst.SquadPlayerReconnectEvent, data)

	def OnSquadPlayerUpdate(self, data):
		"""
		???????????????????????????????????????service????????????client
		"""
		print 'OnSquadPlayerUpdate', data
		playerId = netgameApi.GetPlayerIdByUid(data['entity']['uid'])
		if not playerId:
			print 'can not get playerId by uid: %s' % data['entity']['uid']
			return
		self.SquadServerRender(playerId, squadConst.SquadPlayerUpdateEvent, data)

	def OnPreForward(self, data):
		"""
		??????service??????????????????????????????????????????????????????service
		"""
		print 'OnPreForward', data
		playerId = netgameApi.GetPlayerIdByUid(data['chief'])
		if not playerId:
			print 'can not get playerId by uid: %s' % data['chief']
			return
		comp = self.CreateComponent(playerId, "Minecraft", "dimension")
		dimensionId = comp and comp.GetPlayerDimensionId()
		comp = self.CreateComponent(playerId, "Minecraft", "pos")
		pos = comp and comp.GetPos()
		if not (isinstance(dimensionId, int) and (isinstance(pos, tuple) or isinstance(pos, list))):
			logout.error('got invalid dimensionId: {} or invalid pos: {} by playerId: {} OnPreForward'.format(dimensionId, pos, playerId))
			return
		destination = json.dumps({'dimensionId': dimensionId, 'pos': pos})
		self.RequestToService(
			squadConst.ModName,
			squadConst.PreForwardEvent,
			{'uid': data['uid'], 'destination': destination},
			lambda rtn, data: rtn or logout.error('timeout OnPreForward')
		)

	def OnSquadAssemble(self, data):
		"""
		??????service?????????????????????????????????client
		"""
		print 'OnSquadAssemble', data
		playerId = netgameApi.GetPlayerIdByUid(data['entity']['uid'])
		if not playerId:
			print 'can not get playerId by uid: %s' % data['entity']['uid']
			return
		self.SquadServerRender(playerId, squadConst.AssembleEvent, data)

	def OnSquadInvitePlayer(self, data):
		"""
		??????service???????????????????????????????????????client
		"""
		print 'OnSquadInvitePlayer', data
		playerId = netgameApi.GetPlayerIdByUid(data['entity']['uid'])
		if not playerId:
			print 'can not get playerId by uid: %s' % data['entity']['uid']
			return
		self.SquadServerRender(playerId, squadConst.SquadInvitePlayerEvent, data)

	def OnSomeoneForward(self, data):
		"""
		??????service?????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
		"""
		print 'OnSomeoneForward', data
		playerId = netgameApi.GetPlayerIdByUid(data['uid'])
		if not playerId:
			print 'can not get playerId by uid: %s' % data['uid']
			return
		if 'msg' in data:
			comp = self.CreateComponent(playerId, 'Minecraft', 'command')
			alertSystem = serverApi.GetSystem("neteaseAlert", "neteaseAlertDev")
			if alertSystem:
				alertSystem.Alert(playerId, '{}???'.format(data['msg']), 2, 0.5, 0.8)
			else:
				comp.SetCommand('tellraw @s {"rawtext": [{"text": "%s"}]}' % '{}'.format(data['msg']), playerId)
		if netgameApi.GetServerId() == data['serverId']:
			destination = json.loads(data['destination'])
			comp = self.CreateComponent(playerId, "Minecraft", "dimension")
			comp.ChangePlayerDimension(int(destination['dimensionId']), tuple(destination['pos']))
		else:
			netgameApi.TransferToOtherServerById(playerId, data['serverId'], json.dumps({'destination': data['destination']}))

	def OnSomeoneApply(self, data):
		"""
		??????service?????????????????????????????????????????????client
		"""
		print 'OnSomeoneApply', data
		playerId = netgameApi.GetPlayerIdByUid(data['chief'])
		if not playerId:
			print 'can not get playerId by uid: %s' % data['chief']
			return
		self.NotifyToClient(playerId, squadConst.SquadApplicationNoticeEvent, {'chief': data['chief']})

	def OnSomeoneSetupSquad(self, data):
		"""
		??????service?????????????????????????????????client
		"""
		print 'OnSomeoneSetupSquad', data
		self.BroadcastEvent(squadConst.SetupSquadEvent, {
			'squad': data['entity']['squad'],
		})

	def OnSomeoneDissolveSquad(self, data):
		"""
		??????service?????????????????????????????????client
		"""
		print 'OnSomeoneDissolveSquad', data
		squad = data['entity']['squad']
		for uid in squad['members']:
			if uid != squad['chief']:
				playerId = netgameApi.GetPlayerIdByUid(uid)
				if playerId:
					self.SquadServerRender(playerId, squadConst.DissolveSquadEvent, {
						'code': data['code'],
						'message': data['message'],
						'entity': {'uid': uid}
					})
		self.BroadcastEvent(squadConst.DissolveSquadEvent, {
			'squad': squad,
		})

	def OnKickSquadPlayer(self, data):
		"""
		client???????????????????????????????????????????????????????????????service
		"""
		print 'OnKickSquadPlayer', data
		playerId = data.get("playerId")
		uid = self.mSquadOnlinePlayers.get(playerId)
		if not uid:
			logout.warning('Not Available OnKickSquadPlayer')
			return
		self.KickSquadPlayer(uid, data.get('uid'))

	# ??????????????????????????????????????????
	# 1???client?????????????????????????????????server
	# 2???server?????????????????????service
	# 3???service?????????????????????????????????????????????????????????????????????client?????????server
	# 4???server?????????????????????????????????client
	# 5???client??????????????????????????????????????????????????????????????????
	# 6???client???????????????????????????????????????server
	# 7???server?????????service
	# 8???service???????????????????????????????????????????????????server
	# 9??????????????????server????????????service??????????????????????????????
	# 10???service?????????????????????????????????????????????????????????????????????server
	# 11??????????????????server????????????????????????serverId?????????????????????????????????????????????????????????
	# 12????????????????????????????????????????????????????????????????????????????????????????????????????????????
	def OnAssemble(self, data):
		"""
		client???????????????????????????????????????????????????service
		"""
		print 'OnAssemble', data
		playerId = data.get("playerId")
		uid = self.mSquadOnlinePlayers.get(playerId)
		if not uid:
			logout.warning('Not Available OnAssemble')
			return
		self.Assemble(uid, lambda rtn, data: rtn and self.SquadServerRender(playerId, squadConst.AssembleEvent, data))

	def OnSquadChiefTransfer(self, data):
		"""
		client???????????????????????????????????????????????????service
		"""
		print 'OnSquadChiefTransfer', data
		playerId = data.get("playerId")
		chief = self.mSquadOnlinePlayers.get(playerId)
		if not chief:
			logout.warning('Not Available OnSquadChiefTransfer')
			return
		uid = data.get('uid')
		self.RequestToService(
			squadConst.ModName,
			squadConst.SquadChiefTransferEvent,
			{'chief': chief, 'uid': uid},
			lambda rtn, data: rtn and self.SquadServerRender(playerId, squadConst.SquadChiefTransferEvent, data)
		)

	def OnDissolveSquad(self, data):
		"""
		client???????????????????????????????????????????????????service
		"""
		print 'OnDissolveSquad', data
		playerId = data.get("playerId")
		uid = self.mSquadOnlinePlayers.get(playerId)
		if not uid:
			logout.warning('Not Available OnDissolveSquad')
			return
		self.DissolveSquad(uid)

	def OnSetupSquad(self, data):
		"""
		client???????????????????????????????????????????????????service
		"""
		print 'OnSetupSquad', data
		playerId = data.get("playerId")
		uid = self.mSquadOnlinePlayers.get(playerId)
		if not uid:
			logout.warning('Not Available OnSetupSquad')
			return
		self.SetupSquad(uid)

	def SetupSquad(self, uid):
		"""
		??????????????????
		:param uid: ?????????uid
		"""
		playerId = netgameApi.GetPlayerIdByUid(uid)
		if not playerId:
			print 'can not get playerId by uid: %s' % uid
			return
		if not self.mSquadOnlinePlayers.get(playerId):
			logout.warning('SetupSquad Not Available')
			return
		if uid != self.mSquadOnlinePlayers[playerId]:
			self.mSquadOnlinePlayers[playerId] = uid
		self.RequestToService(
			squadConst.ModName,
			squadConst.SetupSquadEvent,
			{'uid': uid},
			lambda rtn, data: rtn and self.SquadServerRender(playerId, squadConst.SetupSquadEvent, data)
		)

	def DissolveSquad(self, uid):
		"""
		??????????????????
		:param uid: ?????????uid
		"""
		playerId = netgameApi.GetPlayerIdByUid(uid)
		if not playerId:
			print 'can not get playerId by uid: %s' % uid
			return
		if not self.mSquadOnlinePlayers.get(playerId):
			logout.warning('DissolveSquad Not Available')
			return
		if uid != self.mSquadOnlinePlayers[playerId]:
			self.mSquadOnlinePlayers[playerId] = uid
		self.RequestToService(
			squadConst.ModName,
			squadConst.DissolveSquadEvent,
			{'uid': uid},
			lambda rtn, data: rtn and self.SquadServerRender(playerId, squadConst.DissolveSquadEvent, data)
		)

	def KickSquadPlayer(self, chief, uid):
		"""
		???????????????????????????
		:param chief: ????????????uid
		:param uid: ???????????????uid
		"""
		if chief == uid or not (isinstance(chief, int) and isinstance(uid, int)):
			print 'KickSquadPlayer invalid chief: {} uid: {}'.format(chief, uid)
			return
		# playerId = netgameApi.GetPlayerIdByUid(uid)
		# if not playerId:
		# 	print 'can not get playerId by uid: %s' % uid
		# 	return
		# if not self.mSquadOnlinePlayers.get(playerId):
		# 	logout.warning('KickSquadPlayer Not Available')
		# 	return
		# if uid != self.mSquadOnlinePlayers[playerId]:
		# 	self.mSquadOnlinePlayers[playerId] = uid
		self.RequestToService(
			squadConst.ModName,
			squadConst.KickSquadPlayerEvent,
			{'chief': chief, 'uid': uid}
		)

	def SquadAppendPlayer(self, uid, chief, dealer, cb):
		"""
		???????????????????????????
		:param uid: ?????????uid
		:param chief: ?????????uid
		:param dealer: ????????????uid
		:param cb: ??????????????????cb??????
		"""
		self.RequestToService(
			squadConst.ModName,
			squadConst.SquadAppendPlayerEvent,
			{'chief': chief, 'uid': uid, 'dealer': dealer},
			cb
		)

	def SquadInvitePlayer(self, uid, chief, dealer, cb):
		"""
		??????????????????????????????
		:param uid: ?????????uid
		:param chief: ?????????uid
		:param dealer: ????????????uid
		:param cb: ??????????????????cb??????
		"""
		self.RequestToService(
			squadConst.ModName,
			squadConst.SquadInvitePlayerEvent,
			{'chief': chief, 'uid': uid, 'dealer': dealer},
			cb
		)

	def CheckPlayerSquad(self, uid, cb):
		"""
		????????????????????????
		:param uid: ?????????uid
		:param cb: ??????????????????cb??????
		"""
		self.RequestToService(
			squadConst.ModName,
			squadConst.SquadPlayerCheckEvent,
			{'uid': uid},
			cb
		)

	def QuerySquadByOrder(self, order, cb):
		"""
		????????????????????????????????????
		:param order: ????????????
		:param cb: ????????????????????????cb??????
		"""
		self.RequestToService(
			squadConst.ModName,
			squadConst.QuerySquadByOrderEvent,
			{'order': order},
			cb
		)

	def Assemble(self, uid, cb):
		self.RequestToService(
			squadConst.ModName,
			squadConst.AssembleEvent,
			{'uid': uid},
			cb
		)

	def Teleport(self, uid, serverId, dimensionId, pos, label=''):
		"""
		????????????????????????????????????????????????????????????????????????
		:param uid:
		:param serverId:
		:param dimensionId:
		:param pos:
		:param label:
		"""
		destination = json.dumps({'dimensionId': dimensionId, 'pos': pos})
		self.RequestToService(
			squadConst.ModName,
			squadConst.TeleportEvent,
			{'uid': uid, 'serverId': serverId, 'destination': destination, 'label': label}
		)

	def AssembleOption(self, uid, ban, cb):
		"""

		:param uid:
		:param ban:
		:param cb:
		"""
		self.RequestToService(
			squadConst.ModName,
			squadConst.AssembleOptionEvent,
			{'uid': uid, 'ban': ban},
			cb
		)

	def LeaveOption(self, uid, ban, cb):
		"""

		:param uid:
		:param ban:
		:param cb:
		"""
		self.RequestToService(
			squadConst.ModName,
			squadConst.LeaveOptionEvent,
			{'uid': uid, 'ban': ban},
			cb
		)
