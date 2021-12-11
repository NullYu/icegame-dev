# -*- coding: utf-8 -*-
# 请不要删掉上面这行！！！

# ICE_GAME 超级战墙（4队）配置文档
# v1.1
# ################################

# 全局坐标设置
# 等候大厅的坐标
lobbyPos = (0, 242, 0)
# 玩家淘汰后的重生位置
spectatorPos = (0, 100, 0)
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
    1: (79, 66, 0), #red team
    2: (0, 66, -79), #yellow team
    3: (-79, 66, 0), #blue team
    4: (0, 66, 79) #green team
}

# 墙的宽度
width = 5

# 准备时间最高可建造高度
buildHeight = 128
