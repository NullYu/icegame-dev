# -*- coding: utf-8 -*-
import mod.server.extraServerApi as serverApi
import apolloCommon.commonNetgameApi as commonNetgameApi
import apolloCommon.mysqlPool as mysqlPool
import time
import datetime
import replaceScript.replaceConst as c
import lobbyGame.netgameApi as lobbyGameApi

ServerSystem = serverApi.GetServerSystemCls()
ecoSystem = serverApi.GetSystem("eco", "ecoSystem")
mysqlPool.InitDB(30)

####################
enableReplace = False
labels = c.labels
#########################

class replaceWordServerSys(ServerSystem):
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        # 初始时调用监听函数监听事件
        # 第一个参数是namespace，表示客户端名字空间，第二个是客户端System名称，第三个是监听事件的名字，第五个参数是回调函数（或者监听函数）
        self.ListenEvents()

        self.db = {}
        self.cd = {}

        self.consts = {
            'labels': labels,
            'prohibitedLabels': c.prohibitedLabels
        }

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerChatEvent", self,
                            self.OnServerChat)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self,
                            self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent",
                            self,
                            self.OnDelServerPlayer)

    def epoch2Datetime(self, epoch):
        ts = datetime.datetime.fromtimestamp(int(epoch)+0)
        return ts.strftime('%Y-%m-%d %H:%M:%S')

    def OnAddServerPlayer(self, data):
        playerId = data['id']
        uid = lobbyGameApi.GetPlayerUid(playerId)

        # [prefix, label, postfix]
        self.db[playerId] = ['', '', '']

        sql = 'SELECT type FROM perms WHERE uid=%s AND (type>=95 OR 2<=type<=6);'
        def Cb(args):
            if args:
                type = args[0][0]
                print 'OnServerChat/CheckPerms playerId=' + str(playerId) + ' args=' + str(args)

                titleList = {
                    # TODO Add more vip prefixes
                    2: '§l§bEP',
                    95: '§l§aTrainee§r',
                    96: '§l§eMod§r',
                    97: '§l§6Sr.Mod§r',
                    98: '§l§cAdmin§r',
                    99: ''
                }

                if type in titleList:
                    self.db[playerId][0] = "§l§6►§r"*int(type>=95) + titleList[type]
                print 'setting db to %s' % self.db[playerId][0]
        mysqlPool.AsyncQueryWithOrderKey("OnServerChat/CheckPerms", sql,
                                         (uid,),
                                         Cb)

        sql = "SELECT type,itemId,extra FROM items WHERE uid=%s AND inUse=1 AND (expire>=%s OR expire<0);"

        def Cb2(args):
            print 'Checked for label! args=%s' % (args,)
            if args:
                data = args[0]
                typ = data[0].encode('utf-8')
                itemId = int(str(data[1]).strip("L"))
                if typ == 'label':
                    if itemId in labels.keys():
                        self.db[playerId][1] = labels[itemId]
                        def a(player):
                            comp = serverApi.GetEngineCompFactory().CreateName(player)
                            suc = comp.SetPlayerPrefixAndSuffixName("%s" % labels[itemId],serverApi.GenerateColor('RED'),'',serverApi.GenerateColor('RED'))
                            print 'setPrefix suc=%s' % suc
                        commonNetgameApi.AddTimer(3.0, a, playerId)
                    elif itemId == 0:
                        # Customized label
                        self.db[playerId][1] = data[2].encode('utf-8')
                        def a(player):
                            comp = serverApi.GetEngineCompFactory().CreateName(player)
                            suc = comp.SetPlayerPrefixAndSuffixName("%s" % self.db[playerId][1].encode('utf-8'), serverApi.GenerateColor('RED'),'',serverApi.GenerateColor('RED'))
                            print 'setPrefix suc=%s' % suc
                        commonNetgameApi.AddTimer(3.0, a, playerId)
                    else:
                        print 'OnServerChat/Cb2 itemId NOT IN labels! itemId=%s' % (itemId,)

        mysqlPool.AsyncQueryWithOrderKey("OnServerChat/CheckLabel", sql, (uid, time.time()), Cb2)

    def OnDelServerPlayer(self, data):
        playerId = data['id']

        if playerId in self.db:
            self.db.pop(playerId)
        if playerId in self.cd:
            self.cd.pop(playerId)

    def reformatMsg(self, msg, senderId, prefix, label, postfix):
        li = serverApi.GetPlayerList()
        for player in li:
            comp = serverApi.GetEngineCompFactory().CreateMsg(senderId)
            comp.NotifyOneMessage(player, prefix+label+"§r§3"+senderId+": §7"+postfix+msg, "§3")

    def process(self, msg):
        con = c.replaceWords
        words = []
        lines = con.split('\n')
        for line in lines:
            words.append(line.split())

        result = msg

        for line in words:
            for i in range(len(line)-1):
                result = result.replace(line[i+1], line[0])

        return result

    def OnServerChat(self, args):

        exclude = ['testui']

        print 'server=%s' % commonNetgameApi.GetServerType()
        if 'bw' in commonNetgameApi.GetServerType():
            print 'no msg for bw'
            return

        playerId = args['playerId']
        playerNickname = lobbyGameApi.GetPlayerNickname(playerId)
        uid = lobbyGameApi.GetPlayerUid(playerId)
        msg = args["message"]
        if msg in exclude:
            print 'msg in exclude, not processing! msg=', msg
            return

        cosSystem = serverApi.GetSystem('cos', 'cosSystem')
        if playerId not in cosSystem.page or not cosSystem.page[playerId]:
            args["cancel"] = True
        else:
            return

        if len(msg) > 40:
            self.cd[playerId] = 600

        if playerId in self.cd and self.cd[playerId] > time.time():
            self.cd[playerId] += 1
            comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
            comp.NotifyOneMessage(playerId, "发言冷却中，请等待一会后再试", "§3")
            return

        sql = 'SELECT endDate,reason FROM muteData WHERE uid=%s AND (endDate>%s OR endDate<0);'
        def Cb(data):
            if data:
                end = data[0][0]
                reason = data[0][1]

                if end > 0:
                    comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
                    comp.NotifyOneMessage(playerId, "您被禁言至%s" % (self.epoch2Datetime(end),), "§3")
                else:
                    comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
                    comp.NotifyOneMessage(playerId, "您被永久禁言。祝你快乐。", "§3")

            else:
                if enableReplace:
                    # msg = self.replaceWords(args["message"])
                    pass

                else:
                    msgOk = commonNetgameApi.CheckWordsValid(args["message"])
                    print 'OnServerChat/CheckWordsValid playerId='+playerNickname+' message='+msg+' pass='+str(msgOk)
                    if msgOk:
                        self.reformatMsg(msg.replace('§', '§3'), playerNickname, self.db[playerId][0], self.db[playerId][1], self.db[playerId][2])
                        self.cd[playerId] = time.time()+3
                    else:
                        comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
                        comp.NotifyOneMessage(playerId, "不允许发送该消息，请检查", "§3")
        mysqlPool.AsyncQueryWithOrderKey("d78astd7absdn1", sql, (uid, time.time()+0), Cb)

    def Destroy(self):
        self.UnListenForEvent("q", "qClient", 'TestRequest', self, self.OnTestRequest)