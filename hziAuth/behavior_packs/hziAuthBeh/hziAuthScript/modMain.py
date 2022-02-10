# -*- coding: utf-8 -*-
# @Author : uni_kevin(可乐)

from mod.common.mod import Mod
import mod.client.extraClientApi as clientApi

@Mod.Binding(name='HziAuth', version='1.0.0')
class HziAuth(object):

    @Mod.InitClient()
    def ClientInit(self):
        clientApi.RegisterSystem('HziAuth', 'HziAuthBeh', 'hziAuthScript.hziAuthBeh.HziAuthBeh')

    @Mod.DestroyClient()
    def ClientDestroy(self):
        pass