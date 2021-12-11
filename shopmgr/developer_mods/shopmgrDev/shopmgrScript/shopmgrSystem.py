# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import apolloCommon.commonNetgameApi as commonNetgameApi
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.mysqlPool as mysqlPool
cooldown = {}

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

# 在modMain中注册的Server System类
class shopmgrSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

    ##############UTILS##############

    def sendCmd(self, cmd, playerId):
        comp = serverApi.GetEngineCompFactory().CreateCommand(serverApi.getLevelId())
        comp.SetCommand(cmd, playerId)

    def sendTitle(self, title, type, playerId):
        if (type == 1):
            self.sendCmd("/title @s title " + title, playerId)
        elif (type == 2):
            self.sendCmd("/title @s subtitle " + title, playerId)
        elif (type == 3):
            self.sendCmd("/title @s actionbar " + title, playerId)
        else:
            print 'invalid params for call/sendTitle(): type'

    def forceSelect(self, slot, playerId):
        comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
        comp.ChangeSelectSlot(slot)

    def sendMsg(self, msg, playerId):
        comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
        comp.NotifyOneMessage(playerId, msg, "§f")
    #################################

    def ListenEvents(self):
        self.ListenForEvent("neteaseShop", "neteaseShopDev", "ServerShipItemsEvent", self, self.ShipItemsEvent)

    def SendReceipt(self, playerId, orderId, suc=True):
        if suc:
            self.sendMsg('''
订单已完成 -- 本次的订单号为
%s
请将以上内容截图。发起投诉、补发，或退款时需要用到。  
请及时使用/eco查看您的钱包余额，或使用/cos检查库存。
商品的受理期为7个自然日。若需要补发或投诉，请立刻写邮件至service@icegame.xyz''' % orderId, playerId)
        else:
            self.sendMsg('''
§发货失败§r
您的账号不安全，无法发货。请立即处理您的账户。
使用/sudo了解如何保障您的账户安全。
本次的订单号为
%s
您已被扣款，但是商品尚未发货。请立即写邮件至service@icegame.xyz，使用该订单号补发。''' % orderId, playerId)

    def ShipItemsEvent(self, args):
        uid = args['uid']
        data = args['entities']

        playerId = lobbyGameApi.GetPlayerIdByUid(uid)
        cmd = data['cmd']

        ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')

        if cmd == 'buy.currency.8credits':

            sql = 'SELECT * FROM sudo WHERE uid=%s AND unsafe=0;'
            def Cb(args):
                if args:
                    ecoSystem.GivePlayerEco(uid, 8, 'buy 8credits', True)
                    self.SendReceipt(playerId, cmd)
                else:
                    self.SendReceipt(playerId, cmd, False)
                    sql = 'INSERT INTO reship (id, uid, date, pending) VALUES (%s, %s, %s, 1);'
                    mysqlPool.AsyncExecuteWithOrderKey('a07m8dsmg7nr89123', sql, (data['orderid'], uid, data['buytime']))
            mysqlPool.AsyncQueryWithOrderKey('asd0am121231', sql, (uid,), Cb)


    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("report", "reportClient", 'TestRequest', self, self.OnTestRequest)
