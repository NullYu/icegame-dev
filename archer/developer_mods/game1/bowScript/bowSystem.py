# -*- coding: utf-8 -*-
#数据值1:False   0:True

import server.extraServerApi as serverApi
import time
import random
import lobbyGame.netgameApi as lobbyGameApi

ServerSystem = serverApi.GetServerSystemCls()

class bowServerSys(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        lobbyGameApi.ShieldPlayerJoinText(True)
        self.ListenEvents()
        self.cmd = serverApi.GetEngineCompFactory().CreateCommand(serverApi.GetLevelId())
        self.cmd.SetCommand('setworldspawn 0 204 0')
        self.cs=self.cs1=self.fd=self.pla=0
        self.time=30
        self.player=[]
        self.redteam=[]
        self.greenteam=[]
        self.bool=False
        leveldata = serverApi.GetEngineCompFactory().CreateExtraData(serverApi.GetLevelId())
        leveldata.SetExtraData('IsStart',1)

    def ListenEvents(self):
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnScriptTickServer", self,self.OnScriptTickServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerChatEvent", self,self.chat)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "DelServerPlayerEvent", self,self.OnDelServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "AddServerPlayerEvent",self,self.OnAddServerPlayer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerEntityTryPlaceBlockEvent",self,self.OnServerEntityTryPlaceBlock)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ActuallyHurtServerEvent",self,self.OnActuallyHurtServer)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerPlayerTryDestroyBlockEvent",self,self.desblo)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "PlayerDieEvent",self,self.OnPlayerDie)

    def Destroy(self):
        self.UnListenForEvent("gameutils", "gameutilsClient", 'TestRequest', self, self.OnTestRequest)

    def chat(self,args):
        getname=serverApi.GetEngineCompFactory().CreateName(args['playerId'])
        # if args['message'] == 'lobby':
        #     lobbyGameApi.TransferToOtherServer(args['playerId'], 'lobby')
        if args['message'] == 'restart' and (getname.GetName() == 'The_Yrxs' or getname.GetName() == '夜无希i'):
            self.restart()

    def OnAddServerPlayer(self,args):
        self.cmd.SetCommand('spawnpoint @a 0 204 0')
        pos=serverApi.GetEngineCompFactory().CreatePos(args['id'])
        pos.SetPos((0.5,203,0.5))
        name=serverApi.GetEngineCompFactory().CreateName(args['id'])
        comp = serverApi.GetEngineCompFactory().CreateExtraData(args['id'])
        comp.SetExtraData("IsDestroyBlock",1)
        comp.SetExtraData("IsAttack",1)
        comp.SetExtraData("IsPlayer",1)
        if len(serverApi.GetPlayerList()) > 6:
            self.cmd.SetCommand('tellraw @s {"rawtext":[{"text":"§c这个服务器好像爆满了!"}]}',args['playerId'])
            lobbyGameApi.TransferToOtherServer(args['playerId'], 'lobby')

    def OnDelServerPlayer(self,args):
        pass

    def OnScriptTickServer(self):
        id = serverApi.GetPlayerList()
        leveldata = serverApi.GetEngineCompFactory().CreateExtraData(serverApi.GetLevelId())
        
        self.cs+=1
        if self.cs > 30:
            if leveldata.GetExtraData('IsStart') == 1:
                self.cmd.SetCommand('clear @a')
            if leveldata.GetExtraData('IsStart') == 0 and self.redteam == False and self.greenteam == False:
                self.restart()
            self.cmd.SetCommand('execute @a ~~~ detect ~~-1~ grass 0 kill @s')
            self.cmd.SetCommand('execute @a[y=181,r=5] ~~~ detect ~~-1~ diamond_block 0 replaceitem entity @s slot.hotbar 8 arrow 16')
            self.cmd.SetCommand('scoreboard players set "§7[%s]v0.1" server 7'%time.strftime("%Y-%m-%d",time.localtime()))
            self.cmd.SetCommand('scoreboard players set "" server 6')
            self.cmd.SetCommand('scoreboard players set "  §c红队 %d" server 5'%len(self.redteam))
            self.cmd.SetCommand('scoreboard players set "  §a绿队 %d" server 4'%len(self.greenteam))
            self.cmd.SetCommand('scoreboard players reset "  §c红队 %s"'%str(len(self.redteam)-1))
            self.cmd.SetCommand('scoreboard players reset "  §a绿队 %s"'%str(len(self.greenteam)-1))
            self.cmd.SetCommand('scoreboard players reset "  §c红队 %s"'%str(len(self.redteam)+1))
            self.cmd.SetCommand('scoreboard players reset "  §a绿队 %s"'%str(len(self.greenteam)+1))
            self.cmd.SetCommand('scoreboard players set " " server 3')
            self.cmd.SetCommand('scoreboard players set "  §e人数: (%s/6)" server 2'%len(id))
            self.cmd.SetCommand('scoreboard players set "  " server 1')
            self.cmd.SetCommand('scoreboard players set ""§7ICE-ARCHER-%s" server 0' % (lobbyGameApi.GetServerId()))
            self.cmd.SetCommand('scoreboard players reset "  §e人数: (%d/6)"'%(len(id)-1))
            self.cmd.SetCommand('scoreboard players reset "  §e人数: (%d/6)"'%(len(id)+1))
            self.cmd.SetCommand('title @a[x=0,y=201,z=0,r=1] actionbar §l★ 游戏时站在钻石块上面可刷新物品 ★')
            for id1 in id:
                comp = serverApi.GetEngineCompFactory().CreatePlayer(id1)
                comp.SetPlayerHunger(20)
            self.cs=0
        #test a
        if len(serverApi.GetPlayerList()) >= 2:
            self.cs1+=1
            if self.cs1 > 30:
                self.cs1=0
                print "\n玩家:",self.player,"\n红队:",self.redteam,"\n绿队:",self.greenteam,"\n迭代:",self.fd
                if leveldata.GetExtraData('IsStart') == 1:
                    self.cmd.SetCommand('title @a title 正在抽取玩家...')
                    for c in range(0,len(id)+1):
                        playerdata = serverApi.GetEngineCompFactory().CreateExtraData(id[self.pla])
                        if playerdata.GetExtraData("IsPlayer") == 1:
                            self.player.append(id[self.pla])
                            playerdata.SetExtraData("IsPlayer",0)
                            self.pla+=1
                        leveldata.SetExtraData('IsStart',0)

                if leveldata.GetExtraData('IsStart') == 0:
                    if len(self.player) <= 1:
                        self.cmd.SetCommand('tellraw @a {"rawtext":[{"text":"§c人数不足,取消倒计时"}]}')
                        self.restart()
                    elif len(self.player) >= 2:
                        if self.time>0:
                            self.time-=1
                            self.cmd.SetCommand('title @a actionbar 游戏将在 %s 秒开始'%self.time)
                            self.cmd.SetCommand('execute @a ~~~ playsound random.pop')
                            self.red=[]
                            self.green=[]
                        elif self.time == 0:
                            self.cmd.SetCommand('scoreboard players set "  §e游戏中..." server 6')
                            for i in range(0,len(id)):
                                if self.fd > len(id):
                                    break
                                if (self.fd+1) % 2 == 1 :
                                    self.redteam.append(self.player[self.fd])
                                else:
                                    self.greenteam.append(self.player[self.fd])
                                self.fd+=1
                                self.time=-1
                            else:
                                for player in self.player:
                                    comp = serverApi.GetEngineCompFactory().CreateGame(player)
                                    comp.SetDisableDropItem(True)
                                    playerdata = serverApi.GetEngineCompFactory().CreateExtraData(player)
                                    playerdata.SetExtraData('IsAttack',0)
                                    Item = serverApi.GetEngineCompFactory().CreateItem(player)
                                    item1 = {
                                            'itemName': 'minecraft:bow',
                                            'count': 1,
                                            'enchantData': [(serverApi.GetMinecraftEnum().EnchantType.BowDamage, 1),],
                                            'auxValue': 0,
                                            'customTips':'§l 弓 §r',
                                            'extraId': '',
                                            'userData': {},
                                    }
                                    item2 = {
                                            'itemName': 'minecraft:arrow',
                                            'count': 16,
                                            'enchantData': [(serverApi.GetMinecraftEnum().EnchantType.BowDamage, 1),],
                                            'auxValue': 0,
                                            'customTips':'§l 箭 §r',
                                            'extraId': '',
                                            'userData': {},
                                    }
                                    Item.SpawnItemToPlayerInv(item1, player, 0)
                                    Item.SpawnItemToPlayerInv(item2, player, 8)
                                for player in self.redteam:
                                    Item = serverApi.GetEngineCompFactory().CreateItem(player)
                                    item14 = {
                                            'itemName': 'minecraft:wool',
                                            'count': 1,
                                            'enchantData': [(serverApi.GetMinecraftEnum().EnchantType.BowDamage, 1),],
                                            'auxValue': 14,
                                            'customTips':'§l§c 你是红队 §r',
                                            'extraId': '',
                                            'userData': {},
                                    }
                                    Item.SpawnItemToPlayerInv(item14, player,4)
                                    Pos = serverApi.GetEngineCompFactory().CreatePos(player)
                                    Pos.SetPos((0.5,181,-24.5))
                                    redname = serverApi.GetEngineCompFactory().CreateName(player)
                                    redname.SetPlayerPrefixAndSuffixName("【红队】 ",serverApi.GenerateColor('RED'),' ',serverApi.GenerateColor('RED'))
                                for player in self.greenteam:
                                    Item = serverApi.GetEngineCompFactory().CreateItem(player)
                                    item5 = {
                                            'itemName': 'minecraft:wool',
                                            'count': 1,
                                            'enchantData': [(serverApi.GetMinecraftEnum().EnchantType.BowDamage, 1),],
                                            'auxValue': 5,
                                            'customTips':'§l§c 你是绿队 §r',
                                            'extraId': '',
                                            'userData': {},
                                    }
                                    Item.SpawnItemToPlayerInv(item5, player, 4)
                                    Pos = serverApi.GetEngineCompFactory().CreatePos(player)
                                    Pos.SetPos((0.5,181,25.5))
                                    greenname = serverApi.GetEngineCompFactory().CreateName(player)
                                    greenname.SetPlayerPrefixAndSuffixName("【绿队】 ",serverApi.GenerateColor('GREEN'),' ',serverApi.GenerateColor('GREEN'))
                                    self.bool = True
                if self.redteam == [] and leveldata.GetExtraData('IsStart') == 0 and self.bool:
                    self.cmd.SetCommand('tellraw @a {"rawtext":[{"text":"§d§l===== §e游戏结束 §d=====\n|§e 胜者: §a[绿队] \n§d|§c 败者: §c[红队]\n§d|\n§d|  §e获得4NEKO"}]}')
                    ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')
                    for player in self.greenteam:
                        ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(player), 4, 'archer survive')
                    self.restart()

                if self.greenteam == [] and leveldata.GetExtraData('IsStart') == 0 and self.bool:
                    self.cmd.SetCommand('tellraw @a {"rawtext":[{"text":"§d§l===== §e游戏结束 §d=====\n|§e 胜者: §c[红队]\n§d|§c 败者: §a[绿队]\n§d|\n§d|  §e获得4NEKO"}]}')
                    ecoSystem = serverApi.GetSystem('eco', 'ecoSystem')
                    for player in self.redteam:
                        ecoSystem.GivePlayerEco(lobbyGameApi.GetPlayerUid(player), 4, 'archer survive')
                    self.restart()
    
    def OnActuallyHurtServer(self,args):
        comp = serverApi.GetEngineCompFactory().CreateExtraData(args['srcId'])
        if comp.GetExtraData("IsAttack") == 1 or args['cause'] != "projectile":
            args['damage'] = 0
        elif comp.GetExtraData("IsAttack") == 0 and args['cause'] == "projectile":
            args['damage'] =20
        if args['srcId'] in self.redteam and args['entityId'] in self.redteam:
            args['damage'] =0
        if args['srcId'] in self.greenteam and args['entityId'] in self.greenteam:
            args['damage'] =0
        self.cmd.SetCommand('execute @a ~~~ playsound random.levelup')

    def OnPlayerDie(self,args):
        if args['id'] in self.redteam:
            self.redteam.remove(args['id'])
        if args['id'] in self.greenteam:
            self.greenteam.remove(args['id'])
        Pos = serverApi.GetEngineCompFactory().CreatePos(args['id'])
        Pos.SetPos((0.5,204,0.5))

    def desblo(self,args):
        comp = serverApi.GetEngineCompFactory().CreateExtraData(args['playerId'])
        if comp.GetExtraData("IsDestroyBlock") == 1:
            args['cancel'] = True
            self.cmd.SetCommand('tellraw @s {"rawtext":[{"text":"§c请勿破坏该地区方块!"}]}',args['playerId'])

    def OnServerEntityTryPlaceBlock(self,args):
        args['cancel'] = True

    def restart(self):
        for i in serverApi.GetPlayerList():
            name = serverApi.GetEngineCompFactory().CreateName(i)
            name.SetPlayerPrefixAndSuffixName("",serverApi.GenerateColor('WHITE'),'',serverApi.GenerateColor('WHITE'))
            Pos = serverApi.GetEngineCompFactory().CreatePos(i)
            Pos.SetPos((0.5,204,0.5))
        self.cmd.SetCommand('kill @e[type=!player]')
        self.cmd.SetCommand('scoreboard objectives remove server')
        self.cmd.SetCommand('scoreboard objectives add server dummy "§d§l弓箭手作战"')
        self.cmd.SetCommand('scoreboard objectives setdisplay sidebar server')
        self.cmd.SetCommand('scoreboard players set "§7[%s]v0.1" server 7'%time.strftime("%Y-%m-%d",time.localtime()))
        self.cmd.SetCommand('scoreboard players set "" server 6')
        self.cmd.SetCommand('scoreboard players set "  §c红队 %s" server 5'%0)
        self.cmd.SetCommand('scoreboard players set "  §a绿队 %s" server 4'%0)
        self.cmd.SetCommand('scoreboard players set " " server 3')
        self.cmd.SetCommand('scoreboard players set "  §e人数: (%s/6)" server 2'%len(serverApi.GetPlayerList()))
        self.cmd.SetCommand('scoreboard players set "  " server 1')
        self.cmd.SetCommand('scoreboard players set "§7ICE-ARCHER-%s" server 0' % (lobbyGameApi.GetServerId()))
        self.cmd.SetCommand('execute @a ~~~ playsound random.levelup')
        self.redteam=[]
        self.greenteam=[]
        self.player=[]
        self.time=30
        self.fd=self.pla=0
        self.bool=False
        ld = serverApi.GetEngineCompFactory().CreateExtraData(serverApi.GetLevelId())
        ld.SetExtraData('IsStart',1)
        for i in serverApi.GetPlayerList():
            comp = serverApi.GetEngineCompFactory().CreateGame(i)
            comp.SetDisableDropItem(False)
            pd = serverApi.GetEngineCompFactory().CreateExtraData(i)
            pd.SetExtraData('IsPlayer',1)
            pd.SetExtraData('IsAttack',1)