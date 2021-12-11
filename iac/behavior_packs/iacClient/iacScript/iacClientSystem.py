# -*- coding: utf-8 -*-
# 上面这行是让这个文件按utf-8进行编码，这样就可以在注释中写中文了

# 获取客户端引擎API模块
import client.extraClientApi as clientApi
import time

# 获取客户端system的基类ClientSystem
ClientSystem = clientApi.GetClientSystemCls()


# 在modMain中注册的Client System类
class iacClient(ClientSystem):
    # ServerSystem的初始化函数
    def __init__(self, namespace, systemName):
        # 首先调用父类的初始化函数
        ClientSystem.__init__(self, namespace, systemName)
        self.ListenEvents()

        self.mBJumping = False  # 是否正在跳跃
        self.mJumpingHeight = 0  # 跳跃高度
        self.mJumpingTime = 0  # 跳跃持续时间
        self.mJumpPos = None  # 跳跃的位置
        self.mStartToJumpTime = 0
        self.mPlayerFootPos = None
        self.mTickCount = 0
        self.mLocalPlayerId = clientApi.GetLocalPlayerId()

        self.lastTap = 0

    def ListenEvents(self):
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.OnUIInitFinished)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'TapBeforeClientEvent', self, self.OnTapBeforeClient)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), "ClientJumpButtonPressDownEvent", self, self.OnClientJumpButtonPressDownEvent)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'LeftClickBeforeClientEvent', self, self.OnLeftClickBeforeClient)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'ClientPlayerInventoryOpenEvent', self, self.OnClientPlayerInventoryOpen)
        self.ListenForEvent('iac', 'iacSystem', 'ServerAttackEvent', self, self.OnServerAttack)

    def OnClientPlayerInventoryOpen(self, data):
        if data['isCreative']:
            data['cancel'] = True

    def OnUIInitFinished(self, args):
        platform = clientApi.GetPlatform()
        if platform == 0:
            self.NotifyToServer("CaughtModpcEvent", clientApi.GetLocalPlayerId())

    def Update(self):

        # detections for: movement.highjump

        # self.CheckNightView()
        if not self.mBJumping:
            return
        now = time.time()
        # 2秒都没上升，则起跳失败了
        if now - 2 > self.mStartToJumpTime and not self.mJumpingTime:
            self.mBJumping = False
            return
        posComp = clientApi.GetEngineCompFactory().CreatePos(self.mLocalPlayerId)
        blockComp = clientApi.GetEngineCompFactory().CreateBlockInfo(clientApi.GetLevelId())
        footPos = posComp.GetFootPos()
        groundBlock = blockComp.GetBlock((footPos[0], footPos[1] - 1, footPos[2]))
        # 玩家在空中，且上升了
        if groundBlock[0] == 'minecraft:air' and footPos[1] > self.mJumpPos[1]:
            self.mJumpingHeight = max(self.mJumpingHeight, footPos[1] - self.mJumpPos[1])
            self.mJumpingTime = now - self.mStartToJumpTime
            print 'jumping.data:', self.mJumpingHeight, self.mJumpingTime
            print 'block info:', blockComp.GetBlock((footPos[0], footPos[1] - 1, footPos[2])), blockComp.GetBlock(
                (footPos[0], footPos[1] - 2, footPos[2]))
        else:
            if not self.mJumpingTime:  # 还没有起跳，再等等
                return
            else:  # 已经起跳了，玩家着陆，则本次跳跃结束了，可以分析数据
                self.mBJumping = False
        # 分析跳跃数据
        print 'Jump finish.data:', self.mJumpingHeight, self.mJumpingTime

        # TODO Hook into anticheat
        if (self.mJumpingHeight > 2 and self.mJumpingTime > 3) or self.mJumpingHeight > 5 or self.mJumpingTime > 5:
            response = {
                'playerId': clientApi.GetLocalPlayerId(),
                'vl': 10,
                'alertType': 'highjump',
                'height': self.mJumpingHeight,
                'time': self.mJumpingTime
            }
            self.NotifyToServer("ClientVlEvent", response)

        # detections for: movement.clientDesync

    def OnClientJumpButtonPressDownEvent(self, args):
        posComp = clientApi.GetEngineCompFactory().CreatePos(self.mLocalPlayerId)

        blockComp = clientApi.GetEngineCompFactory().CreateBlockInfo(clientApi.GetLevelId())
        footPos = posComp.GetFootPos()
        print 'OnClientJumpButtonPressDownEvent.foot block:', blockComp.GetBlock((footPos[0], footPos[1] - 1, footPos[2]))
        if self.mBJumping:
            return
        self.mBJumping = True
        self.mJumpingHeight = 0
        self.mJumpingTime = 0
        self.mJumpPos = footPos
        self.mStartToJumpTime = int(time.time())

    def OnServerAttack(self, data):
        tapTime = time.time()
        print 'attack timeDiff=%s' % (abs(tapTime-self.lastTap),)

        if abs(tapTime-self.lastTap) > 2:
            response = {
                'playerId': clientApi.GetLocalPlayerId(),
                'vl': 5,
                'alertType': 'fakeTap'
            }
            self.NotifyToServer("ClientVlEvent", response)

            print 'FAKETAP DETECTED!!!'

    def OnTapBeforeClient(self, data):
        self.lastTap = time.time()
        print 'tap'

    def OnLeftClickBeforeClient(self, data):
        self.lastTap = time.time()
        print 'tap'
        response = {
            'playerId': clientApi.GetLocalPlayerId(),
            'vl': 0,
            'alertType': 'joystickTest'
        }
        self.NotifyToServer("ClientVlEvent", response)

    # 函数名为Destroy才会被调用，在这个System被引擎回收的时候会调这个函数来销毁一些内容
    def Destroy(self):
        pass
