# -*- coding: utf-8 -*-
# @Author : uni_kevin(可乐)
import json

import apolloCommon.commonNetgameApi as commonNetgameApi
import lobbyGame.netgameApi as lobbyGameApi
import mod.server.extraServerApi as serverApi
import serverhttp
from apolloCommon import mysqlPool

ServerSystem = serverApi.GetServerSystemCls()
EngineNamespace = serverApi.GetEngineNamespace()
EngineSystemName = serverApi.GetEngineSystemName()

# noinspection SqlResolve
class HziAuthDev(ServerSystem):

    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        self.playerAuthData = {}
        self.needRegPlayer = set([])
        self.sendCodeCd = set([])
        self.kickPlayerTimer = {}
        config = commonNetgameApi.GetModJsonConfig('hziAuthScript')
        self.mustAuth = config['must_auth_phone']
        self.apiHost = config['database_host']
        mysqlPool.InitDB(config['mysql_pool_size'])
        self.ListenForEvent('HziAuth', 'HziAuthMaster', 'InitPlayerHealthCode', self, self.InitPlayerHealthCode)
        self.ListenForEvent('HziAuth', 'HziAuthBeh', 'OnUIInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent('HziAuth', 'HziAuthBeh', 'PlayerRefuse', self, self.PlayerRefuse)
        self.ListenForEvent('HziAuth', 'HziAuthBeh', 'SendCode', self, self.SendCode)
        self.ListenForEvent('HziAuth', 'HziAuthBeh', 'AuthCode', self, self.AuthCode)
        self.ListenForEvent(EngineNamespace, EngineSystemName, 'AddServerPlayerEvent', self, self.AddServerPlayerEvent)
        self.ListenForEvent(EngineNamespace, EngineSystemName, 'DelServerPlayerEvent', self, self.DelServerPlayerEvent)

    def KickPlayer(self, client, msg):
        lobbyGameApi.TryToKickoutPlayer(client, msg)
        def MasterKick():
            self.NotifyToMaster('KickPlayer', {'uid': uid, 'msg': msg})
        uid = lobbyGameApi.GetPlayerUid(client)
        if uid:
            game = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
            game.AddTimer(2, MasterKick)

    def PlayerRefuse(self, e):
        if self.mustAuth:
            self.KickPlayer(e['client'], '必须要绑定手机号才能游玩此服务器。')

    def AuthCode(self, e):
        uid = lobbyGameApi.GetPlayerUid(e['client'])
        if not uid:
            return
        url = self.apiHost + '/auth_code'
        header = {'Content-Type': 'application/json'}
        data = json.dumps({'uid': uid, 'phone': e['phone'], 'code': e['code']})
        def callback(code, result, header):
            if code == 200:
                result = json.loads(result, encoding='utf-8')
                self.NotifyToClient(e['client'], 'AuthRequest', {'code': result['code']})
                if result['code'] == 200:
                    self.playerAuthData[uid]['code'] = 1
                    # game = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
                    # game.CancelTimer(self.kickPlayerTimer[uid])
                    sql = 'INSERT INTO `hziAuth` (uid, phone) VALUES ("%s", "%s")' % (uid, e['phone'])
                    mysqlPool.AsyncInsertOneWithOrderKey(uid, sql, (), None)
            else:
                self.NotifyToClient(e['client'], 'AuthRequest', {'code': -1})
        serverhttp.HttpPool().Request('POST', url, header, data, callback)

    def SendCode(self, e):
        uid = lobbyGameApi.GetPlayerUid(e['client'])
        if not uid:
            self.NotifyToClient(e['client'], 'SendRequest', {'code': -1})
            return
        if uid in self.sendCodeCd:
            return
        self.sendCodeCd.add(uid)
        game = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        game.AddTimer(30, self.sendCodeCd.remove(uid))
        url = self.apiHost + '/send_code'
        header = {'Content-Type': 'application/json'}
        data = json.dumps({'uid': uid, 'phone': e['phone']})
        def callback(code, result, header):
            if code == 200:
                result = json.loads(result, encoding='utf-8')
                self.NotifyToClient(e['client'], 'SendRequest', {'code': result['code']})
            else:
                self.NotifyToClient(e['client'], 'SendRequest', {'code': -1})
        serverhttp.HttpPool().Request('POST', url, header, data, callback)

    def InitPlayerHealthCode(self, e):
        self.playerAuthData[e['uid']] = e

    def OnUIInitFinished(self, e):
        self.NotifyToClient(e['client'], 'AuthInit', {'needReg': e['client'] in self.needRegPlayer, 'mustAuth': self.mustAuth})

    def AddServerPlayerEvent(self, e):
        uid = lobbyGameApi.GetPlayerUid(e['id'])
        if uid not in self.playerAuthData:
            lobbyGameApi.TryToKickoutPlayer(e['id'], '无法连接至世界。')
        else:
            if self.playerAuthData[uid]['kick']:
                lobbyGameApi.TryToKickoutPlayer(e['id'], self.playerAuthData[uid]['kickMsg'])
            if self.playerAuthData[uid]['code'] == 0:
                self.needRegPlayer.add(e['id'])
                # game = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
                # self.kickPlayerTimer[uid] = game.AddTimer(120, lobbyGameApi.TryToKickoutPlayer, e['id'], '请在120秒内完成验证操作，已超时')

    def DelServerPlayerEvent(self, e):
        if e['id'] in self.needRegPlayer:
            self.needRegPlayer.remove(e['id'])
        uid = lobbyGameApi.GetPlayerUid(e['id'])
        if uid in self.playerAuthData:
            self.playerAuthData.pop(uid)

    def Destroy(self):
        mysqlPool.Finish()
        ServerSystem.Destroy(self)
