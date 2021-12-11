# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import math
import apolloCommon.commonNetgameApi as commonNetgameApi
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.mysqlPool as mysqlPool
import cosScript.cosConst as c
import json
import datetime
import random
import apolloCommon.redisPool as redisPool
redisPool.InitDB(30)

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()


# 在modMain中注册的Server System类
class cosSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        self.page = {}

        self.auth = {}
        self.pwdStatus = {}
        self.buffer = {}

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

    def forceSelect(self, slot, playerId):
        comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
        comp.ChangeSelectSlot(slot)

    def sendMsg(self, msg, playerId, suppressHint=False):
        comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
        comp.NotifyOneMessage(playerId, msg, "§f")
        if self.page[playerId] and not suppressHint:
            comp.NotifyOneMessage(playerId, 'READING>', "§f")

    def epoch2Datetime(self, epoch):
        ts = datetime.datetime.fromtimestamp(int(epoch)+0)
        return ts.strftime('%Y-%m-%d %H:%M:%S')

    def getCountInStr(self, string, target):
        count = 0
        for chr in string:
            if chr == target:
                count += 1

        return count

    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerChatEvent", self,
                            self.OnServerChat)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent",
                            self, self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent",
                            self, self.OnDelServerPlayer)

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        uid = lobbyGameApi.GetPlayerUid(playerId)

        self.page[playerId] = 0

        sql = 'SELECT unsafe FROM sudo WHERE uid=%s AND password!="0";'

        def Cb(args):
            if args:
                unsafe = args[0][0]
                if unsafe:
                    self.pwdStatus[playerId] = 2
                else:
                    self.pwdStatus[playerId] = 1
            else:
                self.pwdStatus[playerId] = 0

        mysqlPool.AsyncQueryWithOrderKey('sn90asd123', sql, (uid,), Cb)

        sql = 'DELETE FROM items WHERE uid=%s AND expire>-1 AND expire<%s;'
        mysqlPool.AsyncExecuteWithOrderKey('a9sdn70a9s67db9', sql, (uid, time.time()))

    def OnDelServerPlayer(self, data):
        playerId = data['id']

        if playerId in self.page:
            self.page.pop(playerId)
        if playerId in self.auth:
            self.auth.pop(playerId)
        if playerId in self.buffer:
            self.buffer.pop(playerId)

    def EnterCosMgr(self, playerId):
        uid = lobbyGameApi.GetPlayerUid(playerId)
        self.sendMsg(
            "§b>>>ICE_GAME商店与库存系统\n输入§rexit§b退出；输入§rprev§b回到上一级菜单；输入§rhelp§b或§rh§b获得帮助。\n当您看到§rREADING>§b时，您可以输入新的命令。\n\n",
            playerId, True)
        self.page[playerId] = 1
        self.sendMsg("§a输入start开始，输入任何其他字符退出。", playerId)

    def EmuServerChat(self, playerId, message, page, skipMsg=False, extraParams=None):
        self.page[playerId] = page
        self.OnServerChat({
            'playerId': playerId,
            'message': message,
            'skipMsg': skipMsg,
            'extra': extraParams
        })

    def OnServerChat(self, data):
        playerId = data['playerId']
        msg = data['message']

        self.sendCmd('/gamerule sendcommandfeedback false', playerId)

        page = self.page[playerId]
        if page:
            data['cancel'] = True

            # start processing

            if msg == 'exit':
                self.sendMsg('§b已退出。可以正常聊天了。<<<', playerId, True)
                self.page[playerId] = 0
                data['cancel'] = True
                return

            if page == 1:
                if msg == 'start':
                    self.page[playerId] = 2
                    self.sendMsg("§b请键入选项对应的§r字母§b：\n§rA - §b购买一件物品\n§rB - §b查看您的库存", playerId)
                else:
                    self.sendMsg('§b已退出。可以正常聊天了。<<<', playerId, True)
                    self.page[playerId] = 0

            elif page == 2:
                flag = msg.lower()

                if flag == 'prev':
                    self.EmuServerChat(playerId, 'start', 1)
                    return

                if flag == 'a':
                    self.page[playerId] = 10
                    self.sendMsg("§b请键入选项对应的§r字母§b：\n§rA - §b购买称号\n§rB - §b购买特权\n§rC - §b购买胜利音效\n§rD - §b购买自定义称号§c（暂不开放）", playerId)
                elif flag == 'b':
                    self.page[playerId] = 100
                    self.sendMsg("§b请键入选项对应的§r字母§b：\n§rA - §b称号\n§rB - §b特权\n§rC - §b胜利音效", playerId)
                else:
                    self.sendMsg('%s不是一个有效的命令； 输入exit退出', playerId)

            elif page == 10:
                flag = msg.lower()
                if self.pwdStatus[playerId] == 2:
                    self.sendMsg('cos: buy: permission denied', playerId)
                    self.EmuServerChat(playerId, 'start', 1)
                    return

                if flag == 'prev':
                    self.EmuServerChat(playerId, 'start', 1)
                    return

                if flag == 'a':
                    replaceSystem = serverApi.GetSystem('replaceWords', 'replaceWordsSystem')
                    labels = replaceSystem.consts['labels']
                    nobuy = replaceSystem.consts['prohibitedLabels']
                    if not ('skipMsg' in data) or (not data['skipMsg']):
                        msg = []
                        for index in labels:
                            if index in nobuy:
                                msg.append('%s %s§r (非卖品)' % (index, labels[index]))
                            else:
                                msg.append('%s %s§r' % (index, labels[index]))

                        for item in msg:
                            self.sendMsg(msg[msg.index(item)], playerId, True)
                        self.sendMsg('§b键入选项对应的§r数字§b以查看详情', playerId)
                    self.page[playerId] = 11
                elif flag == 'b':
                    self.sendMsg('§c抱歉，该选项暂不开放', playerId, True)
                    self.EmuServerChat(playerId, 'a', 2)
                    return
                elif flag == 'c':
                    musicSystem = serverApi.GetSystem('music', 'musicSystem')
                    musics = musicSystem.mvpList

                    for key in musics:
                        self.sendMsg('%s %s§r' % (key, musics[key]), playerId, True)
                    self.sendMsg('§b键入选项对应的§r数字§b以查看详情', playerId)
                    self.page[playerId] = 12

                # TODO Remove rebug if not fixed
                elif flag == 'd':
                    self.sendMsg('''§e§l自定义称号计价规则
§r128CREDITS/字，颜色符号本身免费。
最低3个字，最高12个字，不能包含空格。§l自定义称号永久有效。§r
§6自定义称号必须是独一无二的，否则将收取§l百分之433§r§6的费用。

§b请输入您想要购买的自定义称号。请自行复制颜色符号§\n
§l§4警告：§r§c 购买即表示您同意《ICE_GAME管理参考文档》。创建含有违规内容的称号可被永久封禁。
''', playerId)
                    self.page[playerId] = 22
                else:
                    self.sendMsg('%s不是一个有效的命令； 输入exit退出' % flag, playerId)

            elif page == 11:
                print 'chat page=11'
                flag = msg.lower()
                replaceSystem = serverApi.GetSystem('replaceWords', 'replaceWordsSystem')
                labels = replaceSystem.consts['labels']
                nobuy = replaceSystem.consts['prohibitedLabels']

                if flag == 'prev':
                    self.EmuServerChat(playerId, 'a', 2)
                    return

                item = flag
                try:
                    item = int(item)
                except ValueError:
                    self.sendMsg('%s不是一个有效的命令； 输入exit退出' % flag, playerId)
                    self.EmuServerChat(playerId, 'a', 10)
                    return

                if item < 1 or item not in labels.keys():
                    self.sendMsg('%s号物品不存在； 输入exit退出' % flag, playerId)
                    self.EmuServerChat(playerId, 'a', 10)
                    return

                if item in nobuy:
                    print '%s in %s' % (item, nobuy)
                    self.sendMsg('%s号物品是一个非卖品!' % flag, playerId)
                    self.EmuServerChat(playerId, 'a', 10, True)
                    return

                self.EmuServerChat(playerId, None, 20, False, {
                    'itemId': item
                })

            elif page == 20:
                replaceSystem = serverApi.GetSystem('replaceWords', 'replaceWordsSystem')
                labels = replaceSystem.consts['labels']
                if not msg:
                    self.buffer[playerId] = None
                if not msg:
                    self.buffer[playerId] = data['extra']['itemId']
                    print 'announcing item, set item(%s now) to %s' % (self.buffer[playerId], data['extra']['itemId'])
                    self.sendMsg("正在购买称号：%s" % labels[self.buffer[playerId]], playerId, True)
                    self.sendMsg(
                        "§b请键入选项对应的§r字母§b：\n§rA - §b购买24小时 28CREDITS\n§rB - §b购买7天 68CREDITS\n§rC - §b购买45天 298CREDITS\n§rD - §b购买永久 1288CREDITS\n§b或输入prev返回上级",
                        playerId)
                    return

                if msg == '#':
                    self.EmuServerChat(playerId, '%s' % self.buffer[playerId], 11)
                    return

                priceList = {
                    'a': 28,
                    'b': 68,
                    'c': 298,
                    'd': 1288
                }

                flag = msg.lower()
                if flag == 'prev':
                    self.EmuServerChat(playerId, '%s' % self.buffer[playerId], 11)
                    return

                if flag not in priceList.keys() and flag != '#':
                    self.sendMsg('%s不是一个有效的命令； 输入exit退出' % flag, playerId, True)
                    self.EmuServerChat(playerId, '#', 20, False)

                sql = 'SELECT high FROM eco WHERE uid=%s;'

                def Cb(args):
                    if not args:
                        self.sendMsg('Cannot ship: no player balance records!', playerId, True)
                        self.EmuServerChat(playerId, 'exit', 1)
                        return

                    credits = args[0][0]
                    price = priceList[flag]
                    if credits < price:
                        self.sendMsg('§c抱歉，您余额不足！', playerId, True)
                        self.EmuServerChat(playerId, '#', 20, False)
                        return

                    key = random.randint(10000000, 99999999)
                    params = (self.buffer[playerId], time.time(), key)
                    ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')
                    ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(playerId), -price, 'buy cos %s' % key, True)


                    if flag == 'a':
                        self.sendMsg(
                            "§b恭喜您，购买成功！以下是您的收据\n§rtype=称号 duration=1d itemId=%s time=%s key=%s\n§b该订单已被记录，您可以在24小时内使用收据中的§l§ekey§r§b发起CREDITS退款。\n§l请将本收据截图。" % params,
                            playerId, True)

                        sql = 'INSERT INTO items (uid, type, itemId, expire, inUse) VALUES (%s, "label", %s, %s, 0);'
                        mysqlPool.AsyncExecuteWithOrderKey('asd8ansds', sql, (
                            lobbyGameApi.GetPlayerUid(playerId), self.buffer[playerId], time.time() + 86400))
                    elif flag == 'b':
                        self.sendMsg(
                            "§b恭喜您，购买成功！以下是您的收据\n§rtype=称号 duration=7d itemId=%s time=%s key=%s\n§b该订单已被记录，您可以在24小时内使用收据中的§l§ekey§r§b发起CREDITS退款。\n§l请将本收据截图。" % params,
                            playerId, True)

                        sql = 'INSERT INTO items (uid, type, itemId, expire, inUse) VALUES (%s, "label", %s, %s, 0);'
                        mysqlPool.AsyncExecuteWithOrderKey('asd8ansds', sql, (
                            lobbyGameApi.GetPlayerUid(playerId), self.buffer[playerId], time.time() + 604800))
                    elif flag == 'c':
                        self.sendMsg(
                            "§b恭喜您，购买成功！以下是您的收据\n§rtype=称号 duration=45d itemId=%s time=%s key=%s\n§b该订单已被记录，您可以在24小时内使用收据中的§l§ekey§r§b发起CREDITS退款。\n§l请将本收据截图。" % params,
                            playerId, True)

                        sql = 'INSERT INTO items (uid, type, itemId, expire, inUse) VALUES (%s, "label", %s, %s, 0);'
                        mysqlPool.AsyncExecuteWithOrderKey('asd8ansds', sql, (
                            lobbyGameApi.GetPlayerUid(playerId), self.buffer[playerId], time.time() + 3880000))
                    elif flag == 'd':
                        self.sendMsg(
                            "§b恭喜您，购买成功！以下是您的收据\n§rtype=称号 duration=perm itemId=%s time=%s key=%s\n§b该订单已被记录，您可以在24小时内使用收据中的§l§ekey§r§b发起CREDITS退款。\n§l请将本收据截图。" % params,
                            playerId, True)

                        sql = 'INSERT INTO items (uid, type, itemId, expire, inUse) VALUES (%s, "label", %s, -1, 0);'
                        mysqlPool.AsyncExecuteWithOrderKey('asd8ansds', sql,
                                                           (lobbyGameApi.GetPlayerUid(playerId), self.buffer[playerId]))

                    self.EmuServerChat(playerId, 'a', 2)

                mysqlPool.AsyncQueryWithOrderKey('a9s8d7na9sbd6n0asd', sql, (lobbyGameApi.GetPlayerUid(playerId),), Cb)

            elif page == 22:
                label = msg
                if ' ' in label:
                    self.sendMsg('§e称号不能包含空格', playerId)
                    self.EmuServerChat(playerId, 'd', 2)
                    return
                elif not(3 <= len(label) <= 12):
                    self.sendMsg('§e称号不符合长度要求', playerId)
                    self.EmuServerChat(playerId, 'd', 2)
                    return
                elif not(commonNetgameApi.CheckNameValid(label)):
                    self.sendMsg('§e称号含有敏感词', playerId)
                    self.EmuServerChat(playerId, 'd', 2)
                    return

                sql = 'SELECT * FROM items WHERE type="label" AND itemId=0 AND extra="%s";'
                def Cb(args):
                    print 'checkcus args=,', args
                    self.sendMsg('正在购买称号：%s§r\n共%s个有效字符，收费%sCREDITS。' % (label, len(label.strip('§')), 128*len(label.strip('§'))), playerId, False)
                    if args:
                        price = math.floor(len(label.encode('utf-8')) - self.getCountInStr(label.encode('utf-8'), '§')) * 128 * 4.33
                        self.sendMsg('§e这是一个重复的称号！您需要额外支付333%的费用，共收费%sCREDITS。' % price, playerId)
                        print 'repeat label!'
                    else:
                        print 'not repeat label!'
                        price = 128*len(label.strip('§'))
                    self.sendMsg('§b是否购买这个称号？(y/n)', playerId)
                    self.page[playerId] = 23
                    redisPool.AsyncSet('cuslabel-price-buffer-%s' % lobbyGameApi.GetPlayerUid(playerId), "[%s, \"%s\"]" % (price, label))

                mysqlPool.AsyncQueryWithOrderKey('casd9702193', sql, (u'%s' % label, ), Cb)

            elif page == 23:
                flag = msg.lower()[0]
                if flag == 'y':
                    def Cb(args):
                        if not args:
                            self.sendMsg('ERROR: err_no_label_price: Custom label price missing or invalid', playerId)
                            self.EmuServerChat(playerId, 'start', 1)
                            return
                        key = random.randint(10000000, 99999999)
                        labelData = json.loads(args)
                        print 'cusargs=', labelData
                        ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')
                        ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(playerId), -labelData[0], 'buy custom lab %s' % key, True)
                        sql = 'INSERT INTO items (uid, type, itemId, expire, inUse, extra) VALUES (%s, "label", 0, -1, 0, "%s");'
                        mysqlPool.AsyncExecuteWithOrderKey('zxc89qw7e12', "DELETE FROM items WHERE type='label' AND itemId=0 AND extra=%s;", (labelData[1],))
                        mysqlPool.AsyncExecuteWithOrderKey('zxc89qw7e12', sql, (lobbyGameApi.GetPlayerUid(playerId), labelData[1].strip("'")))
                        self.sendMsg(
                            "§b恭喜您，购买成功！以下是您的收据\n§rtype=自定义称号 duration=perm itemId=0 time=%s key=%s\n§b该订单已被记录，您可以在24小时内使用收据中的§l§ekey§r§b发起CREDITS退款。\n§l请将本收据截图。" % (time.time(), key),
                            playerId, True)

                        self.EmuServerChat(playerId, 'start', 1)

                    redisPool.AsyncGet('cuslabel-price-buffer-%s' % lobbyGameApi.GetPlayerUid(playerId), Cb)
                elif flag == 'n':
                    redisPool.AsyncDelete('cuslabel-price-buffer-%s' % lobbyGameApi.GetPlayerUid(playerId))
                    self.EmuServerChat(playerId, 'd', 2)
                    return
                else:
                    self.sendMsg('%s不是一个有效的命令' % msg, playerId)
                    return

            elif page == 100:
                    flag = msg.lower()

                    print 'page 100'

                    if self.pwdStatus[playerId] == 2:
                        self.sendMsg('cos: inv: permission denied', playerId)
                        self.EmuServerChat(playerId, 'start', 1)
                        return

                    if flag == '#':
                        self.EmuServerChat(playerId, 'b', 2)
                        return

                    if flag == 'prev':
                        self.EmuServerChat(playerId, 'start', 1)
                        return

                    if flag == 'a':
                        self.sendMsg('正在加载您的库存...', playerId, True)
                        sql = 'SELECT itemId,expire,inUse FROM items WHERE uid=%s AND type="label" AND (expire<0 OR expire>=%s);'
                        def Cb(args):
                            if args:
                                replaceSystem = serverApi.GetSystem('replaceWords', 'replaceWordsSystem')
                                labels = replaceSystem.consts['labels']

                                labelList = []
                                for item in args:
                                    labelList.append((item[0], item[1], item[2]))

                                for item in labelList:
                                    print 'datagather = %s, %s' % (labels, item)
                                    if item[1] > 0:
                                        self.sendMsg("%s%s %s§r 至%s%s" % ('§e'*int(item[2]==1), item[0], labels[item[0]], self.epoch2Datetime(item[1]), ' （已装备）'*int(item[2]==1)), playerId, True)
                                    else:
                                        self.sendMsg("%s%s %s§r 永久%s" % ('§e'*int(item[2]==1), item[0], labels[item[0]], ' （已装备）'*int(item[2]==1)), playerId, True)

                                self.EmuServerChat(playerId, 'b', 101, False, labelList)

                            else:
                                self.sendMsg('§c抱歉，您的库存空空如也！', playerId, True)
                                self.EmuServerChat(playerId, 'start', 1)
                                return
                        mysqlPool.AsyncQueryWithOrderKey('as98m7ae6712903n1', sql, (lobbyGameApi.GetPlayerUid(playerId), time.time()), Cb)
                        self.sendMsg('输入物品编号来装备/卸下；输入#再次查看库存', playerId, True)
                    elif flag == 'c':
                        self.sendMsg('正在加载您的库存...', playerId, True)
                        sql = 'SELECT itemId,expire,inUse FROM items WHERE uid=%s AND type="mvp" AND (expire<0 OR expire>=%s);'
                        def Cb(args):
                            if args:
                                musicSystem = serverApi.GetSystem('music', 'musicSystem')
                                labels = musicSystem.mvpList

                                labelList = []
                                for item in args:
                                    labelList.append((item[0], item[1], item[2]))

                                for item in labelList:
                                    if item[1] > 0:
                                        self.sendMsg("%s%s %s§r 至%s%s" % ('§e'*int(item[2]==1), item[0], labels[item[0]], self.epoch2Datetime(item[1]), ' （已装备）'*int(item[2]==1)), playerId, True)
                                    else:
                                        self.sendMsg("%s%s %s§r 永久%s" % ('§e'*int(item[2]==1), item[0], labels[item[0]], ' （已装备）'*int(item[2]==1)), playerId, True)

                                self.EmuServerChat(playerId, 'b', 101, False, labelList)

                            else:
                                self.sendMsg('§c抱歉，您的库存空空如也！', playerId, True)
                                self.EmuServerChat(playerId, 'start', 1)
                                return
                        mysqlPool.AsyncQueryWithOrderKey('as98m7ae6712903n1', sql, (lobbyGameApi.GetPlayerUid(playerId), time.time()), Cb)
                        self.sendMsg('输入物品编号来装备/卸下；输入#再次查看库存', playerId, True)

            elif page == 101:
                flag = msg.lower()

                if flag == 'prev':
                    self.EmuServerChat(playerId, 'b', 2)
                    return

                if 'extra' in data:
                    if data['extra']:
                        self.buffer[playerId] = data['extra']

                replaceSystem = serverApi.GetSystem('replaceWords', 'replaceWordsSystem')
                labels = replaceSystem.consts['labels']

                labelList = self.buffer[playerId]

                try:
                    choice = int(flag)
                except ValueError:
                    if not 'extra' in data:
                        self.sendMsg('%s不是一个有效的命令' % msg, playerId)
                        return

                if not choice in labels:
                    self.sendMsg('您没有该物品的使用权！', playerId)
                    return

                uid = lobbyGameApi.GetPlayerUid(playerId)
                sql = [
                    'UPDATE items SET inUse=0 WHERE uid=%s AND type="label";',
                    'UPDATE items SET inUse=1 WHERE uid=%s AND type="label" AND inUse=0 AND itemId=%s;'
                ]
                mysqlPool.AsyncExecuteWithOrderKey('8qa0sdm7asd', sql[0], (uid,))
                mysqlPool.AsyncExecuteWithOrderKey('8qa0sdm7asd', sql[1], (uid, choice))
                self.sendMsg('操作成功。一些设置需在重新进入服务器后生效。', playerId, True)

                self.EmuServerChat(playerId, 'b', 2)

            elif page == 102:
                flag = msg.lower()

                if flag == 'prev':
                    self.EmuServerChat(playerId, 'b', 2)
                    return

                if 'extra' in data:
                    if data['extra']:
                        self.buffer[playerId] = data['extra']

                musicSystem = serverApi.GetSystem('music', 'musicSystem')
                labels = musicSystem.mvpList

                labelList = self.buffer[playerId]

                try:
                    choice = int(flag)
                except ValueError:
                    if not 'extra' in data:
                        self.sendMsg('%s不是一个有效的命令' % msg, playerId)
                        return

                if not choice in labels:
                    self.sendMsg('您没有该物品的使用权！', playerId)
                    return

                uid = lobbyGameApi.GetPlayerUid(playerId)
                sql = [
                    'UPDATE items SET inUse=0 WHERE uid=%s AND type="mvp";',
                    'UPDATE items SET inUse=1 WHERE uid=%s AND type="mvp" AND inUse=0 AND itemId=%s;'
                ]
                mysqlPool.AsyncExecuteWithOrderKey('8qa0sdm7asd', sql[0], (uid,))
                mysqlPool.AsyncExecuteWithOrderKey('8qa0sdm7asd', sql[1], (uid, choice))
                self.sendMsg('操作成功。一些设置需在重新进入服务器后生效。', playerId, True)

                self.EmuServerChat(playerId, 'b', 2)

                    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("report", "reportClient", 'TestRequest', self, self.OnTestRequest)
