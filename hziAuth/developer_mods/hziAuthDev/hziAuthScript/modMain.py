# -*- coding: utf-8 -*-
# @Author : uni_kevin(可乐)

from mod.common.mod import Mod
import mod.server.extraServerApi as serverApi

@Mod.Binding(name='HziAuth', version='1.0.0')
class HziAuth(object):

    @Mod.InitServer()
    def ServerInit(self):
        serverApi.RegisterSystem('HziAuth', 'HziAuthDev', 'hziAuthScript.hziAuthDev.HziAuthDev')
        serverApi.RegisterSystem('HziAuth', 'HziAuthApi', 'hziAuthScript.hziAuthApi.HziAuthApi')

    @Mod.DestroyServer()
    def ServerDestroy(self):
        pass