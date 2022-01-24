# -*- coding: utf-8 -*-
import server.extraServerApi as serverApi
import time
import json
import random
import datetime
import v5Script.v5Consts as c
import lobbyGame.netgameApi as lobbyGameApi
import apolloCommon.commonNetgameApi as commonNetgameApi

"""
Y1S0 names:
1. handcannon
2. tnt
3. jumpboost
4. distraction
5. escape
"""

def sendCmd(cmd, playerId):
    comp = serverApi.GetEngineCompFactory().CreateCommand(serverApi.GetLevelId())
    comp.SetCommand(cmd, playerId)

def dist(x1, y1, z1, x2, y2, z2):
    """
    运算3维空间距离，返回float
    """
    p = ((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) ** 0.5
    re = float('%.1f' % p)
    return re

def setPos(playerId, pos):
    comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
    re = comp.SetFootPos(pos)
    return re

def sendTitle(title, type, playerId):
    if (type == 1):
        sendCmd("/title @s title " + title, playerId)
    elif (type == 2):
        sendCmd("/title @s subtitle " + title, playerId)
    elif (type == 3):
        sendCmd("/title @s actionbar " + title, playerId)
    else:
        print 'invalid params for call/sendTitle(): type'

def DoSkill(playerId, skillName, teamDict, siteIndex, eqpSlot):
    if skillName == "handcannon":
        comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
        sPos = comp.GetPos()
        rComp = serverApi.GetEngineCompFactory().CreateRot(playerId)
        sDir = serverApi.GetDirFromRot((rComp.GetRot()))
        comp = serverApi.GetEngineCompFactory().CreateProjectile(serverApi.GetLevelId())
        param = {
            'position': sPos,
            'direction': sDir
            #'damage': 999
        }
        comp.CreateProjectileEntity(playerId, "minecraft:fireball", param)

    elif skillName == "tnt":
        sendCmd('/summon tnt', playerId)

    elif skillName == "jumpboost":
        sendCmd('/effect @s jump_boost 25 3 true', playerId)

    elif skillName == "distraction":
        li = []
        distBuffer = 99999
        targetBuffer = None

        for player in teamDict:
            if teamDict[player] != teamDict[playerId]:
                li.append(player)

        for player in li:
            comp = serverApi.GetEngineCompFactory().CreatePos(player)
            tPos = comp.GetPos()
            comp = serverApi.GetEngineCompFactory().CreatePos(playerId)
            sPos = comp.GetPos()
            distance = dist(tPos[0], tPos[1], tPos[2], sPos[0], sPos[1], sPos[2])
            if distance < distBuffer:
                distBuffer = distance
                targetBuffer = player

        if targetBuffer:
            sendCmd('/effect @s nausea 10 1 true', targetBuffer)

    elif skillName == "escape":
        comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
        comp.ChangeSelectSlot(4)

        def a():
            if teamDict[playerId] == 0:
                setPos(playerId, c.defendersSpawn[siteIndex])
            else:
                setPos(playerId, c.attackersSpawn)

            comp = serverApi.GetEngineCompFactory().CreatePlayer(playerId)
            comp.ChangeSelectSlot(eqpSlot - 1)

        commonNetgameApi.AddTimer(4.0, a)
        sendTitle('§l§6技能前摇4秒...', 3, playerId)
