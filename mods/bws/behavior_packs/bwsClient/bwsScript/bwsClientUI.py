import client.extraClientApi as clientApi
import bwsScript.consts as vars

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
TouchEvent = clientApi.GetMinecraftEnum().TouchEvent
ClientSystem = clientApi.GetSystem("bws", "bwsClient")

varsList = [
    vars.blocks,
    vars.tools,
    vars.weapons,
    vars.armor,
    vars.misc
]

class bwsScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        print '==== %s ====' % 'init TestScreen'

        self.closeBtn = '/closeBtn'
        self.prevBtn = '/prevBtn'
        self.balanceInd = '/balance'

        self.menuPanel = '/panel0'
        self.buyBlocks = self.menuPanel+'/button0'
        self.buyWeapon = self.menuPanel+'/button1'
        self.buyTools = self.menuPanel+'/button2'
        self.buyArmor = self.menuPanel+'/button3'
        self.buyMisc = self.menuPanel+'/button4'

        self.blocksPanel = '/panel1'
        self.toolsPanel = '/panel3'
        self.weaponsPanel = '/panel2'
        self.armorPanel = '/panel4'
        self.miscPanel = '/panel5'

        self.page = 0
        self.balance = 0

    def Create(self):
        print '==== %s ====' % 'bwsScreen Create'
        self.AddTouchEventHandler(self.closeBtn, self.ExitUi, {"isSwallow": True})
        self.AddTouchEventHandler(self.prevBtn, self.prev, {"isSwallow": True})

        self.AddTouchEventHandler(self.buyBlocks, self.buyAction, {"isSwallow": True})
        self.AddTouchEventHandler(self.buyWeapon, self.buyAction, {"isSwallow": True})
        self.AddTouchEventHandler(self.buyTools, self.buyAction, {"isSwallow": True})
        self.AddTouchEventHandler(self.buyArmor, self.buyAction, {"isSwallow": True})
        self.AddTouchEventHandler(self.buyMisc, self.buyAction, {"isSwallow": True})

        for key in vars.blocks:
            name = key.replace('minecraft:', '')
            path = '/panel1/%s' % (name,)
            self.AddTouchEventHandler(path, self.buy, {"isSwallow": True})

        for key in vars.tools:
            name = key.replace('minecraft:', '')
            path = '/panel2/%s' % (name,)
            self.AddTouchEventHandler(path, self.buy, {"isSwallow": True})

        for key in vars.weapons:
            name = key.replace('minecraft:', '')
            path = '/panel3/%s' % (name,)
            self.AddTouchEventHandler(path, self.buy, {"isSwallow": True})

        for key in vars.armor:
            name = key.replace('minecraft:', '')
            path = '/panel4/%s' % (name,)
            self.AddTouchEventHandler(path, self.buy, {"isSwallow": True})

        for key in vars.misc:
            name = key.replace('minecraft:', '')
            path = '/panel5/%s' % (name,)
            self.AddTouchEventHandler(path, self.buy, {"isSwallow": True})

    def InitScreen(self):
        print '==== %s ====' % 'uiScreen Init'

        self.SetVisible("", False)
        self.reset()

    def prev(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and self.page > 0:
            self.reset()

    def buyAction(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and self.page == 0:
            path = args['ButtonPath'].replace('/panel0/', '')
            print 'entering buy from menu path=%s' % path
            self.SetVisible(self.menuPanel, False)
            self.SetVisible(self.prevBtn, True)
            if path == 'button0':
                self.SetVisible(self.blocksPanel, True)
                self.page = 1
            elif path == 'button1':
                self.SetVisible(self.toolsPanel, True)
                self.page = 2
            elif path == 'button2':
                self.SetVisible(self.weaponsPanel, True)
                self.page = 3
            elif path == 'button3':
                self.SetVisible(self.armorPanel, True)
                self.page = 4
            elif path == 'button4':
                self.SetVisible(self.miscPanel, True)
                self.page = 5

    def buy(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            path = args['ButtonPath'].replace('/panel1/', '').replace('/panel2/', '').replace('/panel3/', '').replace('/panel4/', '').replace('/panel5/', '')
            print 'buying path=%s' % path

            useNamespace = False
            for di in varsList:
                if path in di:
                    itemData = di[path]
                    break
                elif 'minecraft:'+path in di:
                    itemData = di['minecraft:'+path]
                    useNamespace = True
                    break

            price = itemData[0]
            print 'price for this item is %s!' % price
            if price <= self.balance:
                data = {
                    'path': path,
                    'namespaced': useNamespace,
                    'itemData': itemData,
                    'balance': self.balance
                }
                ClientSystem.ReturnToServer(data)
                self.balance -= price
                print 'balance is now %s' % self.balance
                self.SetText(self.balanceInd, str(self.balance))
            else:
                print 'cannot afford %s!' % path
                comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
                comp.AddTimer(0.5, lambda args: self.SetVisible(args, False), self.balanceInd)
                comp.AddTimer(1, lambda args: self.SetVisible(args, True), self.balanceInd)
                comp.AddTimer(1.5, lambda args: self.SetVisible(args, False), self.balanceInd)
                comp.AddTimer(2, lambda args: self.SetVisible(args, True), self.balanceInd)
                comp.AddTimer(2.5, lambda args: self.SetVisible(args, False), self.balanceInd)
                comp.AddTimer(3, lambda args: self.SetVisible(args, True), self.balanceInd)

    def reset(self):
        self.SetVisible(self.menuPanel, True)
        self.SetVisible(self.prevBtn, False)
        self.page = 0
        for i in range(5):
            self.SetVisible('/panel%s' % (i + 1,), False)

    def update(self):
        self.SetText(self.balanceInd, self.balance)

    def ShowUi(self, money):
        clientApi.SetInputMode(1)
        clientApi.HideSlotBarGui(True)
        print 'UISCRIPT CALL ShowUi'
        self.SetVisible("", True)
        self.balance = money
        self.SetText(self.balanceInd, str(money))

    def ExitUi(self, args):
        print 'UISCRIPT CALL ExitUi args=%s' % (args,)
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.close()

    def close(self):
        self.SetVisible("", False)
        self.reset()
        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)