import client.extraClientApi as clientApi
import math

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
TouchEvent = clientApi.GetMinecraftEnum().TouchEvent
ClientSystem = clientApi.GetSystem("hg", "hgClient")

class hgScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        print '==== %s ====' % 'init TestScreen'

        self.timerPanel = '/panel0'
        self.timerInd = self.timerPanel + '/label0'

        self.fallenPanel = '/panel1'
        self.fallenHeading = self.fallenPanel + '/image1'
        self.fallenList = self.fallenPanel + '/image2'
        self.tributeNameInd = self.fallenPanel + '/label1'
        self.districtInd = self.fallenPanel + '/label2'

    def Create(self):
        print '==== %s ====' % 'rankScreen Create'

    def InitScreen(self):
        print '==== %s ====' % 'uiScreen Init'

        # self.SetVisible('/panel0', False)
        self.SetVisible("", False)

        self.SetVisible(self.fallenHeading, True)
        self.SetVisible(self.fallenList, False)
        self.SetVisible(self.timerPanel, False)

    def PlayAnthem(self, li):

        def SetFallenInformation(name, district):
            self.SetText(self.tributeNameInd, name)
            self.SetText(self.districtInd, district)

        delay = round((33/len(li)), 1)

        self.SetVisible(self.fallenPanel, True)
        self.SetVisible(self.tributeNameInd, False)
        self.SetVisible(self.districtInd, False)
        self.SetVisible(self.fallenHeading, False)

        comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        def seq1():
            self.SetVisible(self.tributeNameInd, True)
            self.SetVisible(self.districtInd, True)
            self.SetVisible(self.fallenHeading, False)
            self.SetVisible(self.fallenList, True)

            for name in li:
                comp.AddTimer((li.keys().index(name) + 1)*delay, lambda n: SetFallenInformation(n, li[n]), name)
        comp.AddTimer(4.0, seq1)

        comp.AddTimer(34.0, lambda n: self.SetVisible(n, False), self.fallenPanel)

    def ShowCountdown(self, time):
        if time >= 0:
            self.SetVisible(self.timerPanel, True)
            self.SetText(self.timerInd, time)
        else:
            self.SetVisible(self.timerPanel, False)

    def close(self):
        self.SetVisible("", False)
        clientApi.SetInputMode(0)
        clientApi.HideSlotBarGui(False)
