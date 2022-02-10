# -*- coding: utf-8 -*-

from common.mod import Mod


@Mod.Binding(name="partyService", version="0.1")
class ServiceMod(object):
    def __init__(self):
        pass

    @Mod.InitService()
    def initService(self):
        print '####################partyService UP####################'
        # 注册service的system
        import server.extraServiceApi as serviceApi
        self.server = serviceApi.RegisterSystem("partyService", "partyService",
                                                "partyServiceScript.partyServiceSystem.partyServiceSystemSys")

    @Mod.DestroyService()
    def destroyService(self):
        print '===========================AwesomeService destroyService==============================='
