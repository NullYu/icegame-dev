# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了
#
# 这行是import到MOD的绑定类Mod，用于绑定类和函数

#NOTHING SHOUD BE IN CLIENT MOD

from common.mod import Mod
# 这行import到的是引擎客户端的API模块
import client.extraClientApi as clientApi


# 用Mod.Binding来绑定MOD的类，引擎从而能够识别这个类是MOD的入口类
@Mod.Binding(name="FFA", version="0.1")
class LobbyBehaviorMod(object):
    # 类的初始化函数
    def __init__(self):
        pass

    # InitClient绑定的函数作为客户端脚本初始化的入口函数，通常用来注册客户端系统system和组件component
    @Mod.InitClient()
    def initClient(self):
        print '===========================init ffa client mod!==============================='
        # 函数可以将System注册到客户端引擎中，实例的创建和销毁交给引擎处理。第一个参数是名字空间，第二个是System名称，第三个是自定义MOD System类的路径
        # 取名名称尽量个性化，不能与其他人的MOD冲突，可以使用英文、拼音、下划线这三种。
        self.lobbyClient = clientApi.RegisterSystem("ffa", "ffaClient",
                                                    "ffaScript.ffaClientSystem.ffaClientSystem")

    # DestroyClient绑定的函数作为客户端脚本退出的时候执行的析构函数，通常用来反注册一些内容,可为空
    @Mod.DestroyClient()
    def destroyClient(self):
        print 'destroy_client==============='
