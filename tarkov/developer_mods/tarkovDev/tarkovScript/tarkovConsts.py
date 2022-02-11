# -*- coding: utf-8 -*-
# 请不要删掉上面这行！！！

# ICE_GAME 塔科夫dan'fu 配置文档
# v1.1
# 注意：每个地图需分class
# ################################

# TODO IMPORTANT!!! Debug mode switch
# Plugin will not function while in debug mode!!!
debugMode = True

#通用设置
# 多少人后会开始倒计时？
startCountdown = 2
# 多少人后会缩短倒计时
enoughPlayers = 10

exampleParam = {
    # the amount of spawn points must be higher than the amount of player allowed on server
    'spawnPos': [(0, 0, 0), (1, 1, 1)],
    # players within 5 block radius of evacPoint gets counted
    'evacPoints': [(2, 2, 2), (3, 3, 3)],
    'evacPointNames': ['Evac_A', 'Evac_B'],
    'scavSpawns': [(4, 4, 4), (5, 5, 5)],
    'evacTime': 1800
}

class Constructor:
    spawnPos = None
    evacPoints = None
    scavSpawns = None
    evacTime = None
    evacPointNames = None

    def __init__(self, params):
        self.spawnPos = params['spawnPos']
        self.evacPoints = params['evacPoints']
        self.scavSpawns = params['scavSpawns']
        self.evacTime = params['evacTime']
        self.evacPointNames = params['evacPointNames']

# start for each map
exampleMap = Constructor({
    'spawnPos': [(0, 0, 0), (1, 1, 1)],
    # players within 5 block radius of evacPoint gets counted
    'evacPoints': [(2, 2, 2), (3, 3, 3)],
    'evacPointNames': ['Evac_A', 'Evac_B'],
    'scavSpawns': [(4, 4, 4), (5, 5, 5)],
    'evacTime': 1800
})