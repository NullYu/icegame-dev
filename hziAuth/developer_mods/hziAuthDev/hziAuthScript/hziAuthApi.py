# -*- coding: utf-8 -*-
# @Author : uni_kevin(可乐)
import json

import mod.server.extraServerApi as serverApi
import apolloCommon.commonNetgameApi as commonNetgameApi
import serverhttp

ServerSystem = serverApi.GetServerSystemCls()
EngineNamespace = serverApi.GetEngineNamespace()
EngineSystemName = serverApi.GetEngineSystemName()

# noinspection SqlResolve
class HziAuthApi(ServerSystem):

    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        config = commonNetgameApi.GetModJsonConfig('hziAuthScript')
        self.apiHost = config['database_host']

    @staticmethod
    def IsPlayerBindPhone(uid):
        system = serverApi.GetSystem('HziAuth', 'HziAuthDev')
        if uid in system.playerAuthData:
            return system.playerAuthData[uid]['code'] != 0
        else:
            return False

    def IsPlayerBindPhoneNewest(self, uid, cb):
        url = self.apiHost + '/check_player'
        header = {'Content-Type': 'application/json'}
        data = json.dumps({'uid': uid})
        def callback(code, result, header):
            if code == 200:
                result = json.loads(result, encoding='utf-8')
                cb(result['code'] != 0)
            else:
                cb(None)
        serverhttp.HttpPool().Request('POST', url, header, data, callback)

    @staticmethod
    def GetPlayerBanData(uid):
        system = serverApi.GetSystem('HziAuth', 'HziAuthDev')
        if uid in system.playerAuthData:
            return system.playerAuthData[uid]['banData']
        else:
            return False

    def GetPlayerBanDataNewest(self, uid, cb):
        url = self.apiHost + '/check_player'
        header = {'Content-Type': 'application/json'}
        data = json.dumps({'uid': uid})
        def callback(code, result, header):
            if code == 200:
                result = json.loads(result, encoding='utf-8')
                if 'ban_data' in result:
                    cb(dict(json.loads(result['ban_data'].encode('utf-8'))))
                else:
                    cb({})
            else:
                cb(False)
        serverhttp.HttpPool().Request('POST', url, header, data, callback)

    def BanPlayer(self, uid, level, cb):
        url = self.apiHost + '/ban'
        header = {'Content-Type': 'application/json'}
        data = json.dumps({'uid': uid, 'level': level})
        def callback(code, result, header):
            if code == 200:
                result = json.loads(result, encoding='utf-8')
                cb(result)
            else:
                cb(False)
        serverhttp.HttpPool().Request('POST', url, header, data, callback)

