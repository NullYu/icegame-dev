# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import random
import json
import ecoScript.ecoConsts as vars
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.redisPool as redisPool
import apolloCommon.commonNetgameApi as commonNetgameApi
import apolloCommon.mysqlPool as mysqlPool
from mod_log import logger
mysqlPool.InitDB(30)

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

# Variable defines
createPwdConf = {}

# 在modMain中注册的Server System类
class ecoSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self,
                            self.OnCommand)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self, self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self, self.OnDelServerPlayer)
        self.ListenForEvent('eco', 'ecoClient', 'SudoReturnEvent', self, self.OnSudoReturn)
        self.ListenForEvent("neteaseShop", "neteaseShopDev", "ServerShipItemsEvent", self, self.ShipItemsEvent)

        self.bank = {}

    ##############UTILS##############

    def sendCmd(self, cmd, playerId):
        comp = serverApi.GetEngineCompFactory().CreateCommand(serverApi.GetLevelId())
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

    def sendMsg(self, msg, playerId):
        comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
        comp.NotifyOneMessage(playerId, msg, "§f")

    def forceSelect(self, slot, playerId):
        # print 'forceSelect called slot='+slot+' playerId='+playerId
        comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
        comp.ChangeSelectSlot(slot)

    #################################

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("lobbyutils", "lobbyutilsClient", 'TestRequest', self, self.OnTestRequest)

    def OnDelServerPlayer(self, data):
        playerId = data['id']
        if playerId in self.bank:
            self.bank.pop(playerId)

    # diamond shop shippping

    def SendReceipt(self, playerId, orderId, suc=True):
        if suc:
            self.sendMsg('''
订单已完成 -- 本次的订单号为
%s
请将以上内容截图。发起投诉、补发，或退款时需要用到。
§e若您购买了优先队列，您必须重新进入服务器。§f
请及时使用/eco查看您的钱包余额，或使用/cos检查库存。
商品的受理期为7个自然日。若需要补发或投诉，请立刻写邮件至service@icegame.xyz''' % str(orderId).encode('utf-8'), playerId)
        else:
            self.sendMsg('''
§c发货失败§r
您的账号不安全，无法发货。请立即处理您的账户。
使用/sudo了解如何保障您的账户安全。
本次的订单号为
%s
§e您已被扣款，但是商品尚未发货。请立即写邮件至service@icegame.xyz，使用该订单号补发。''' % str(orderId).encode('utf-8'), playerId)

    def ShipItemsEvent(self, args):

        logger.info('bought %s' % args)

        redisPool.AsyncSet('shoptest', str(args))
        uid = args['uid']
        mData = args['entities']

        playerId = lobbyGameApi.GetPlayerIdByUid(uid)
        for data in mData:
            cmd = data['cmd']

            ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')

            if 'buy.currency.' in cmd:

                amount = int(cmd.replace('buy.currency.', '').replace('credits', ''))

                sql = 'SELECT * FROM sudo WHERE uid=%s AND unsafe=0;'

                def Cb(args):
                    if args:
                        ecoSystem.GivePlayerEco(uid, amount, 'buy %scredits' % amount, True)
                        self.SendReceipt(playerId, data['orderid'])
                    else:
                        self.SendReceipt(playerId, data['orderid'], False)
                        sql = 'INSERT INTO reship (id, uid, date, pending) VALUES (%s, %s, %s, 1);'
                        mysqlPool.AsyncExecuteWithOrderKey('a07m8dsmg7nr89123', sql,
                                                           (data['orderid'], uid, data['buytime']))

                mysqlPool.AsyncQueryWithOrderKey('asd0am121231', sql, (uid,), Cb)

            elif 'buy.ep.' in cmd:
                cmd = cmd.replace('buy.ep.', '').split()
                level = int(cmd[0])

                sql = 'SELECT * FROM sudo WHERE uid=%s AND unsafe=0;'

                def Cb():
                    if args:
                        mysqlPool.AsyncExecuteWithOrderKey('zxc9ad0123',
                                                           "INSERT INTO perms VALUES (uid, type, endDate) VALUES (%s, %s, %s);",
                                                           (uid, (level+1), time.time()+2592000))
                        self.SendReceipt(playerId, data['orderid'])

                        # TODO As of 22JUL: Delete gifted random song
                        sql = 'INSERT INTO items (uid, type, itemId, expire) VALUES (%s, "mvp", %s, %s);'
                        mysqlPool.AsyncExecuteWithOrderKey('zxc978qe09123123', sql, (uid, random.randint(1, 13), time.time() + 1209600))

                    else:
                        self.SendReceipt(playerId, data['orderid'], False)
                        sql = 'INSERT INTO reship (id, uid, date, pending) VALUES (%s, %s, %s, 1);'
                        mysqlPool.AsyncExecuteWithOrderKey('a07m8dsmg7nr89123', sql,
                                                           (data['orderid'], uid, data['buytime']))

                mysqlPool.AsyncQueryWithOrderKey('asdasdasdasd', sql, (uid,), Cb)

            elif 'buy.mvp.' in cmd:
                cmd = cmd.replace('buy.mvp.', '').split()
                id = int(cmd[0])

                sql = 'SELECT * FROM sudo WHERE uid=%s AND unsafe=0;'
                def Cb():
                    if args:
                        if len(cmd) > 1:
                            expire = cmd[1]
                        else:
                            mysqlPool.AsyncExecuteWithOrderKey('zxc9ad0123', "INSERT INTO items VALUES (uid, type, itemId, expire) VALUES (%s, 'mvp', %s, -1);", (uid, id))
                        self.SendReceipt(playerId, data['orderid'])
                    else:
                        self.SendReceipt(playerId, data['orderid'], False)
                        sql = 'INSERT INTO reship (id, uid, date, pending) VALUES (%s, %s, %s, 1);'
                        mysqlPool.AsyncExecuteWithOrderKey('a07m8dsmg7nr89123', sql,
                                                           (data['orderid'], uid, data['buytime']))
                mysqlPool.AsyncQueryWithOrderKey('asdasdasdasd', sql, (uid,), Cb)

            elif 'buy.prioq' in cmd:
                sql = 'INSERT INTO items (uid, type, itemId, endDate, inUse) VALUES (%s, "prioq", 0, %s, 1);'
                mysqlPool.AsyncExecuteWithOrderKey('prioqbuyQ%s' % uid, sql, (uid, time.time()+2592000))

            neteaseShopServerSystem = serverApi.GetSystem("neteaseShop", "neteaseShopDev")
            response = {
                'uid': uid,
                'entities': mData
            }
            neteaseShopServerSystem.ShipOrderSuccess(response)

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        uid = data['uid']

        createPwdConf[playerId] = 0

        sql = 'SELECT nickname,password FROM sudo WHERE uid=%s;'
        def Cb(args):
            if args:
                data = args[0]

                nickname = data[0].strip("'").strip('u')
                password = data[1].strip("'").strip('u')
                if not(nickname == lobbyGameApi.GetPlayerNickname(playerId)):
                    sql = "UPDATE sudo SET nickname='%s' WHERE uid=%s;"
                    def Cb1(args):
                        pass
                    mysqlPool.AsyncExecuteWithOrderKey('OnAddServerPlayer/UpdateNickname', sql, (nickname, uid), Cb1)

                def a(playerId):
                    self.sendMsg("\n§l§c注意！§r您还没有设置§l独立密码§r。\n该密码将保护您的账户不被不法分子盗用。\n在设置密码前，§e您收到的任何钱款将作废§f，转账也将被退回。\n现在使用§b/sudo§f了解如何创建密码！", playerId)
                if password == '0':
                    commonNetgameApi.AddTimer(10.0, a, playerId)

            else:
                sql = "INSERT INTO sudo (uid, nickname) VALUES (%s, %s);"
                def Cb2(args):
                    pass
                mysqlPool.AsyncExecuteWithOrderKey('OnAddServerPlayer/CreatePlayerProfile', sql, (uid, lobbyGameApi.GetPlayerNickname(playerId)), Cb2)
                def b(playerId):
                    self.sendMsg("\n§l§c注意！§r您还没有设置§l独立密码§r。\n该密码将保护您的账户不被不法分子盗用。\n在设置密码前，§e您收到的任何钱款将作废§f，转账也将被退回。\n现在使用§b/sudo§f了解如何创建密码！", playerId)
                commonNetgameApi.AddTimer(10.0, b, playerId)

        mysqlPool.AsyncQueryWithOrderKey('OnAddServerPlayer/CheckIfProfileExist', sql, (uid,), Cb)

        sql = 'SELECT neko,high FROM eco WHERE uid=%s;'
        def Cb3(args):
            if not args:
                sql = 'INSERT INTO eco (uid) VALUES (%s);'
                def Cb4(args):
                    pass
                mysqlPool.AsyncExecuteWithOrderKey('OnAddServerPlayer/CreatePlayerEcoProfile', sql, (uid,), Cb4)
            else:
                neko = args[0][0]
                credits = args[0][1]
                self.bank[playerId] = [neko, credits]
        mysqlPool.AsyncQueryWithOrderKey('OnAddServerPlayer/CheckIfEcoProfileExist', sql, (uid,), Cb3)

    def OnSudoReturn(self, data):
        print 'OnSudoReturn data=%s' % (data,)
        mode = data['mode']
        playerId = data['playerId']
        uid = lobbyGameApi.GetPlayerUid(playerId)

        if mode == 'change':
            newpassword = data['password']
            sql = "UPDATE sudo SET password=%s,lastAccess=%s,unsafe=0,changeKey='0' WHERE uid=%s"
            mysqlPool.AsyncExecuteWithOrderKey('OnSudoReturn/ChangePwd', sql, (newpassword, time.time(), uid))

            self.sendMsg("\n§b成功创建独立密码。\n如果您的账号开启了安全锁，其已被关闭。\n您必须牢记该密码。\n§b若遗忘密码或想更改请发送邮件：\nservice@icegame.xyz\n\n", playerId)

        elif mode == 'lock':
            sql = "UPDATE sudo SET lastAccess=%s,unsafe=1 WHERE uid=%s"
            mysqlPool.AsyncExecuteWithOrderKey('OnSudoReturn/Lock', sql, (time.time(), uid))

            self.sendMsg("\n§e§l账号安全锁已启动\n§r您的账号将不再能够收款或付款，直到\n该状态解除。\n使用§b/sudo§r查看账号状态\n§b想解锁？发送邮件至\nservice@icegame.xyz\n\n", playerId)

    def OnCommand(self, data):
        playerId = data['entityId']
        uid = lobbyGameApi.GetPlayerUid(playerId)
        msg = data['command'].split()
        cmd = msg[0].strip('/')

        if cmd == 'eco':
            data['cancel'] = True

            if len(msg) == 1:
                if playerId in self.bank:
                    data = self.bank[playerId]
                    neko = str(data[0])
                    high = str(data[1])
                    self.sendMsg("\n§b§l我的钱包余额\n§rNEKO: §e"+neko+"\n§fCREDITS: §e"+high+"\n§f使用§b/eco -h§f查看帮助\n\n", playerId)
            elif msg[1] == "-h":
                self.sendMsg("§beco - 玩家经济\n§r§l/eco -dt [selectorData] [selectorData2] [selectorData3] [extraFlag] [extraFlag2]\n§r§b访问t.im/commands了解详情", playerId)
            else:
                self.sendMsg("§c无效的命令。使用/eco -h查看帮助。", playerId)

        elif cmd == 'sudo':
            data['cancel'] = True

            if len(msg) == 1:
                sql = "SELECT password,lastAccess,unsafe,changeKey FROM sudo WHERE uid=%s"
                def Cb(args):
                    data = args[0]
                    if data:
                        password = data[0]
                        lastAccess = int((data[1]))
                        # if not lastAccess == 0:
                        #     lastAccess = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(int(lastAccess+0)))
                        unsafe = int((data[2]))
                        changekey = data[3]

                        response = {
                            'uid': uid,
                            'password': password,
                            'lastAccess': lastAccess,
                            'unsafe': unsafe,
                            'changekey': changekey
                        }
                        self.NotifyToClient(playerId, "OpenPanelEvent", response)
                        print 'Notify'
                        # if password == '0':
                        #     self.sendMsg("\n§l§b您的独立密码状态\n§r§3密码：§c§l未设置\n§r请尽快设置密码，以免造成不必要的损失\n§b使用/sudo -h查看帮助\n\n", playerId)
                        # else:
                        #     if unsafe:
                        #         self.sendMsg("\n§l§b您的独立密码状态\n§r§3密码：§e§l不安全\n§r§3上一次输入密码:"+str(lastAccess)+"\n§e该账号不能收付款\n§3该账号处于\"不安全\"状态。请联系service@icegame.xyz解除\n§b使用/sudo -h查看帮助\n\n",
                        #                      playerId)
                        #     else:
                        #         self.sendMsg("\n§l§b您的独立密码状态\n§r§3密码：§a§l正常\n§r§3上一次输入密码:" + str(
                        #             lastAccess) + "\n§b使用/sudo -h查看帮助\n\n",
                        #                      playerId)
                mysqlPool.AsyncQueryWithOrderKey('OnCommand/QuerySudoStatus', sql, (uid,), Cb)


            elif len(msg) > 1 and msg[1] == '-h':
                self.sendMsg("§bsudo - 独立密码管理\n§r§l/sudo -chlv [selectorData] [selectorData2]\n§r创建/更换密码 /sudo -c <新密码> [密码更换授权码]*\n§7显示本帮助页面 /sudo -h\n§r将账号切换为不安全状态 /sudo -l <独立密码>\n§7检查自己是否记得密码 /sudo -v <独立密码>\n§r*新创建密码无需填写密码更换授权码\n§b访问t.im/commands了解更多", playerId)
            elif len(msg) > 1 and len(msg) < 5 and msg[1] == '-c':

                sql = 'SELECT password,changeKey FROM sudo WHERE uid=%s'
                def Cb(args):
                    if args:
                        data = args[0]
                        password = data[0]

                        if len(msg) == 3 and not(password == '0'):
                            self.sendMsg("请提供密码更换授权码！\n§b不知道这是什么？访问t.im/commands", playerId)
                            return
                        elif len(msg) == 4 and password == '0':
                            self.sendMsg("新建密码无需提供授权码。\n请使用§b/sudo -c <新密码>", playerId)
                            return

                        #Create new pwd
                        if len(msg) == 3:
                            pwd = msg[2]

                            if len(pwd)<6 or len(pwd)>24 or '§' in pwd:
                                self.sendMsg(
                                    "§e密码长度必须在7~24，并且不包含颜色代码符§", playerId)
                                return

                            sql = 'UPDATE sudo SET password=%s,lastAccess=%s,unsafe=0 WHERE uid=%s'
                            def Cb2(args):
                                pass
                            mysqlPool.AsyncExecuteWithOrderKey('OnAddServerPlayer/CreatePlayerEcoProfile', sql,(pwd, time.time(), uid), Cb2)
                            self.sendMsg("\n§b成功创建独立密码\n§3密码是: §r"+pwd+"\n您必须牢记该密码。\n§b若遗忘密码或想更改请发送邮件：\nservice@icegame.xyz\n\n", playerId)

                        elif len(msg) == 4:
                            pwd = msg[2]
                            key = msg[3]
                            if key == '0':
                                self.sendMsg("sudo: Sorry, try again", playerId)
                                return
                            sql = 'SELECT * FROM sudo WHERE uid=%s and changeKey=%s'
                            def Cb3(args):
                                if args:
                                    if len(pwd) < 6 or len(pwd) > 24 or '§' in pwd:
                                        self.sendMsg(
                                            "§e密码长度必须在7~24，并且不包含颜色代码符§", playerId)
                                        return

                                    sql = 'UPDATE sudo SET password=%s,lastAccess=%s,changeKey=0,unsafe=0 WHERE uid=%s'

                                    def Cb4(args):
                                        pass

                                    mysqlPool.AsyncExecuteWithOrderKey('OnAddServerPlayer/CreatePlayerEcoProfile', sql,
                                                                       (pwd, time.time(), uid), Cb4)
                                    self.sendMsg(
                                        "\n§b成功创建独立密码\n§3密码是: §r" + pwd + "\n您必须牢记该密码。\n§b若遗忘密码或想更改请发送邮件：\nservice@icegame.xyz\n\n",
                                        playerId)
                                else:
                                    self.sendMsg("sudo: Sorry, try again", playerId)
                                    return
                            mysqlPool.AsyncQueryWithOrderKey('OnCommand/CheckIfChangeKey', sql, (uid,key), Cb3)
                    else:
                        print 'eco OnCommand/RequestCreateNewPassword UID NOT IN DB! uid='+str(uid)
                mysqlPool.AsyncQueryWithOrderKey('OnCommand/RequestCreateNewPassword', sql, (uid,), Cb)

            elif len(msg) == 3 and msg[1] == '-v':
                pwd = msg[2]
                sql = 'SELECT password FROM sudo WHERE uid=%s'
                def Cb(args):
                    if args:
                        data = args[0]
                        password = data[0].strip("u").strip("'")
                        if password == '0':
                            self.sendMsg("§e您还没有创建独立密码。\n§f使用§b/sudo§f了解如何创建", playerId)
                        elif password == pwd:
                            self.sendMsg("password OK", playerId)
                            sql = 'UPDATE sudo SET lastAccess=%s WHERE uid=%s'
                            def Cb2(args):
                                pass
                            mysqlPool.AsyncExecuteWithOrderKey('OnAddServerPlayer/UpdateTime', sql,
                                                               (time.time(), uid), Cb2)
                        else:
                            self.sendMsg("sudo: Sorry, try again", playerId)
                mysqlPool.AsyncQueryWithOrderKey('OnCommand/RequestVerifyPassword', sql, (uid,), Cb)

            elif len(msg)<4 and msg[1] == "-l":
                if len(msg) < 3:
                    self.sendMsg("sudo: Permission denied", playerId)
                    return
                pwd = msg[2]
                sql = 'SELECT password,unsafe FROM sudo WHERE uid=%s'
                def Cb(args):
                    if args:
                        data = args[0]
                        password = data[0].strip("u").strip("'")
                        unsafe = int(str(data[1]).strip("L"))
                        if unsafe or password=='0':
                            self.sendMsg("sudo: Operation not permitted", playerId)
                            return
                        if password == pwd:
                            self.sendMsg("\n§e§l账号安全锁已启动\n§r您的账号将不再能够收款或付款，直到\n该状态解除。\n使用§b/sudo§r查看账号状态\n§b想解锁？发送邮件至\nservice@icegame.xyz\n\n", playerId)
                            sql = 'UPDATE sudo SET unsafe=1,lastAccess=%s WHERE uid=%s'
                            def Cb2(args):
                                pass

                            mysqlPool.AsyncExecuteWithOrderKey('OnAddServerPlayer/UpdateAccountLock', sql,
                                                               (time.time(),uid), Cb2)
                        else:
                            self.sendMsg("sudo: Sorry, try again", playerId)
                mysqlPool.AsyncQueryWithOrderKey('OnCommand/RequestVerifyPassword', sql, (uid,), Cb)

            else:
                self.sendMsg("§c无效的命令。使用/sudo -h查看帮助。", playerId)

    # ###System Api### #

    # ecoSystem = serverApi.GetSystem("eco", "ecoSystem")

    def GivePlayerItem(self, uid, itemType, itemId, expire=-1, equipNow=False):
        playerId = lobbyGameApi.GetPlayerIdByUid(uid)
        sql = 'INSERT INTO items (uid, type, itemId, expire, inUse) VALUES (%s, %s, %s, %s, %s);'
        mysqlPool.AsyncExecuteWithOrderKey("GivePlayerItem/InsertNewItem", sql, (uid, itemType, itemId, expire, int(equipNow)))

    def EquipPlayerItem(self, inUse, uid, itemType='', itemId=0, id=0):
        sql = 'UPDATE items SET inUse=0 WHERE uid=%s;'
        mysqlPool.AsyncExecuteWithOrderKey("EquipPlayerItem/UnequipFirstPlayerAllItems", sql, (uid,))
        if id:
            sql = 'UPDATE items SET inUse=%s WHERE id=%s;'
            def Cb(args):
                return args
            mysqlPool.AsyncExecuteWithOrderKey("EquipPlayerItem/UsingItemUniqueId", sql, (int(inUse), id), Cb)
        else:
            sql = 'UPDATE items SET inUse=%s WHERE uid=%s,itemType=%s,itemId=%s;'
            def Cb(args):
                return args
            mysqlPool.AsyncExecuteWithOrderKey("EquipPlayerItem/UsingItemAttrs", sql, (int(inUse), uid, itemType, itemId), Cb)

    def GivePlayerEco(self, uid, amount, reason, useCredits=False):
        # Return Codes
        # 0=OK
        # 1=password not set or unsafe
        # 2=not enough money
        # Only code 0 is OK
        playerId = lobbyGameApi.GetPlayerIdByUid(uid)
        sql = "SELECT * FROM sudo WHERE uid=%s and password!='0' and unsafe=0;"

        if not useCredits:
            sql = "UPDATE eco SET neko=neko+%s WHERE uid=%s;"
            mysqlPool.AsyncExecuteWithOrderKey('GivePlayerEco/UpdateEco', sql, (amount, uid))
            sql = "INSERT INTO ecologs (uid, amount, reason, date) VALUES (%s, %s, %s, %s);"
            mysqlPool.AsyncExecuteWithOrderKey('GivePlayerEco/InsertIntoEcologs', sql,
                                               (uid, amount, reason, time.time()))
        else:
            sql = "UPDATE eco SET high=high+%s WHERE uid=%s;"
            mysqlPool.AsyncExecuteWithOrderKey('GivePlayerEco/UpdateEco', sql, (amount, uid))
            sql = "INSERT INTO ecologs (uid, type, amount, reason, date) VALUES (%s, 1, %s, %s, %s);"
            mysqlPool.AsyncExecuteWithOrderKey('GivePlayerEco/InsertIntoEcologs', sql,
                                               (uid, amount, reason, time.time()))