# -*- coding: utf-8 -*-

from common.mod import Mod


@Mod.Binding(name="manhuntService", version="0.1")
class ServiceMod(object):
    def __init__(self):
        pass

    @Mod.InitService()
    def initService(self):
        print '####################manhuntService UP####################'
        # 注册service的system
        import server.extraServiceApi as serviceApi
        self.server = serviceApi.RegisterSystem("manhuntService", "manhuntService",
                                                "manhuntServiceScript.manhuntServiceSystem.manhuntServiceSystemSys")

    @Mod.DestroyService()
    def destroyService(self):
        print '===========================AwesomeService destroyService==============================='
