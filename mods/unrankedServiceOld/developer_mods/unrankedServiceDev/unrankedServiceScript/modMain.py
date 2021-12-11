# -*- coding: utf-8 -*-

from common.mod import Mod


@Mod.Binding(name="unrankedService", version="0.1")
class ServiceMod(object):
    def __init__(self):
        pass

    @Mod.InitService()
    def initService(self):
        print '####################unrankedService UP####################'
        # 注册service的system
        import server.extraServiceApi as serviceApi
        self.server = serviceApi.RegisterSystem("unrankedService", "unrankedService",
                                                "unrankedServiceScript.unrankedServiceSystem.unrankedServiceSystemSys")

    @Mod.DestroyService()
    def destroyService(self):
        print '===========================AwesomeService destroyService==============================='
