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

        self.prepPanel = '/prepPanel'
        self.prepChooseWeaponPanel = self.prepPanel + '/panel0'
        self.prepChooseWeaponDisableInd = self.prepChooseWeaponPanel + '/wd'
        self.prepChooseWeaponChosenInd = self.prepChooseWeaponPanel + '/ws'
        self.prepChooseSkillPanel = self.prepPanel + '/panel1'
        self.prepChooseSkillDisableInd = self.prepChooseSkillPanel + '/sd'
        self.prepChooseSkillChosenInd = self.prepChooseSkillPanel + '/ss'

        self.timerPanel = '/timerPanel'
        self.timerIndPanel = self.timerPanel + '/panel2'
        self.timerIndMinuteDigit1 = self.timerIndPanel + '/m1'
        self.timerIndSecondDigit1 = self.timerIndPanel + '/se1'
        self.timerIndSecondDigit2 = self.timerIndPanel + '/se2'
        self.defuserInd = self.timerPanel + '/image5'

        self.eqpPanel = '/eqpPanel'
        self.eqpWeaponBroken = self.eqpPanel + '/image6'
        self.eqpDur1Bar = self.eqpPanel + '/dur1'
        self.eqpDur2Bar = self.eqpPanel + '/dur2'
        self.eqpDur3Bar = self.eqpPanel + '/dur2'
        self.eqpFixBar = self.eqpPanel + '/durf'
        self.eqpFixBtn = self.eqpPanel + '/fixBtn'
        self.eqpSlotsPanel = self.eqpPanel + '/panel3'
        self.eqpSlotsPrimaryButton = self.eqpSlotsPanel + '/primary'
        self.eqpSlotsSecondaryButton = self.eqpSlotsPanel + '/secondary'
        self.eqpSlotsSkillButton = self.eqpSlotsPanel + '/skill'

        self.selectionsData = None

    def SetProgressbarValue(self, path, value):
        progressBarUIControl = clientApi.GetUI('v5', 'v5UI').GetBaseUIControl(path).asProgressBar()
        progressBarUIControl.SetValue(value/100.0)

    def Create(self):
        print '==== %s ====' % 'v5Screen Create'
        uiNode = clientApi.GetUI('v5', 'v5UI')

        self.AddTouchEventHandler(self.eqpFixBtn, self.eqpFix, {"isSwallow": False})
        self.AddTouchEventHandler(self.eqpSlotsPrimaryButton, self.eqpPrimary, {"isSwallow": False})
        self.AddTouchEventHandler(self.eqpSlotsSecondaryButton, self.eqpSecondary, {"isSwallow": False})
        self.AddTouchEventHandler(self.eqpSlotsSkillButton, self.eqpSkill, {"isSwallow": False})

        # register buttons from w1~w5, s1~s5
        for i in range(5):
            ref = i+1
            self.AddTouchEventHandler(self.prepChooseWeaponPanel + '/w%s' % (ref,), self.weaponSelectHandle, {"isSwallow": False})
            self.AddTouchEventHandler(self.prepChooseWeaponPanel + '/s%s' % (ref,), self.skillSelectHandle, {"isSwallow": False})

        # clone disabled overlay & select indicator for w2~w5, s2~s5
        for i in range(4):
            ref = i+2
            uiNode.Clone(self.prepChooseWeaponDisableInd, self.prepChooseWeaponPanel, self.prepChooseWeaponPanel + 'wd%s' % ref)
            uiNode.GetBaseUIControl('wd%s' % ref).SetPosition(uiNode.GetBaseUIControl('w%s' % ref).GetPosition())

            uiNode.Clone(self.prepChooseWeaponChosenInd, self.prepChooseWeaponPanel, self.prepChooseWeaponPanel + 'ws%s' % ref)
            uiNode.GetBaseUIControl('ws%s' % ref).SetPosition((uiNode.GetBaseUIControl('w%s' % ref).GetPosition()[0], -4))

            uiNode.Clone(self.prepChooseSkillDisableInd, self.prepChooseSkillPanel, self.prepChooseSkillPanel + 'sd%s' % ref)
            uiNode.GetBaseUIControl('sd%s' % ref).SetPosition(uiNode.GetBaseUIControl('s%s' % ref).GetPosition())

            uiNode.Clone(self.prepChooseSkillChosenInd, self.prepChooseSkillPanel, self.prepChooseSkillPanel + 'ss%s' % ref)
            uiNode.GetBaseUIControl('ss%s' % ref).SetPosition((uiNode.GetBaseUIControl('s%s' % ref).GetPosition()[0], -97))

    def InitScreen(self):
        print '==== %s ====' % 'uiScreen Init V5UI'

        # self.SetVisible('/panel0', False)
        self.SetVisible("", True)
        self.SetVisible(self.prepPanel, False)
        self.SetVisible(self.timerPanel, False)
        self.SetVisible(self.eqpPanel, False)

    def tick(self):
        pass

    def UpdatePrepSelectionScreen(self, data):
        #   team: {
        #         player: [weaponSelectionId, skillSelectionId]
        #     }

        selections = data['selections']
        self.selectionsData = selections

        if data['isShow']:
            self.SetVisible(self.prepPanel, True)
        else:
            self.SetVisible(self.prepPanel, False)

        for i in range(5):
            ref = i+1
            # self.SetVisible(self.prepChooseWeaponPanel + '/w%s' % ref, False)
            self.SetVisible(self.prepChooseWeaponPanel + '/ws%s' % ref, False)
            self.SetVisible(self.prepChooseWeaponPanel + '/wd%s' % ref, False)
            # SetVisible(self.prepChooseSkillPanel + '/s%s' % ref, False)
            self.SetVisible(self.prepChooseSkillPanel + '/sd%s' % ref, False)
            self.SetVisible(self.prepChooseSkillPanel + '/ss%s' % ref, False)

        for player in selections:
            weaponSelectionId = selections[player][0]
            skillSelectionId = selections[player][1]

            if not weaponSelectionId:
                pass
            elif player == clientApi.GetLocalPlayerId():
                self.SetVisible(self.prepChooseWeaponPanel + '/ws%s' % weaponSelectionId, True)
            else:
                self.SetVisible(self.prepChooseWeaponPanel + '/wd%s' % weaponSelectionId, True)

            if not skillSelectionId:
                pass
            elif player == clientApi.GetLocalPlayerId():
                self.SetVisible(self.prepChooseSkillPanel + '/ss%s' % skillSelectionId, True)
            else:
                self.SetVisible(self.prepChooseSkillPanel + '/sd%s' % skillSelectionId, True)


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