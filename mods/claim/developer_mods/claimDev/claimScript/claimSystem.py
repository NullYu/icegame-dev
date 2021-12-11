# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 这行import到的是引擎服务端的API模块
import server.extraServerApi as serverApi
import time
import apolloCommon.commonNetgameApi as commonNetgameApi
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.mysqlPool as mysqlPool

# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
ServerSystem = serverApi.GetServerSystemCls()

# 在modMain中注册的Server System类
class claimSystemSys(ServerSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        self.confirm = {}

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

    def sendMsg(self, msg, playerId):
        comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
        comp.NotifyOneMessage(playerId, msg, "§f")
    #################################

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "CommandEvent", self, self.OnCommand)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent", self, self.OnAddServerPlayerEvent)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self, self.OnDelServerPlayerEvent)

    def OnAddServerPlayerEvent(self, data):
        playerId = data['id']
        self.confirm[playerId] = False

    def OnDelServerPlayerEvent(self, data):
        playerId = data['id']
        if playerId in self.confirm:
            self.confirm.pop(playerId)

    def OnCommand(self, data):
        playerId = data['entityId']
        uid = lobbyGameApi.GetPlayerUid(playerId)
        cmd = data['command'].split()
        validCmd = ["/claim"]
        if cmd[0] in validCmd:
            data['cancel'] = True

            if len(cmd) == 1:

                if self.confirm[playerId]:
                    # TODO Current event: Qixi event [leave one week for event signins]
                    sql = 'SELECT done FROM e1 WHERE uid=%s AND checkin>=7;'
                    def Cb(args):
                        if args:
                            isDone = args[0][0]
                            if isDone:
                                self.sendMsg('§l§c您已经领取过这个礼包了。不能贪心。', playerId)
                                return
                            else:
                                # TODO Process claim req
                                pass
                        else:
                            self.sendMsg('§l§c您不满足领取条件！§r§f查看介绍图片了解如何领取该礼包！', playerId)
                            return
                    mysqlPool.AsyncQueryWithOrderKey('asd98p8u2p3123', sql, (uid,), Cb)

                    self.confirm[playerId] = False
                else:
                    self.sendMsg("§e再次执行命令以确认。断开连接或输入/claim -c以取消。\nRe-issue command to confirm. Disconnect or do </claim -c> to cancel", playerId)
                    self.confirm[playerId] = True

            else:
                kw = cmd[2]
                if kw == '-h'.lower():
                    self.sendMsg('§bclaim - 领取一个活动礼品或礼包\n§*你应该在正常渠道不可用时使用本命令\n§f/claim -ch --cancel --help\n§7输入两次本命令以确认领取',
                                 playerId)
                    return
                elif kw.lower() == '-c' or '--cancel':
                    if playerId in self.confirm and self.confirm[playerId]:
                        self.confirm[playerId] = False
                        self.sendMsg('§b已成功解除领取确认。', playerId)
                    else:
                        self.sendMsg('§e您没有领取一个礼包或奖品', playerId)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        # 注销监听事件
        self.UnListenForEvent("report", "reportClient", 'TestRequest', self, self.OnTestRequest)
