# -*- coding: utf-8 -*-
# 请不要删掉上面这行！！！

# ICE_GAME 5v5 配置文档
# v1.1
# 新增 大厅等待人数
# ################################

# TODO IMPORTANT!!! Debug mode switch
# Plugin will not function while in debug mode!!!
debugMode = False

# 全局坐标设置
# 等候大厅的坐标
lobbyPos = (10, 4, -25)
# 玩家淘汰后的重生位置
spectatorPos = (34, 4, -24)
# 多少人后会开始倒计时？
startCountdown = 4
# 多少人后会缩短倒计时
enoughPlayers = 10
# 进攻方（CT）出生点
attackersSpawn = (28, 4, -25)
# 防守方（T）出生点
defendersSpawn = [(-29, 4, -8), (-32, 10, -41), (-19, 10, -8), (-4, 16, -49)]
# 炸弹爆点
bombSites = {
    0: [(-28, 4, -17), (-13, 4, -10)],
    1: [(-24, 10, -40), (-17, 10, -38)],
    2: [(-25, 10, -20), (-17, 10, -2)],
    3: [(-32, 16, -11), (-10, 16, -18)]
}
# 准备阶段路障
mapBlockers = [
    (15, 5, -23), (15, 5, -24), (15, 5, -25), (15, 5, -26),
    (6, 5, -24), (6, 5, -25),
    (4, 17, -23), (4, 17, -24), (4, 17, -25),
    (-42, 11, -25), (-42, 11, -24)
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

armorPresets = {
    1: 'none',
    2: 'iron',
    3: 'iron',
    4: 'iron',
    5: 'diamond'
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
    1: 45,
    2: 175,
    3: 9999
}


# =============================常量定义区域，请勿修改=================================
breakableBlocks = [
    'planks', 'concrete', 'wool', 'dark_oak_door'
]

explosionDamageSetting = {
    3: 999,
    5: 12,
    8: 5
}