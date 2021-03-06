# -*- coding: utf-8 -*-
# 请不要删掉上面这行！！！

# ICE_GAME 超级战墙（4队）配置文档
# v1.1
# ################################

# 全局坐标设置
# 等候大厅的坐标
lobbyPos = (-194, 220, -173)
lobbyHeightLimit = 213
# 玩家淘汰后的重生位置
spectatorPos = (-194, 120, -173)
# 多少人后会开始倒计时？
startCountdown = 2

# 队伍设置
# 使用数字index，1234分别为红黄蓝绿

# 设置队名（将在各种信息中显示）
teamNames = {
    1: '§c§l红队§r',
    2: '§e§l黄队§r',
    3: '§b§l蓝队§r',
    4: '§a§l绿队§r'
}

# 队伍简称（出现在玩家头顶)
teamPrefix = {
    1: '§c§lR§r',
    2: '§e§lY§r',
    3: '§b§lB§r',
    4: '§a§lG§r'
}

# 总队伍数量
teamsCount = 4

# 队伍出生点
pos = {
    1: (-868, 73, -210), #red team
    2: (-868, 73, -136), #yellow team
    3: (-721, 73, -136), #blue team
    4: (-721, 73, -210) #green team
}

# 目标点坐标
containerPos = {
    1: (-821, 94, -214), #red team
    2: (-821, 94, -132), #yellow team
    3: (-767, 94, -132), #blue team
    4: (-767, 94, -214) #green team
}

# 墙壁坐标
wallPos = [
    ((-724, 98, -164), (-785, 74, -164)),
    ((-785, 98, -103), (-785, 74, -164)),
    ((-803, 98, -103), (-803, 74, -164)),
    ((-864, 98, -164), (-803, 74, -164)),
    ((-864, 98, -182), (-803, 74, -182)),
    ((-803, 98, -243), (-803, 74, -182)),
    ((-785, 98, -243), (-785, 74, -182)),
    ((-724, 98, -182), (-785, 74, -182))
]

# 墙的宽度
width = 5

# 准备时间最高可建造高度
buildHeight = 97
maxBuildHeight = 180

# 准备阶段倒计时
prepPhaseDuration = 30
