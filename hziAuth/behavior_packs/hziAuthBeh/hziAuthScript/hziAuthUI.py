# -*- coding: utf-8 -*-
# @Author : uni_kevin(可乐)

import logging
import random

import mod.client.extraClientApi as clientApi

connect = '/variables_button_mappings_and_controls/safezone_screen_matrix/inner_matrix/safezone_screen_panel/root_screen_panel'
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()
LocalPlayerId = clientApi.GetLocalPlayerId()
PhoneReg = '^1(?:34[0-8]|3[5-9]\d|5[0-2,7-9]\d|7[28]\d|8[2-4,7-8]\d|9[5,7,8]\d|3[0-2]\d|[578][56]\d|66\d|96\d|33\d|53\d|7[37]\d|8[019]\d|9[0139]\d|92\d)\d{7}$'


class HziAuthUI(ScreenNode):
    def __init__(self, namespace, name, param):
        super(HziAuthUI, self).__init__(namespace, name, param)
        self.codeReset = False
        self.secondCode = 0
        self.secondBg = 0
        self.timer = None
        self.titleC = None

    def Timer(self):
        if self.secondBg < 10:
            self.secondBg += 1
        else:
            self.secondBg = 0
            self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/banner').asImage().SetSprite('textures/ui/hzi_auth/banner%s' % random.randint(1, 4))
        if self.codeReset:
            self.secondCode -= 1
            if self.secondCode <= -1:
                self.codeReset = False
                self.ResetCodeButton()
            else:
                self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step2/button3/label2').asLabel().SetText(
                '§l重新发送(%ss)' % self.secondCode)

    def Create(self):
        game = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        self.timer = game.AddRepeatedTimer(1, self.Timer)
        self.titleC = self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/title').asLabel()
        refuseButton = self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step1/button1/').asButton()
        refuseButton.AddTouchEventParams()
        system = clientApi.GetSystem('HziAuth', 'HziAuthBeh')
        if not system.mustAuth:
            label = self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step1/button1/button_label').asLabel()
            label.SetTextColor((65 / 256.0, 65 / 256.0, 65 / 256.0))
            label.SetText('§l我再想想')
        def RefuseButtonUp(e):
            system.NotifyToServer('PlayerRefuse', {'client': LocalPlayerId})
            if not system.mustAuth:
                system.needReg = False
            self.SetRemove()
        refuseButton.SetButtonTouchUpCallback(RefuseButtonUp)
        agreeButton = self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step1/button0').asButton()
        agreeButton.AddTouchEventParams()
        def AgreeButtonUp(e):
            self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step1').SetVisible(False)
            self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step2').SetVisible(True)
        agreeButton.SetButtonTouchUpCallback(AgreeButtonUp)

        sendCodeButton = self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step2/button3').asButton()
        sendCodeButton.AddTouchEventParams()
        def SendCodeButtonUp(e):
            phoneNumber = self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step2/text_edit_box0').asTextEditBox().GetEditText()
            if re.match(PhoneReg, str(phoneNumber)):
                sendCodeButton.SetTouchEnable(False)
                self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step2/button3/image0').SetVisible(True)
                self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step2/button3/label2').asLabel().SetText(
                    '§l发送中')
                system.NotifyToServer('SendCode', {'client': LocalPlayerId, 'phone': phoneNumber})
            else:
                self.ShowTips('手机号不合法')
        sendCodeButton.SetButtonTouchUpCallback(SendCodeButtonUp)
        def ConfirmCodeButtonUp(e):
            phoneNumber = self.GetBaseUIControl(
                connect + '/auth_panel0/auth_image_bg/step2/text_edit_box0').asTextEditBox().GetEditText()
            if re.match(PhoneReg, str(phoneNumber)):
                code = self.GetBaseUIControl(
                    connect + '/auth_panel0/auth_image_bg/step2/text_edit_box1').asTextEditBox().GetEditText()
                if code and code.isdigit() and len(code) == 6:
                    confirmCodeButton.SetTouchEnable(False)
                    self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step2/button2/image2').SetVisible(True)
                    self.GetBaseUIControl(
                        connect + '/auth_panel0/auth_image_bg/step2/button2/button_label').asLabel().SetText('§l请稍后')
                    system.NotifyToServer('AuthCode', {'client': LocalPlayerId, 'phone': phoneNumber, 'code': int(code)})
                else:
                    self.ShowTips('请输入正确验证码')
            else:
                self.ShowTips('手机号不合法')
        confirmCodeButton = self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step2/button2').asButton()
        confirmCodeButton.AddTouchEventParams()
        confirmCodeButton.SetButtonTouchUpCallback(ConfirmCodeButtonUp)


    def ResetCodeButton(self):
        sendCodeButton = self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step2/button3').asButton()
        sendCodeButton.SetTouchEnable(True)
        self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step2/button3/image0').SetVisible(False)
        self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step2/button3/label2').asLabel().SetText('§l获取验证码')

    def AuthRequest(self, e):
        self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step2/button2').asButton().SetTouchEnable(True)
        self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step2/button2/image2').SetVisible(False)
        self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step2/button2/button_label').asLabel().SetText(
            '§l一个手机号只能绑定一个uid， 点击确认绑定')
        if e['code'] == 200:
            self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step2').SetVisible(False)
            self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step3').SetVisible(True)
            def OkButtonUp(e):
                system = clientApi.GetSystem('HziAuth', 'HziAuthBeh')
                if system:
                    system.needReg = False
                self.SetRemove()
            okButton = self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step3/button4').asButton()
            okButton.AddTouchEventParams()
            okButton.SetButtonTouchUpCallback(OkButtonUp)
        if e['code'] == -1:
            self.ShowTips('系统错误')
        if e['code'] == 0:
            self.ShowTips('验证码错误')
        if e['code'] == 1:
            self.ShowTips('你的uid或手机号被占用')

    def SendRequest(self, e):
        if e['code'] == 200:
            self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step2/button3/label2').asLabel().SetText(
                '§l重新发送(30s)')
            self.codeReset = True
            self.secondCode = 31
            self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step2/button2').asButton().SetTouchEnable(True)
            self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step2/button2/image2').SetVisible(False)
            self.GetBaseUIControl(connect + '/auth_panel0/auth_image_bg/step2/button2/button_label').asLabel().SetText('§l一个手机号只能绑定一个uid， 点击确认绑定')
            self.ShowTips('验证码已发送')
        if e['code'] == -1:
            self.ShowTips('系统错误')
            self.ResetCodeButton()
        if e['code'] == 2:
            self.ShowTips('你已经绑定过手机号')
            self.ResetCodeButton()
        if e['code'] == 3:
            self.ShowTips('此手机号已经被占用')
            self.ResetCodeButton()
        if e['code'] == 1:
            self.ShowTips('今日你的验证码发送次数达到上限')
            self.ResetCodeButton()

    def ShowTips(self, msg, daley=2):
        self.GetBaseUIControl(connect + '/auth_panel0/msg').SetVisible(True)
        self.GetBaseUIControl(connect + '/auth_panel0/msg/text').asLabel().SetText(msg.replace('&', '§'))
        game = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        game.AddTimer(daley, self.GetBaseUIControl(connect + '/auth_panel0/msg').SetVisible, False)


    def Destroy(self):
        game = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        game.CancelTimer(self.timer)