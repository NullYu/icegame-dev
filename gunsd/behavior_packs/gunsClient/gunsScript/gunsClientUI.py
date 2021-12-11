import client.extraClientApi as clientApi
import datetime
import time

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
TouchEvent = clientApi.GetMinecraftEnum().TouchEvent
ClientSystem = clientApi.GetSystem("guns", "gunsClient")
c = ClientSystem.c

class gunsScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        print '==== %s ====' % 'init TestScreen'

        self.ammo = 0
        self.reserveAmmo = 0
        self.maxAmmo = 0

        self.health = 100
        self.isArmor = False
        self.armor = 100

        self.periodicalDamage = 0
        self.gunId = 0
        # scope type: 0=no scope 1=zoom only 2=full scope
        self.scopeType = 0
        self.scopeMode = 0
        # fire type: 0=manual 1=auto 2=bolt 3=charge
        self.fireMode = 0
        self.fireCooldown = False
        self.fireBtnHeld = False
        # can fire right now
        self.canFire = False

        self.crosshairOverlay = '/image1'
        self.scopeOverlay = '/image0'

        self.buttonsPanel = '/panel0'
        self.fireBtn = self.buttonsPanel + '/button0'
        self.reloadBtn = self.buttonsPanel + '/button1'
        self.scopeBtn = self.buttonsPanel + '/button2'
        self.meleeBtn = self.buttonsPanel + '/button3'
        self.ammoInd = self.buttonsPanel + '/label0'

        self.healthPanel = '/panel1'
        self.healthInd = self.healthPanel + '/label1'
        self.armorInd = self.healthPanel + '/image3'
        self.armorDurationInd = self.armorInd + '/label2'

        self.bloodPanel = '/panel2'
        self.bloodFov = self.bloodPanel + '/image4'
        self.splatterPanel = self.bloodPanel + '/panel3'
        self.splatter1 = self.splatterPanel + '/blood1'
        self.splatter2 = self.splatterPanel + '/blood2'
        self.splatter3 = self.splatterPanel + '/blood3'

        self.damageIndPanel = '/panel4'
        self.damageInFovInd = '/dmgind1'
        self.damageNotInFovInd = '/dmgind2'

    def MakeTimer(self, isRepeat, delay, func, args=None):
        comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        if isRepeat:
            comp.AddRepeatedTimer(delay, func, args)
        else:
            comp.AddTimer(delay, func, args)

    def epoch2Datetime(self, epoch):
        ts = datetime.datetime.fromtimestamp(int(epoch) + 0)
        return ts.strftime('%Y%m%d%H%M%S')

    def datetime2Epoch(self, y, m, d, h, mi):
        # Datetime must be in tuple(YYYY, MM, DD, HH, mm), for example, (1977, 12, 1, 0, 0)
        ts = (datetime.datetime(y, m, d, h, mi) - datetime.datetime(1970, 1, 1)).total_seconds()
        return int(ts)

    def Create(self):
        print '==== %s ====' % 'gunsScreen Create'

        self.AddTouchEventHandler(self.fireBtn, self.fire, {"isSwallow": True})
        self.AddTouchEventHandler(self.scopeBtn, self.scope, {"isSwallow": True})
        self.AddTouchEventHandler(self.meleeBtn, self.melee, {"isSwallow": True})
        self.AddTouchEventHandler(self.reloadBtn, self.reload, {"isSwallow": True})
        self.MakeTimer(True, 0.08, self.AutoFireCycle)
        self.UpdateData()

    def InitScreen(self):
        print '==== %s ====' % 'adminScreen Init'

        # self.SetVisible('/panel0', False)
        self.SetVisible("", True)
        self.SetVisible(self.scopeOverlay, False)
        self.SetVisible(self.crosshairOverlay, True)
        self.SetVisible(self.damageIndPanel, False)
        self.SetVisible(self.bloodPanel, False)

        self.SetText(self.ammoInd, "%s/%s" % (self.ammo, self.reserveAmmo))
        self.SetText(self.healthInd, str(self.health))
        # self.InitTextPanel()

    def UpdateData(self):
        self.SetText(self.healthInd, str(self.health))
        self.SetVisible(self.armorInd, self.isArmor)
        self.SetText(self.armorDurationInd, str(self.armor))
        self.SetText(self.ammoInd, "%s/%s" % (self.ammo, self.reserveAmmo))

    def AutoFireCycle(self, arg):
        if self.ammo > 0 and self.fireBtnHeld and self.fireMode == 1:
            self.ammo -= 1
            ClientSystem.ReturnToServer({
                'action': 'fire',
                'weaponId': self.gunId
            })
            ClientSystem.PlayMusic('sfx.guns.fire.auto')

    def fire(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchDown or event == TouchEvent.TouchUp:
            print 'shot fired, ammo=%s firemode=%s cooldown=%s' % (self.ammo, self.fireMode, self.fireCooldown)
            if self.ammo > 0:
                if self.fireMode == 0:
                    if event == TouchEvent.TouchUp and not self.fireCooldown:
                        self.ammo -= 1
                        self.fireCooldown = True
                        def a(arg):
                            self.fireCooldown = False
                        self.MakeTimer(False, 0.22, a)
                        self.UpdateData()

                        ClientSystem.ReturnToServer({
                            'action': 'fire',
                            'weaponId': self.gunId
                        })
                        ClientSystem.PlayMusic('sfx.guns.fire.manual')

                elif self.fireMode == 1:
                    if self.ammo > 0 and not self.fireCooldown:
                        if event == TouchEvent.TouchDown:
                            # auto fire
                            self.fireBtnHeld = True
                        elif event == TouchEvent.TouchUp:
                            self.fireBtnHeld = False
                    else:
                        ClientSystem.PlayMusic('sfx.guns.empty')
                elif self.fireMode == 2:
                    if event == TouchEvent.TouchUp and not self.fireCooldown:
                        # fire
                        self.ammo -= 1
                        self.fireCooldown = True
                        self.scopeMode = 2
                        self.scope({'event': TouchEvent.TouchUp})

                        def a(arg):
                            self.fireCooldown = False
                            self.scopeMode = 0
                            self.scope({'event': TouchEvent.TouchUp})

                        self.MakeTimer(False, 1.46, a)
                        self.UpdateData()

                        ClientSystem.ReturnToServer({
                            'action': 'fire',
                            'weaponId': self.gunId
                        })
                        if self.gunId == 13:
                            ClientSystem.PlayMusic('sfx.guns.awp')
                        else:
                            ClientSystem.PlayMusic('sfx.guns.fire.manual')

                        def b(args):
                            ClientSystem.PlayMusic('sfx.guns.bolt')
                        self.MakeTimer(False, 0.3, b)
                elif self.fireMode == 3:
                    self.ammo -= 1
                    self.fireCooldown = True

                    def a(arg):
                        self.fireCooldown = False

                    def b(arg):
                        ClientSystem.ReturnToServer({
                            'action': 'fire',
                            'weaponId': self.gunId
                        })
                        ClientSystem.PlayMusic('sfx.guns.fire.manual')
                        self.UpdateData()

                    self.MakeTimer(False, 0.4, b)
                    self.MakeTimer(False, 0.3, a)
            else:
                print 'mags empty'
                ClientSystem.PlayMusic('sfx.guns.empty')
            self.UpdateData()

    def reload(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            print 'reload'
            if self.reserveAmmo > 0:
                self.scopeMode = 2
                self.scope({'event': TouchEvent.TouchUp})
                comp = clientApi.GetEngineCompFactory().CreateCamera(clientApi.GetLevelId())
                comp.SetFov(60)
                self.fireCooldown = True
                self.ammo = 0
                if self.reserveAmmo >= self.maxAmmo:
                    self.ammo = self.maxAmmo
                    self.reserveAmmo -= self.maxAmmo
                else:
                    self.ammo = self.reserveAmmo
                    self.reserveAmmo = 0

                def a(args):
                    self.fireCooldown = False
                    self.UpdateData()
                self.MakeTimer(False, 2.5, a)
                ClientSystem.PlayMusic('sfx.guns.reload')
            else:
                ClientSystem.PlayMusic('sfx.guns.empty')

    def scope(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and self.scopeType:
            print 'scope'
            if self.scopeType == 1:
                if self.scopeMode == 0:
                    self.scopeMode = 1
                    comp = clientApi.GetEngineCompFactory().CreateCamera(clientApi.GetLevelId())
                    comp.SetFov(45)
                elif self.scopeMode == 1:
                    self.scopeMode = 0
                    comp = clientApi.GetEngineCompFactory().CreateCamera(clientApi.GetLevelId())
                    comp.SetFov(60)
            elif self.scopeType == 2:
                if self.scopeMode == 0:
                    self.scopeMode = 1
                    comp = clientApi.GetEngineCompFactory().CreateCamera(clientApi.GetLevelId())
                    comp.SetFov(45)
                    self.SetVisible(self.crosshairOverlay, False)
                    self.SetVisible(self.scopeOverlay, True)
                elif self.scopeMode == 1:
                    self.scopeMode = 2
                    comp = clientApi.GetEngineCompFactory().CreateCamera(clientApi.GetLevelId())
                    comp.SetFov(30)
                elif self.scopeMode == 2:
                    self.scopeMode = 0
                    comp = clientApi.GetEngineCompFactory().CreateCamera(clientApi.GetLevelId())
                    comp.SetFov(60)
                    self.SetVisible(self.crosshairOverlay, True)
                    self.SetVisible(self.scopeOverlay, False)

    def melee(self, args):
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp and not self.fireCooldown:
            print 'melee'
            self.fireCooldown = True

            def a(arg):
                self.fireCooldown = False

            self.MakeTimer(False, 0.9, a)
            self.UpdateData()

            ClientSystem.ReturnToServer({
                'action': 'melee',
                'weaponId': self.gunId
            })
            ClientSystem.PlayMusic('sfx.guns.fire.auto')
    def ShowUi(self):
        self.SetVisible("", True)

    def ExitUi(self, args):
        print 'UISCRIPT CALL ExitUi args=%s' % (args,)
        event = args['TouchEvent']
        if event == TouchEvent.TouchUp:
            self.close()

    def close(self):
        self.SetVisible("", False)
        self.InitTextPanel()
        clientApi.HideSlotBarGui(False)
        pass