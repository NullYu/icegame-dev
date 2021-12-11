# -*- coding: utf-8 -*-

from common.mod import Mod
import mod.client.extraClientApi as clientApi
# 变量的值尽量写在一个config文件中，这里我们写在了modConfig中
# 这样的好处是，对于字符串变量我们不会打错减少BUG
# DeBug的时候或者修改变量的时候，不用修改每一个使用的地方，只需要修改config文件
from awesomeModScripts.modCommon import modConfig
# 用来打印规范格式的log
from mod_log import logger

@Mod.Binding(name = modConfig.AwesomeModName, version = modConfig.ModVersion)
class HugoFpsMod(object):

    def __init__(self):
        logger.info("===== init HugoFpsMod =====")
    
    @Mod.InitClient()
    def HugoFpsClientInit(self):
        '''
        加载mod入口
        '''
        logger.info("===== init HugoFpsMod client =====")
        clientApi.RegisterSystem(modConfig.AwesomeModName, modConfig.FpsClientSystemName, modConfig.FpsClientSystemClsPath)
    
    @Mod.DestroyClient()
    def HugoFpsClientDestroy(self):
        '''
        退出游戏时注销mod
        '''
        logger.info("===== destroy HugoFpsMod client =====")
