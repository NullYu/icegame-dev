# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraMasterApi as extraMasterApi
import apolloCommon.mysqlPool as mysqlPool
import time
import master.serverManager as serverManager

# 获取引擎服务端System的基类，System都要继承于MasterSystem来调用相关函数
MasterSystem = extraMasterApi.GetMasterSystemCls()

# 在modMain中注册的Server System类
class reportMasterSystem(MasterSystem):
    # MasterSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        MasterSystem.__init__(self, namespace, systemName)
        self.ListenEvent()

    def ListenEvent(self):
        self.ListenForEvent('report', 'reportSystem', 'SendReportEvent', self, self.OnSendReport)
        self.ListenForEvent('report', 'reportSystem', 'ProcessReportEvent', self, self.OnProcessReport)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass

    def OnSendReport(self, args):
        print 'CALL OnSendReport args=%s' % (args,)
        idList = serverManager.GetConnectedLobbyAndGameIds()

        for server in idList:
            self.NotifyToServerNode(server, "DisplayReportEvent", args)

    def OnProcessReport(self, args):
            idList = serverManager.GetConnectedLobbyAndGameIds()
            print 'onprocesreport args=%s' % (args,)

            for server in idList:
                self.NotifyToServerNode(server, "DisplayProcessReportEvent", args)