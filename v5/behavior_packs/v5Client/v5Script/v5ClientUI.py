import client.extraClientApi as clientApi
import random

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
TouchEvent = clientApi.GetMinecraftEnum().TouchEvent
ClientSystem = clientApi.GetSystem("v5", "v5Client")

class v5Screen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        print '==== %s ====' % 'init v5Screen'

        self.hpBar = '/hpbar'
        self.extraBar = '/extrabar'
        self.growthBar = '/growthbar'
        self.decrBar = '/decrbar'

        self.killIndicatorPanel = '/panel2'
        self.killIndicatorNormal = self.killIndicatorPanel + '/image5'
        self.killIndicatorSuicide = self.killIndicatorPanel + '/image7'

        self.killfeedPanel = '/panel3'
        self.bottomKillfeed = self.killfeedPanel + '/image8'
        self.killfeedMsgNormal = self.killfeedPanel + '/image9'
        self.killfeedKillerInd = self.killfeedMsgNormal + '/label0'
        self.killfeedMsgSuicide = self.killfeedPanel + '/image10'

        self.hp = 100
        self.randHp = 100
        self.deltaHp = 100

        self.healthNumPanel = '/panel0'
        self.healthDigit1 = self.healthNumPanel + '/image0'
        self.healthDigit2 = self.healthNumPanel + '/image1'
        self.healthDigit3 = self.healthNumPanel + '/image2'

        self.armorNumPanel = '/panel1'
        self.armorDigit1 = self.armorNumPanel + '/image3'
        self.armorDigit2 = self.armorNumPanel + '/image4'

        self.mPlayAnimTimerObj = None
        self.mPlayAnimTimerCount = 0

        self.isDead = False

        self.hudLoadingImg = '/image11'

    def SetProgressbarValue(self, path, value):
        progressBarUIControl = clientApi.GetUI('hud', 'hudUI').GetBaseUIControl(path).asProgressBar()
        progressBarUIControl.SetValue(value/100.0)

    def Create(self):
        print '==== %s ====' % 'rankScreen Create'
        # self.AddTouchEventHandler(self.closeBtn, self.ExitUi, {"isSwallow": True})

    def InitScreen(self):
        print '==== %s ====' % 'uiScreen Init'

        # self.SetVisible('/panel0', False)
        self.SetVisible("", True)
        self.SetVisible(self.hpBar, False)
        self.SetVisible(self.healthNumPanel, False)
        self.SetVisible(self.armorNumPanel, False)
        self.SetVisible(self.extraBar, False)
        self.SetVisible(self.growthBar, False)
        self.SetVisible(self.decrBar, False)
        self.SetVisible(self.killIndicatorPanel, False)

        self.SetVisible(self.killfeedPanel, False)
        self.SetVisible(self.killfeedMsgNormal, False)
        self.SetVisible(self.killfeedMsgSuicide, False)
        self.SetVisible(self.killfeedKillerInd, False)

        comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        comp.AddRepeatedTimer(0.01, self.tick)

    def tick(self):
        if self.randHp < self.deltaHp:
            self.deltaHp -= 1
            self.SetVisible(self.growthBar, False)
            self.SetVisible(self.decrBar, True)
            self.SetProgressbarValue(self.decrBar, self.deltaHp)

        elif self.randHp > self.deltaHp:
            self.deltaHp += 1
            self.SetVisible(self.growthBar, True)
            self.SetVisible(self.decrBar, False)
            self.SetProgressbarValue(self.hpBar, self.deltaHp)

        else:
            self.SetVisible(self.growthBar, False)
            self.SetVisible(self.decrBar, False)

    def UpdatePrepSelectionScreen(self, data):
        pass

    def PlayBottomKillfeedAnim(self):
        # positions: y 154 to 98, interval=0.008
        self.SetVisible(self.bottomKillfeed, True)

    def ShowUi(self, isEnableHud):
        # ui = clientApi.GetUI('rank', 'rankUI')
        # mPath = '/panel0/scroll_view0'
        # # UC: UiControl
        # scrollUC = ui.GetBaseUIControl(mPath).asScrollView()
        # scroll = scrollUC.GetScrollViewContentPath()
        # self.rankContent = scroll + '/content'

        print 'UISCRIPT CALL ShowUi hud'
        self.isDead = False
        self.SetVisible(self.hudLoadingImg, False)
        self.SetVisible("", isEnableHud)
        self.SetVisible(self.extraBar, False)
        self.SetVisible(self.hpBar, True)
        self.SetVisible(self.healthNumPanel, True)
        self.SetVisible(self.armorNumPanel, False)
        self.SetVisible(self.growthBar, False)
        self.SetVisible(self.decrBar, False)
        self.SetProgressbarValue(self.hpBar, 100)
        self.SetVisible(self.killIndicatorPanel, False)

        self.SetVisible(self.killfeedPanel, False)
        self.SetVisible(self.killfeedMsgNormal, False)
        self.SetVisible(self.killfeedMsgSuicide, False)
        self.SetVisible(self.killfeedKillerInd, False)

    def DisplayKillIndicator(self, isSuicide):
        self.SetVisible(self.killIndicatorPanel, True)
        self.SetVisible(self.killIndicatorNormal, False)
        self.SetVisible(self.killIndicatorSuicide, False)

        if isSuicide:
            self.isDead = True
            self.SetVisible(self.killIndicatorSuicide, True)
            self.SetVisible(self.hpBar, False)
            self.SetVisible(self.healthNumPanel, False)
            self.SetVisible(self.armorNumPanel, False)
            self.SetVisible(self.extraBar, False)
            self.SetVisible(self.growthBar, False)
            self.SetVisible(self.decrBar, False)
        else:
            self.SetVisible(self.killIndicatorNormal, True)

        comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        comp.AddTimer(0.2, lambda p: self.SetVisible(p, False), self.killIndicatorPanel)

    def DisplayDeath(self, data):
        self.isDead = True
        isSuicide = data['isSuicide']
        if not isSuicide:
            attackerId = data['killerId']
            attackerNick = data['killerNickname']

        print 'display death, suicide=%s' % isSuicide

        self.SetVisible(self.hpBar, False)
        self.SetVisible(self.healthNumPanel, False)
        self.SetVisible(self.armorNumPanel, False)
        self.SetVisible(self.extraBar, False)
        self.SetVisible(self.growthBar, False)
        self.SetVisible(self.decrBar, False)

        self.SetVisible(self.killfeedPanel, True)
        if isSuicide:
            self.SetVisible(self.killfeedMsgSuicide, True)
        else:
            self.SetVisible(self.killfeedMsgNormal, True)
            self.SetVisible(self.killfeedKillerInd, True)
            self.SetText(self.killfeedKillerInd, attackerNick)

        self.PlayBottomKillfeedAnim()

    def UpdateData(self, data):
        # print data

        if self.isDead:
            return

        print 'update'
        uiNode = clientApi.GetUI('hud', 'hudUI')
        rawHp = data['hp']*5
        if rawHp != self.hp:
            if rawHp == 100:
                hp = 100
            else:
                hp = rawHp + random.randint(-4, 4)
                if rawHp > self.hp and hp < self.randHp:
                    hp = self.randHp+random.randint(1, 4)
                elif rawHp < self.hp and hp > self.randHp:
                    hp = self.randHp-random.randint(-4, 1)
            ClientSystem.UpdateHp(hp)
        else:
            hp = self.hp

        displayHp = hp + data['extra']*5
        if data['extra'] > 0:
            self.SetVisible(self.extraBar, True)
            self.SetProgressbarValue(self.extraBar, data['extra'])
        else:
            self.SetVisible(self.extraBar, False)

        armor = data['armor']*2
        print 'armor is %s' % armor
        if rawHp < self.hp:
            self.SetProgressbarValue(self.hpBar, hp)
        elif rawHp > self.hp:
            self.SetVisible(self.growthBar, True)
            self.SetProgressbarValue(self.growthBar, hp)
        # self.SetProgressbarValue(self.decrBar, hp)
        # self.SetProgressbarValue(self.growthBar, hp)
        self.SetVisible(self.healthNumPanel, True)

        # return

        # set hp sprites
        # digit 1
        if displayHp >= 100:
            self.SetVisible(self.healthDigit1, True)
            uiNode.GetBaseUIControl(self.healthDigit1).asImage().SetSprite('textures/ui/hudUI/%s' % (int(displayHp // 10**2 % 10),))
        else:
            self.SetVisible(self.healthDigit1, False)
        # digit 2
        if displayHp >= 10:
            self.SetVisible(self.healthDigit2, True)
            uiNode.GetBaseUIControl(self.healthDigit2).asImage().SetSprite('textures/ui/hudUI/%s' % (int(displayHp // 10**1 % 10),))
        else:
            self.SetVisible(self.healthDigit2, False)
        # digit 3
        if displayHp >= 1:
            self.SetVisible(self.healthDigit3, True)
            uiNode.GetBaseUIControl(self.healthDigit3).asImage().SetSprite('textures/ui/hudUI/%s' % (int(displayHp % 10),))
        else:
            self.SetVisible(self.healthDigit3, False)

        # set armor sprites:
        if armor > 0:
            self.SetVisible(self.armorNumPanel, True)
        # digit 1
            if armor >= 10:
                self.SetVisible(self.armorDigit1, True)
                uiNode.GetBaseUIControl(self.armorDigit1).asImage().SetSprite('textures/ui/hudUI/a%s' % (armor // 10**1 % 10,))
            else:
                self.SetVisible(self.armorDigit1, False)
            # digit 2
            if armor >= 1:
                self.SetVisible(self.armorDigit2, True)
                uiNode.GetBaseUIControl(self.armorDigit2).asImage().SetSprite('textures/ui/hudUI/a%s' % (armor % 10,))
            else:
                self.SetVisible(self.armorDigit2, False)
        else:
            self.SetVisible(self.armorNumPanel, False)

        self.hp = rawHp
        self.randHp = hp


    def ExitUi(self, args):
        print 'UISCRIPT CALL ExitUi args=%s' % (args,)
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.close()

    def ResetHud(self):
        self.hp = 100
        self.randHp = 100
        self.deltaHp = 100
        self.mPlayAnimTimerObj = None
        self.mPlayAnimTimerCount = 0

        self.ShowUi(True)
        self.SetVisible(self.bottomKillfeed, False)

    def close(self):
        self.SetVisible("", False)
        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)