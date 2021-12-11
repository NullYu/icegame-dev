# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraMasterApi as extraMasterApi
import apolloCommon.mysqlPool as mysqlPool
import master.netgameApi as netMasterApi
import time
import master.serverManager as serverManager
import apolloCommon.commonNetgameApi as commonNetgameApi

# 获取引擎服务端System的基类，System都要继承于MasterSystem来调用相关函数
MasterSystem = extraMasterApi.GetMasterSystemCls()

# 在modMain中注册的Server System类
class rebootMasterSystem(MasterSystem):
    # MasterSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        MasterSystem.__init__(self, namespace, systemName)
        self.ListenEvent()

        self.authServer = None

    def ListenEvent(self):
        self.ListenForEvent('reboot', 'rebootSystem', 'DoRebootEvent', self, self.OnDoReboot)
        self.ListenForEvent('login', 'loginSystem', 'RegisterAuthServer', self, self.OnRegisterAuthServer)

        # return
        def loginStratege(uid, callback):
            callback(self.authServer)  # 必须执行，执行登陆后续操作
        netMasterApi.SetLoginStratege(loginStratege)

    def OnDoReboot(self, data):
        sid = data['sid']
        serverManager.StopServerById(sid, 1)

    def OnRegisterAuthServer(self, sid):
        print 'onregisterauthserver'
        print 'AUTH SERVER IS SET TO %s' % sid
        self.authServer = sid
