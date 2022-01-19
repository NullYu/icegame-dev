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
        self.defuserBar = self.timerPanel + '/defuserBar'
        self.defuserActiveInd = self.timerPanel + '/image5'
        self.defuserPlantPanel = self.timerPanel + '/panel4'
        self.defuserPlantBtn = self.defuserPlantPanel + '/button0'
        self.counterDefuseBtn = self.defuserPlantPanel + '/button1'
        self.defuserPlantBar = self.defuserPlantPanel + '/plantBar'

        self.eqpPanel = '/eqpPanel'
        self.eqpWeaponBrokenInd = self.eqpPanel + '/image6'
        self.eqpDur1Bar = self.eqpPanel + '/dur1'
        self.eqpDur2Bar = self.eqpPanel + '/dur2'
        self.eqpDur3Bar = self.eqpPanel + '/dur3'
        self.eqpFixBar = self.eqpPanel + '/durf'
        self.eqpSlotsPanel = self.eqpPanel + '/panel3'
        self.eqpFixBtn = self.eqpSlotsPanel + '/fixBtn'
        self.eqpSlotsPrimaryButton = self.eqpSlotsPanel + '/primary'
        self.eqpSlotsSecondaryButton = self.eqpSlotsPanel + '/secondary'
        self.eqpSlotsSkillButton = self.eqpSlotsPanel + '/skill'

        self.reinforcementPanel = '/reinforcementPanel'
        self.reinfCounterDigit1 = self.reinforcementPanel + '/image8'
        self.reinfCounterDigit2 = self.reinforcementPanel + '/image9'
        self.reinfCounterDigit3 = self.reinforcementPanel + '/image10'

        self.selectionsData = None

        self.defuserTimer = 44
        self.defuseStarted = False
        self.timerText = '0:02:50'

        self.eqpDur1 = 20
        self.eqpDur2 = 20
        self.eqpDur2Max = 20
        self.eqpDur3 = 0
        self.eqpDur3Max = 0
        self.slot1 = None
        self.slot2 = None
        self.slotSkill = None
        self.fixProgress = 0
        self.fixStarted = False
        self.currentEquipped = 0

        self.defuserPlantProgress = 0
        
        self.reinfsLeft = 0

    def SetProgressbarValue(self, path, value):
        progressBarUIControl = clientApi.GetUI('v5', 'v5UI').GetBaseUIControl(path).asProgressBar()
        progressBarUIControl.SetValue(value)

    def Create(self):
        print '==== %s ====' % 'v5Screen Create'
        uiNode = clientApi.GetUI('v5', 'v5UI')

        # clone disabled overlay & select indicator for w2~w5, s2~s5
        # manual locations
        locations = {
            1: [(149, 36.5), (223, 36.5), (297, 36.5), (371, 36.5)],
            2: [(164, 119.5), (238, 119.5), (312, 119.5), (386, 119.5)],
            3: [(149, 36.5), (223, 36.5), (297, 36.5), (371, 36.5)],
            4: [(164, 26.5), (238, 26.5), (312, 26.5), (386, 26.5)]
        }

        for i in range(4):
            ref = i+2
            uiNode.Clone(self.prepChooseWeaponDisableInd, self.prepChooseWeaponPanel, 'wd%s' % ref)
            uiNode.GetBaseUIControl(self.prepChooseWeaponPanel + '/wd%s' % ref).SetPosition(locations[1][i])
            print 'moving wd%s@%s to %s' % (ref, uiNode.GetBaseUIControl(self.prepChooseWeaponPanel + '/wd%s' % ref).GetPosition(), uiNode.GetBaseUIControl(self.prepChooseWeaponPanel + '/w%s' % ref).GetPosition())

            uiNode.Clone(self.prepChooseWeaponChosenInd, self.prepChooseWeaponPanel, 'ws%s' % ref)
            uiNode.GetBaseUIControl(self.prepChooseWeaponPanel + '/ws%s' % ref).SetPosition(locations[2][i])

            uiNode.Clone(self.prepChooseSkillDisableInd, self.prepChooseSkillPanel, 'sd%s' % ref)
            uiNode.GetBaseUIControl(self.prepChooseSkillPanel + '/sd%s' % ref).SetPosition(locations[3][i])

            uiNode.Clone(self.prepChooseSkillChosenInd, self.prepChooseSkillPanel, 'ss%s' % ref)
            uiNode.GetBaseUIControl(self.prepChooseSkillPanel + '/ss%s' % ref).SetPosition(locations[4][i])

        self.AddTouchEventHandler(self.eqpFixBtn, self.eqpFix, {"isSwallow": False})
        self.AddTouchEventHandler(self.eqpSlotsPrimaryButton, self.eqpPrimary, {"isSwallow": False})
        self.AddTouchEventHandler(self.eqpSlotsSecondaryButton, self.eqpSecondary, {"isSwallow": False})
        self.AddTouchEventHandler(self.eqpSlotsSkillButton, self.eqpSkill, {"isSwallow": False})
        
        self.AddTouchEventHandler(self.defuserPlantBtn, self.defuserPlant, {"isSwallow": False})
        self.AddTouchEventHandler(self.counterDefuseBtn, self.counterDefuse, {"isSwallow": False})

        # register buttons from w1~w5, s1~s5
        for i in range(5):
            ref = i + 1
            self.AddTouchEventHandler(self.prepChooseWeaponPanel + '/w%s' % (ref,), self.weaponSelectHandle,
                                      {"isSwallow": False})
            self.AddTouchEventHandler(self.prepChooseSkillPanel + '/s%s' % (ref,), self.skillSelectHandle,
                                      {"isSwallow": False})

    def InitScreen(self):
        print '==== %s ====' % 'uiScreen Init V5UI'

        # self.SetVisible('/panel0', False)
        self.SetVisible("", True)
        self.SetVisible(self.prepPanel, False)
        self.SetVisible(self.timerPanel, False)
        self.SetVisible(self.eqpPanel, False)
        self.SetVisible(self.reinforcementPanel, False)
        self.SetVisible(self.defuserPlantPanel, False)
        self.resetPrepPanel()

        comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        comp.AddRepeatedTimer(1.0, self.defuserTick)
        comp.AddRepeatedTimer(1.0, self.tick)

        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)

    def resetPrepPanel(self):
        for i in range(5):
            ref = i+1
            self.SetVisible(self.prepChooseWeaponPanel + '/wd%s' % ref, False)
            self.SetVisible(self.prepChooseWeaponPanel + '/ws%s' % ref, False)
            self.SetVisible(self.prepChooseSkillPanel + '/sd%s' % ref, False)
            self.SetVisible(self.prepChooseSkillPanel + '/ss%s' % ref, False)

        self.SetVisible(self.prepChooseWeaponPanel + '/wd', False)
        self.SetVisible(self.prepChooseWeaponPanel + '/ws', False)
        self.SetVisible(self.prepChooseSkillPanel + '/sd', False)
        self.SetVisible(self.prepChooseSkillPanel + '/ss', False)

    def resetTimerPanel(self):
        self.SetVisible(self.timerIndPanel, True)
        self.SetVisible(self.defuserBar, False)
        self.SetVisible(self.defuserActiveInd, False)

    def resetEqpPanel(self):
        self.eqpDur1 = 20
        self.eqpDur2 = 20
        self.eqpDur3 = 0
        self.fixProgress = 0
        self.fixStarted = False
        self.SetVisible(self.eqpWeaponBrokenInd, False)
        self.updateEqpBars()

    def updateEqpBars(self):
        self.SetProgressbarValue(self.eqpDur1Bar, self.eqpDur1/20.0)
        self.SetProgressbarValue(self.eqpDur2Bar, self.eqpDur2/float(self.eqpDur2Max))
        self.SetProgressbarValue(self.eqpDur3Bar, self.eqpDur3/float(self.eqpDur3Max))

    def UpdateKitDurability(self, data):
        selected = data['selected']
        self.eqpDur1 = data[1][1]
        self.eqpDur2 = data[2][1]
        self.eqpDur3 = data[3][1]
        self.updateEqpBars()
        if data[selected][1] <= 0:
            self.SetVisible(self.eqpWeaponBrokenInd, True)

    def setEqpData(self, data):
        print 'rcv setEqpData, data=', data
        slot1 = data[1][0]
        slot1Name = data[1][0].split('/')
        slot2 = data[2][0]
        slot2Name = data[2][0].split('/')
        slot3 = data[3][0]
        self.slot1 = slot1Name[0]
        self.slot2 = slot2Name[0]
        self.slotSkill = slot3[0]
        self.eqpDur1 = 20
        self.eqpDur2 = data[2][1]
        self.eqpDur2Max = data[2][1]
        self.eqpDur3 = data[3][1]
        self.eqpDur3Max = data[3][1]

        uiNode = clientApi.GetUI('v5', 'v5UI')
        # set slot 1
        buttonUIControl = uiNode.GetBaseUIControl(self.eqpSlotsPrimaryButton).asButton()
        buttonDefaultUIControl = buttonUIControl.GetChildByName("default").asImage()
        buttonHoverUIControl = buttonUIControl.GetChildByName("hover").asImage()
        buttonPressedUIControl = buttonUIControl.GetChildByName("pressed").asImage()
        buttonDefaultUIControl.SetSprite("textures/ui/v5UI/%s" % slot1Name[0])
        buttonHoverUIControl.SetSprite("textures/ui/v5UI/%s1" % slot1Name[0])
        buttonPressedUIControl.SetSprite("textures/ui/v5UI/%s1" % slot1Name[0])

        # set slot 2
        buttonUIControl = uiNode.GetBaseUIControl(self.eqpSlotsSecondaryButton).asButton()
        buttonDefaultUIControl = buttonUIControl.GetChildByName("default").asImage()
        buttonHoverUIControl = buttonUIControl.GetChildByName("hover").asImage()
        buttonPressedUIControl = buttonUIControl.GetChildByName("pressed").asImage()
        slotName = slot2
        if 'bow' in slotName:
            if len(slot2Name) > 1:
                fileName = 'healbow'
            else:
                fileName = 'bow'
        elif 'shield' in slotName:
            fileName = 'shield'
        else:
            fileName = 'wooden_sword'
        buttonDefaultUIControl.SetSprite("textures/ui/v5UI/%s" % fileName)
        buttonHoverUIControl.SetSprite("textures/ui/v5UI/%s1" % fileName)
        buttonPressedUIControl.SetSprite("textures/ui/v5UI/%s1" % fileName)

        # set slot 3
        buttonUIControl = uiNode.GetBaseUIControl(self.eqpSlotsSkillButton).asButton()
        buttonDefaultUIControl = buttonUIControl.GetChildByName("default").asImage()
        buttonHoverUIControl = buttonUIControl.GetChildByName("hover").asImage()
        buttonPressedUIControl = buttonUIControl.GetChildByName("pressed").asImage()
        buttonDefaultUIControl.SetSprite("textures/ui/v5UI/%s" % slot3)
        buttonHoverUIControl.SetSprite("textures/ui/v5UI/%s1" % slot3)
        buttonPressedUIControl.SetSprite("textures/ui/v5UI/%s1" % slot3)

        self.updateEqpBars()

    def tick(self):
        pass

    def UpdatePrepSelectionScreen(self, data):
        #   team: {
        #         player: [weaponSelectionId, skillSelectionId]
        #     }
        selections = data['selections']
        print 'update msg RCV data=', data

        self.selectionsData = selections

        if data['isShow']:
            self.SetVisible(self.prepPanel, True)
            clientApi.SetInputMode(1)
            clientApi.HideSlotBarGui(True)
        else:
            self.SetVisible(self.prepPanel, False)
            clientApi.SetInputMode(0)
            clientApi.HideSlotBarGui(False)
            return

        self.resetPrepPanel()

        for player in selections:
            weaponSelectionId = selections[player][0]
            skillSelectionId = selections[player][1]

            print 'selection ids: %s, %s' % (weaponSelectionId, skillSelectionId)

            if not weaponSelectionId:
                pass
            elif player == clientApi.GetLocalPlayerId():
                self.SetVisible(self.prepChooseWeaponPanel + ('/ws%s' % weaponSelectionId).replace('1', ''), True)
            else:
                self.SetVisible(self.prepChooseWeaponPanel + ('/wd%s' % weaponSelectionId).replace('1', ''), True)

            if not skillSelectionId:
                pass
            elif player == clientApi.GetLocalPlayerId():
                self.SetVisible(self.prepChooseSkillPanel + ('/ss%s' % skillSelectionId).replace('1', ''), True)
            else:
                self.SetVisible(self.prepChooseSkillPanel + ('/sd%s' % skillSelectionId).replace('1', ''), True)

    def ShowTimerPanel(self, isShow, isReset):
        self.SetVisible(self.timerPanel, isShow)
        if isReset:
            self.resetTimerPanel()

    def ShowEqpPanel(self, isShow, isReset):
        self.SetVisible(self.eqpPanel, isShow)
        self.SetVisible(self.eqpWeaponBrokenInd, False)
        self.SetVisible(self.eqpFixBar, False)
        clientApi.HideSlotBarGui(isShow)
        if isReset:
            pass

    def ShowDefuserButtons(self, data):
        print 'rcv ShowDefuserButtons data=', data
        self.SetVisible(self.defuserPlantPanel, data['isShow'])
        self.SetVisible(self.defuserPlantBar, False)
        self.SetProgressbarValue(self.defuserPlantBar, 0.0)
        
        if data['isShow']:
            self.SetVisible(self.defuserPlantBtn, False)
            self.SetVisible(self.counterDefuseBtn, False)
            if data['type'] == 'plant':
                self.SetVisible(self.defuserPlantBtn, True)
            else:
                self.SetVisible(self.counterDefuseBtn, True)
        
    def UpdateReinfPanel(self, data):
        self.reinfsLeft = data['count']
        if 'isShow' in data:
            isShow = data['isShow']
            self.SetVisible(self.reinforcementPanel, isShow)
            clientApi.HideSlotBarGui(isShow)
        self.UpdateReinfCount(self.reinfsLeft)

    def UpdateReinfCount(self, count):
        self.reinfsLeft = count
        uiNode = clientApi.GetUI('v5', 'v5UI')
        # set hp sprites
        # digit 1
        if count >= 100:
            self.SetVisible(self.reinfCounterDigit1, True)
            uiNode.GetBaseUIControl(self.reinfCounterDigit1).asImage().SetSprite('textures/ui/v5UI/%s' % (int(count // 10 ** 2 % 10),))
        else:
            self.SetVisible(self.reinfCounterDigit1, False)
        # digit 2
        if count >= 10:
            self.SetVisible(self.reinfCounterDigit2, True)
            uiNode.GetBaseUIControl(self.reinfCounterDigit2).asImage().SetSprite('textures/ui/v5UI/%s' % (int(count // 10 ** 1 % 10),))
        else:
            self.SetVisible(self.reinfCounterDigit2, False)
        # digit 3
        self.SetVisible(self.reinfCounterDigit3, True)
        uiNode.GetBaseUIControl(self.reinfCounterDigit3).asImage().SetSprite('textures/ui/v5UI/%s' % (int(count % 10),))

    def weaponSelectHandle(self, args):
        event = args['TouchEvent']
        path = args['ButtonPath']
        if event == TouchEvent.TouchUp:
            response = {
                'operation': 'weaponSelect',
                'selectionId': path.replace(self.prepChooseWeaponPanel + '/w', '')
            }
            print 'weaponSelect res=', response
            ClientSystem.ReturnToServer(response)

    def skillSelectHandle(self, args):
        event = args['TouchEvent']
        path = args['ButtonPath']
        if event == TouchEvent.TouchUp:
            response = {
                'operation': 'skillSelect',
                'selectionId': path.replace(self.prepChooseSkillPanel + '/s', '')
            }
            print 'skillSelect res=', response
            ClientSystem.ReturnToServer(response)

    def eqpFix(self, args):
        event = args['TouchEvent']
        path = args['ButtonPath']
        if event == TouchEvent.TouchUp:

            if self.currentEquipped == 1 and (self.eqpDur1 == 20 or self.eqpDur1 <= 0):
                return
            elif self.currentEquipped == 2 and (self.eqpDur2 == self.eqpDur2Max or self.eqpDur2 <= 0):
                return
            elif self.currentEquipped == 3:
                return

            response = {
                'operation': 'fixWeapon',
                'stage': 'start'
            }
            ClientSystem.ReturnToServer(response)
            self.SetVisible(self.eqpFixBar, True)
            self.fixProgress = 0

            def a(timerComp):
                self.fixProgress += 1
                self.SetProgressbarValue(self.eqpFixBar, self.fixProgress / 100.0)
                if self.fixProgress >= 100:
                    timerComp.CancelTimer(self.bEqpFixTimer)
                    self.SetVisible(self.eqpFixBar, False)
                    response = {
                        'operation': 'fixWeapon',
                        'stage': 'finish',
                        'equipped': self.currentEquipped
                    }
                    ClientSystem.ReturnToServer(response)

            comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
            self.bEqpFixTimer = comp.AddRepeatedTimer(0.02, lambda timerComp: a(timerComp), comp)

    def eqpPrimary(self, args):
        event = args['TouchEvent']
        path = args['ButtonPath']
        if event == TouchEvent.TouchUp:
            self.SetVisible(self.eqpWeaponBrokenInd, False)
            self.currentEquipped = 1
            if self.eqpDur1 <= 0:
                self.SetVisible(self.eqpWeaponBrokenInd, True)
                return

            response = {
                'operation': 'equipWeapon',
                'equipId': 1
            }
            ClientSystem.ReturnToServer(response)

    def eqpSecondary(self, args):
        event = args['TouchEvent']
        path = args['ButtonPath']
        if event == TouchEvent.TouchUp:
            self.SetVisible(self.eqpWeaponBrokenInd, False)
            self.currentEquipped = 2
            if self.eqpDur2 <= 0:
                self.SetVisible(self.eqpWeaponBrokenInd, True)
                return
            response = {
                'operation': 'equipWeapon',
                'equipId': 2
            }
            ClientSystem.ReturnToServer(response)

    def eqpSkill(self, args):
        event = args['TouchEvent']
        path = args['ButtonPath']
        if event == TouchEvent.TouchUp:
            self.SetVisible(self.eqpWeaponBrokenInd, False)
            if self.eqpDur3 <= 0:
                self.SetVisible(self.eqpWeaponBrokenInd, True)
                comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
                comp.AddTimer(1.5, lambda p: self.SetVisible(p, False), self.eqpWeaponBrokenInd)
                return
            response = {
                'operation': 'useSkill'
            }
            ClientSystem.ReturnToServer(response)
    
    def defuserPlant(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchDown:
            print 'defuser button down'
            response = {
                'operation': 'defuserPlant',
                'stage': 'start'
            }
            ClientSystem.ReturnToServer(response)
            self.SetVisible(self.defuserPlantBar, True)
            self.defuserPlantProgress = 0

            def a(timerComp):
                self.defuserPlantProgress += 1
                self.SetProgressbarValue(self.defuserPlantBar, self.defuserPlantProgress / 100.0)
                if self.defuserPlantProgress >= 100:
                    timerComp.CancelTimer(self.bDefuserPlantTimer)
                    self.SetVisible(self.defuserPlantPanel, False)
                    response = {
                        'opration': 'defusePlant',
                        'stage': 'finish'
                    }
                    ClientSystem.ReturnToServer(response)

            comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
            self.bDefuserPlantTimer = comp.AddRepeatedTimer(0.075, lambda timerComp: a(timerComp), comp)

        elif event == TouchEvent.TouchUp:
            if not self.GetVisible(self.defuserPlantPanel):
                return

            print 'defuser button up'
            self.SetVisible(self.defuserPlantBar, False)
            if self.bDefuserPlantTimer:
                comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
                comp.CancelTimer(self.bDefuserPlantTimer)
            response = {
                'operation': 'defuserPlant',
                'stage': 'stop'
            }
            ClientSystem.ReturnToServer(response)

    def counterDefuse(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchDown:
            print 'defuser button down'
            response = {
                'operation': 'defuserDestroy',
                'stage': 'start'
            }
            ClientSystem.ReturnToServer(response)
            self.SetVisible(self.defuserPlantBar, True)
            self.defuserPlantProgress = 0

            def a(timerComp):
                self.defuserPlantProgress += 1
                self.SetProgressbarValue(self.defuserPlantBar, self.defuserPlantProgress / 100.0)
                if self.defuserPlantProgress >= 100:
                    timerComp.CancelTimer(self.bDefuserPlantTimer)
                    self.SetVisible(self.defuserPlantPanel, False)
                    response = {
                        'opration': 'defuserDestroy',
                        'stage': 'finish'
                    }
                    ClientSystem.ReturnToServer(response)

            comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
            self.bDefuserPlantTimer = comp.AddRepeatedTimer(0.075, lambda timerComp: a(timerComp), comp)

        elif event == TouchEvent.TouchUp:
            if not self.GetVisible(self.defuserPlantPanel):
                return

            print 'defuser button up'
            self.SetVisible(self.defuserPlantBar, False)
            if self.bDefuserPlantTimer:
                comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
                comp.CancelTimer(self.bDefuserPlantTimer)
            response = {
                'operation': 'defuserDestroy',
                'stage': 'stop'
            }
            ClientSystem.ReturnToServer(response)
    
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

    def StartDefuserProgress(self):
        print 'defuser progress started'
        self.defuseStarted = True

    def defuserTick(self):
        if self.defuseStarted:
            self.SetVisible(self.defuserBar, True)
            self.SetVisible(self.timerIndPanel, False)
            self.SetProgressbarValue(self.defuserBar, (44-self.defuserTimer)/44.0)
            self.defuserTimer -= 1
            if self.defuserTimer % 2 == 0:
                self.SetVisible(self.defuserActiveInd, True)
            else:
                self.SetVisible(self.defuserActiveInd, False)

            print 'UNTIL DEFUSE: ', self.defuserTimer
            if self.defuserTimer <= 0:
                self.defuseStarted = False
                self.SetVisible(self.timerPanel, False)

        else:
            self.SetVisible(self.defuserBar, False)
            self.SetVisible(self.defuserActiveInd, False)
            self.SetVisible(self.timerIndPanel, True)

            #Update timer text
            uiNode = clientApi.GetUI('v5', 'v5UI')
            uiNode.GetBaseUIControl(self.timerIndMinuteDigit1).asImage().SetSprite('textures/ui/v5UI/%s' % int(self.timerText[3]))
            uiNode.GetBaseUIControl(self.timerIndSecondDigit1).asImage().SetSprite('textures/ui/v5UI/%s' % int(self.timerText[5]))
            uiNode.GetBaseUIControl(self.timerIndSecondDigit2).asImage().SetSprite('textures/ui/v5UI/%s' % int(self.timerText[6]))

    def reset(self):
        self.selectionsData = None

        self.defuserTimer = 44
        self.defuseStarted = False
        self.timerText = '0:02:50'

        self.eqpDur1 = 20
        self.eqpDur2 = 20
        self.eqpDur2Max = 20
        self.eqpDur3 = 0
        self.eqpDur3Max = 0
        self.slot1 = None
        self.slot2 = None
        self.slotSkill = None
        self.fixProgress = 0
        self.fixStarted = False
        self.currentEquipped = 0

        self.defuserPlantProgress = 0

        self.reinfsLeft = 0

        self.SetVisible("", True)
        self.SetVisible(self.prepPanel, False)
        self.SetVisible(self.timerPanel, False)
        self.SetVisible(self.eqpPanel, False)
        self.SetVisible(self.reinforcementPanel, False)
        self.SetVisible(self.defuserPlantPanel, False)
        self.resetPrepPanel()

    def ExitUi(self, args):
        print 'UISCRIPT CALL ExitUi args=%s' % (args,)
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.close()

    def close(self):
        self.SetVisible("", False)
        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)