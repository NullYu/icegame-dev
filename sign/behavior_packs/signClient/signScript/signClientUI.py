import client.extraClientApi as clientApi
import datetime
import time

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
TouchEvent = clientApi.GetMinecraftEnum().TouchEvent
ClientSystem = clientApi.GetSystem("sign", "signClient")

class signScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        print '==== %s ====' % 'init TestScreen'

        self.date = 0
        self.lastsign = 0
        self.day = 0
        self.combo = 0
        self.total = 0
        self.extraCredits = 0
        self.neko = 0
        self.credits = 0
        self.canSign = True

        self.bg = '/bg'
        self.closeBtn = '/button_close'
        self.signBtn = '/button0'
        self.signBlocker = '/done'

        self.totalnum = '/signnum'
        self.combonum = '/combonum'
        self.daynum = '/daynum'
        self.extranum = '/extracredits'

        self.textpanel = '/panel0'
        self.nekoPending = self.textpanel+'/label0'
        self.creditsPending = self.textpanel+'/neko'
        self.getNeko = self.textpanel+'/getneko'
        self.getCredits = self.textpanel+'/getcredits'
        self.getGift = self.textpanel+'/getgift'

    def epoch2Datetime(self, epoch):
        ts = datetime.datetime.fromtimestamp(int(epoch) + 0)
        return ts.strftime('%Y%m%d%H%M%S')

    def datetime2Epoch(self, y, m, d, h, mi):
        # Datetime must be in tuple(YYYY, MM, DD, HH, mm), for example, (1977, 12, 1, 0, 0)
        ts = (datetime.datetime(y, m, d, h, mi) - datetime.datetime(1970, 1, 1)).total_seconds()
        return int(ts)

    def Create(self):
        print '==== %s ====' % 'adminScreen Create'

        self.AddTouchEventHandler(self.closeBtn, self.ExitUi, {"isSwallow": True})
        self.AddTouchEventHandler(self.signBtn, self.Sign, {"isSwallow": True})

    def InitTextPanel(self):
        self.SetVisible(self.getGift, False)
        self.SetVisible(self.getNeko, False)
        self.SetVisible(self.getCredits, False)

    def InitScreen(self):
        print '==== %s ====' % 'adminScreen Init'

        # self.SetVisible('/panel0', False)
        self.SetVisible("", False)
        self.SetVisible(self.signBtn, True)
        self.SetVisible(self.signBlocker, False)
        self.SetVisible(self.textpanel, False)
        self.InitTextPanel()

    def Sign(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and self.canSign:
            self.canSign = False
            self.SetVisible(self.signBtn, False)
            self.SetVisible(self.signBlocker, True)

            self.SetVisible(self.textpanel, False)
            self.SetText(self.totalnum, str(self.total+1))
            self.SetText(self.combonum, str(self.combo+1))

            response = {
                'neko': self.neko,
                'credits': self.credits
            }
            ClientSystem.ReturnToServer(response)

    def ShowUi(self, canSign, date, lastsign, combo, total, neko, credits, extraCredits):
        print 'sign UISCRIPT CALL ShowUi'
        self.SetVisible("", True)

        clientApi.HideSlotBarGui(True)

        self.canSign = canSign
        self.lastsign = lastsign
        self.combo = combo
        self.date = date
        # Time format: YYYYMMDDHHmmSS
        self.day = int(str(self.epoch2Datetime(self.date))[6:8])-2
        self.total = total
        self.neko = neko
        self.credits = credits
        self.extraCredits = extraCredits

        if not canSign:
            self.SetVisible(self.textpanel, False)
            self.SetVisible(self.signBtn, False)
            self.SetVisible(self.signBlocker, True)
        else:
            self.SetVisible(self.textpanel, True)
            self.SetVisible(self.getNeko, True)
            self.SetText(self.nekoPending, str(self.neko))
            self.SetText(self.creditsPending, str(self.credits))
            self.SetVisible(self.getCredits, bool(self.credits))
            # TODO Add Give gift to player
            self.SetVisible(self.getGift, False)

        self.SetText(self.extranum, str(self.extraCredits))
        self.SetText(self.daynum, str(self.day))
        self.SetText(self.totalnum, str(self.total))
        self.SetText(self.combonum, str(self.combo))

        clientApi.SetInputMode(1)
        clientApi.HideSlotBarGui(True)

    def ExitUi(self, args):
        print 'UISCRIPT CALL ExitUi args=%s' % (args,)
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.close()

    def close(self):
        self.SetVisible("", False)
        self.SetVisible(self.textpanel, False)
        self.InitTextPanel()
        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)
        pass