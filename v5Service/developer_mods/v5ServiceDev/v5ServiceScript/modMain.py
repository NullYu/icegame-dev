# -*- coding: utf-8 -*-

from common.mod import Mod


@Mod.Binding(name="v5Service", version="0.1")
class ServiceMod(object):
    def __init__(self):
        pass

    @Mod.InitService()
    def initService(self):
        print '####################v5Service UP####################'
        # 注册service的system
        import server.extraServiceApi as serviceApi
        self.server = serviceApi.RegisterSystem("v5Service", "v5Service",
                                                "v5ServiceScript.v5ServiceSystem.v5ServiceSystemSys")

    @Mod.DestroyService()
    def destroyService(self):
        print '===========================AwesomeService destroyService==============================='
