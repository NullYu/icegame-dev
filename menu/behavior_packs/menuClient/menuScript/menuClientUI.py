import client.extraClientApi as clientApi

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
TouchEvent = clientApi.GetMinecraftEnum().TouchEvent
ClientSystem = clientApi.GetSystem("menu", "menuClient")

class menuScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        print '==== %s ====' % 'init TestScreen'

        self.page = 0
        self.section = 0

        self.bg = '/bg'
        self.closeBtn = '/bg/button_close'
        self.nextBtn = '/bg/button_next'
        self.prevBtn = '/bg/button_prev'

        self.mainMenu = '/bg/panel0'
        self.mainMenuPage1 = self.mainMenu+'/panel0-1'
        self.unrankedEntrance = self.mainMenuPage1+'/button0'
        self.rushEntrance = self.mainMenuPage1 + '/button1'
        self.rankedEntrance = self.mainMenuPage1 + '/button2'

        self.mainMenuPage2 = self.mainMenu+'/panel0-2'
        self.btsEntrance = self.mainMenuPage2+'/button10'
        self.bridgeEntrance = self.mainMenuPage2+'/button11'
        self.cpartyEntrance = self.mainMenuPage2+'/button12'

        self.unrankedMenu = '/bg/panel1'
        self.us2p2 = self.unrankedMenu+'/button3'
        self.unor = self.unrankedMenu + '/button4'
        self.utotem = self.unrankedMenu + '/button5'
        self.usumo = self.unrankedMenu + '/button6'
        self.ubuilduhc = self.unrankedMenu + '/button7'
        self.uarcher = self.unrankedMenu + '/button8'
        self.ucombo = self.unrankedMenu + '/button9'

    def Create(self):
        print '==== %s ====' % 'adminScreen Create'

        self.AddTouchEventHandler(self.closeBtn, self.ExitUi, {"isSwallow": True})
        self.AddTouchEventHandler(self.unrankedEntrance, self.EnterUnranked, {"isSwallow": True})
        self.AddTouchEventHandler(self.rushEntrance, self.EnterRush, {"isSwallow": True})
        self.AddTouchEventHandler(self.btsEntrance, self.EnterBts, {"isSwallow": True})
        self.AddTouchEventHandler(self.bridgeEntrance, self.EnterBridge, {"isSwallow": True})
        self.AddTouchEventHandler(self.cpartyEntrance, self.EnterCparty, {"isSwallow": True})
        self.AddTouchEventHandler(self.prevBtn, self.Prev, {"isSwallow": True})
        self.AddTouchEventHandler(self.nextBtn, self.Next, {"isSwallow": True})

        self.AddTouchEventHandler(self.us2p2, self.PlayUs2p2, {"isSwallow": True})
        self.AddTouchEventHandler(self.utotem, self.PlayUtotem, {"isSwallow": True})
        self.AddTouchEventHandler(self.ucombo, self.PlayCombo, {"isSwallow": True})
        self.AddTouchEventHandler(self.uarcher, self.PlayArcher, {"isSwallow": True})
        self.AddTouchEventHandler(self.usumo, self.PlaySumo, {"isSwallow": True})
        #self.AddTouchEventHandler(self.ubuilduhc, self.PlayBuhc, {"isSwallow": True})
        self.AddTouchEventHandler(self.unor, self.PlayNor, {"isSwallow": True})

    def InitScreen(self):
        print '==== %s ====' % 'adminScreen Init'

        # self.SetVisible('/panel0', False)
        self.SetVisible("", False)
        self.SetVisible(self.unrankedMenu, False)

    def Next(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            if self.page == 0 and self.section == 0:
                self.section += 1
                self.SetVisible(self.mainMenuPage1, False)
                self.SetVisible(self.mainMenuPage2, True)

    def Prev(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            if self.page == 1:
                self.page = 0
                self.section = 0
                self.SetVisible(self.mainMenu, True)
                self.SetVisible(self.unrankedMenu, False)
            elif self.page == 0 and self.section == 1:
                self.section = 0
                self.SetVisible(self.mainMenuPage1, True)
                self.SetVisible(self.mainMenuPage2, False)

    def PlayCombo(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            data = {
                'choice': 'unranked',
                'mode': 'combo'
            }
            ClientSystem.ReturnToServer(data)
            self.close()

    def PlaySumo(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            data = {
                'choice': 'unranked',
                'mode': 'sumo'
            }
            ClientSystem.ReturnToServer(data)
            self.close()

    def PlayArcher(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            data = {
                'choice': 'unranked',
                'mode': 'archer'
            }
            ClientSystem.ReturnToServer(data)
            self.close()
    def PlayNor(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            data = {
                'choice': 'unranked',
                'mode': 'nor'
            }
            ClientSystem.ReturnToServer(data)
            self.close()
    def PlayBuhc(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            data = {
                'choice': 'unranked',
                'mode': 'buhc'
            }
            ClientSystem.ReturnToServer(data)
            self.close()
    def PlayUs2p2(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            data = {
                'choice': 'unranked',
                'mode': 's2p2'
            }
            ClientSystem.ReturnToServer(data)
            self.close()
    def PlayUtotem(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            data = {
                'choice': 'unranked',
                'mode': 'totem'
            }
            ClientSystem.ReturnToServer(data)
            self.close()

    def EnterUnranked(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.SetVisible(self.mainMenu, False)
            self.SetVisible(self.unrankedMenu, True)
            self.page = 1
            self.section = 0

    def EnterRush(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            data = {
                'choice': 'rush'
            }
            ClientSystem.ReturnToServer(data)
            self.close()

    def EnterBts(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            data = {
                'choice': 'bts'
            }
            ClientSystem.ReturnToServer(data)
            self.close()

    def EnterCparty(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            data = {
                'choice': 'cparty'
            }
            ClientSystem.ReturnToServer(data)
            self.close()

    def EnterBridge(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            data = {
                'choice': 'bridge'
            }
            ClientSystem.ReturnToServer(data)
            self.close()

    def ShowUi(self, data=None):
        print 'UISCRIPT CALL ShowUi'
        self.page = 0
        self.section = 0
        self.SetVisible("", True)
        self.SetVisible(self.mainMenu, True)
        self.SetVisible(self.mainMenuPage1, True)
        self.SetVisible(self.mainMenuPage2, False)
        clientApi.SetInputMode(1)
        clientApi.HideSlotBarGui(True)

        if data == 1:
            self.SetVisible(self.mainMenu, False)
            self.SetVisible(self.unrankedMenu, True)
            self.page = 1
            self.section = 0

    def ExitUi(self, args):
        print 'UISCRIPT CALL ExitUi args=%s' % (args,)
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.close()

    def close(self):
        self.SetVisible("", False)
        self.SetVisible(self.unrankedMenu, False)
        self.page = 0
        self.section = 0
        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)
        pass