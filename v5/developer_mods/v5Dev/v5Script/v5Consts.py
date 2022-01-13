# -*- coding: utf-8 -*-
# 请不要删掉上面这行！！！

# ICE_GAME 5v5 配置文档
# v1.1
# 新增 大厅等待人数
# ################################

# TODO IMPORTANT!!! Debug mode switch
# Plugin will not function while in debug mode!!!
debugMode = True

# 全局坐标设置
# 等候大厅的坐标
lobbyPos = (0, 242, 0)
# 玩家淘汰后的重生位置
spectatorPos = (0, 109, 0)
# 多少人后会开始倒计时？
startCountdown = 2
# 多少人后会缩短倒计时
enoughPlayers = 10
# 进攻方（CT）出生点
attackersSpawn = (0, 0, 0)
# 防守方（T）出生点
defendersSpawn = [(0, 0, 0), (1, 1, 1), (2, 2, 2), (3, 3, 3)]
# 炸弹爆点
bombSites = {
    1: [(0, 0, 0), (1, 1, 1)],
    2: [(0, 0, 0), (1, 1, 1)],
    3: [(0, 0, 0), (1, 1, 1)],
    4: [(0, 0, 0), (1, 1, 1)]
}
# 准备阶段路障
mapBlockers = [
    (0, 0, 0), (1, 1, 1)
]


# 全局设置
roundTime = 170

# 背包设置
# format: <tuple>(primary, secondary, armor)
weaponPresets = {
    1: ('diamond_sword', 'bow', 'none'),
    2: ('iron_sword', 'wooden_sword/2', 'iron'),
    3: ('iron_sword', 'wooden_sword/2', 'iron'),
    4: ('wooden_sword', 'bow/1', 'iron'),
    5: ('stone_sword/1', 'shield', 'diamond')
}

# format: <tuple>(id, uses)
skillPresets = {
    1: ('handcannon', 1),
    2: ('tnt', 4),
    3: ('jumpboost', 1),
    4: ('distraction', 2),
    5: ('escape', 1)
}

# 对局设置
# 总共加固墙面数
reinfsAllowed = 180
# 总共点的数量
totalSites = 4

# 计时器设置
# 准备阶段时间
phaseTimes = {
    0: 30,
    1: 30,
    2: 175
}


# =============================常量定义区域，请勿修改=================================
bedHeading = {
    1: 1,
    2: 3
}
