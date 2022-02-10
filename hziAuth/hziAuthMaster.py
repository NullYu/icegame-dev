# -*- coding: utf-8 -*-
# @Author : uni_kevin(可乐)

import json
import logging
import random

import master.netgameApi as netMasterApi
import apolloCommon.commonNetgameApi as commonNetgameApi
import mod.server.extraMasterApi as extraMasterApi
import serverhttp
import master_api.login_net as login_net

MasterSystem = extraMasterApi.GetMasterSystemCls()
EngineNamespace = extraMasterApi.GetEngineNamespace()
EngineSystemName = extraMasterApi.GetEngineSystemName()

class HziAuthMaster(MasterSystem):

    def __init__(self, namespace, systemName):
        MasterSystem.__init__(self, namespace, systemName)
        self.proxyId = 2000
        serverList = netMasterApi.GetCommonConfig()['serverlist']
        for server in serverList:
            if server['app_type'] == 'proxy':
                self.proxyId = server['serverid']
        config = commonNetgameApi.GetModJsonConfig('hziAuthScript')
        self.apiHost = config['database_host']
        self.passAllWhenTimeout = config['pass_all_player_when_database_timeout']
        self.trustUnit = config['trust_unit']
        self.kickMsgList = config['kick_msg']
        self.ListenForEvent(EngineNamespace, EngineSystemName, 'PlayerLoginServerEvent', self, self.PlayerLoginServerEvent)
        self.ListenForEvent('HziAuth', 'HziAuthDev', 'KickPlayer', self, self.KickPlayer)

    def KickPlayer(self, e):
        login_net.login_failed(self.proxyId, e['uid'], e['msg'])

    def PlayerLoginServerEvent(self, e):
        if not e['isTransfer']:
            url = self.apiHost + '/check_player'
            header = {'Content-Type': 'application/json'}
            data = json.dumps({'uid': e['uid']})
            def callback(code, result, header):
                if code == 200:
                    result = json.loads(result, encoding='utf-8')
                    """
                    code 0 未绑定手机号玩家
                    code 1 完全良好玩家
                    code 2 有封禁记录玩家
                    """
                    kick = False
                    if result['code'] == 2:
                        # 有封禁记录玩家
                        for banServer, banLevel in dict(json.loads(result['ban_data'].encode('utf-8'))).items():
                            print banServer, banLevel
                            if banServer in self.trustUnit.keys():
                                if banLevel >= self.trustUnit[banServer]:
                                    kick = True
                                    login_net.login_failed(self.proxyId, e['uid'], random.choice(self.kickMsgList).encode('utf-8`'))
                            else:
                                logging.error('[Apollo统一验证系统] >> 有名为 %s 的接入单位不在你的 trust_unit 配置中, 请检查')
                    eventData = {
                        'uid': e['uid'],
                        'code': result['code'],
                        'kick': kick,
                        'kickMsg': random.choice(self.kickMsgList).encode('utf-8'),
                        'banData': result['ban_data'] if 'ban_data' in result else None
                    }
                    self.NotifyToServerNode(e['serverId'], 'InitPlayerHealthCode', eventData)
                else:
                    logging.error('[Apollo统一验证系统] >> 访问远程数据库失败')
                    if not self.passAllWhenTimeout:
                        login_net.login_failed(self.proxyId, e['uid'], random.choice(self.kickMsgList).encode('utf-8`'))
            serverhttp.HttpPool().Request('POST', url, header, data, callback)