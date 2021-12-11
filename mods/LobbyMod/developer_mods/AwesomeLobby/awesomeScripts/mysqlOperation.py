# -*- coding: utf-8 -*-
import apolloCommon.mysqlPool as mysqlPool
import logout
import lobbyGame.netgameApi as netgameApi

class MysqlOperation(object):
	def __init__(self):
		mysqlPool.InitDB(20)
	
	def QueryPlayerData(self, player_id, uid, cb=None):
		sql = 'SELECT uid,nickname,login_time FROM playerCol WHERE uid=%s'
		params = (uid,)
		mysqlPool.AsyncQueryWithOrderKey(uid,sql,params, cb)
	
	def InsertPlayerData(self, player_id, uid, player_data, cb=None):
		sql = 'INSERT INTO playerCol (uid, nickname,login_time) VALUES (%s, %s, %s)'
		params = (uid, player_data['nickname'],player_data['login_time'])
		mysqlPool.AsyncQueryWithOrderKey(uid,sql,params,cb)
	
	def SavePlayerByUid(self, uid, player_data, cb=None):
		sql = 'UPDATE playerCol SET nickname=%s,login_time=%s WHERE uid=%s'
		params = (player_data['nickname'],player_data['login_time'],uid)
		mysqlPool.AsyncQueryWithOrderKey(uid,sql, params, cb)
		
	def Destroy(self):
		mysqlPool.Finish()
		