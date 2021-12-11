# -*- coding: utf-8 -*-
# ICE_GAME Guns Daemon <gunsd>
# ICE_GAME枪械服务mod - 可与ICGO或吃鸡mod一同使用。
# 价目表 - https://www.notion.so/icegame/238839a9c0ae420da13e86c01f22b1b8?v=8a175efddda8426e8cfef6249032ecdb

# SUDOCLASSES
# isManual
manual = 0
auto = 1
bolt = 2
# isSilent, isScope, isHeavy, isShotgun, isMelee, isCharge, canZoom
silent, scope, heavy, shotgun, melee, charge, zoom = 'silent', 'canscope', 'heavy', 'shotgun', 'melee', 'charge', 'zoom'
# side
t = 'terrorist'
ct = 'police'
all = 'universal_use'

gunNames = [
    '<!INDEX ERR>',
    'USP', 'GLOCK18', 'CZ75',
    'DEAGLE', 'R8左轮', 'BK47',
    'N4B4', 'N4B4S', 'SG533',
    'GALIL', 'GAMAS', 'SSG',
    'AWP', 'LONGBOW',
    'P90', 'MAC10', 'MP9',
    'BISON', 'NEGEV', 'SPITFIRE',
    'EVA', 'NOVA', 'MAG',
    '<MELEE>', 'HORNET'
]

# gun attributes format:
# side, mode, magazine, recoil, normal/crit
# recoil: + = up/left - = down/right: 1/2...
# magazine: 1/2...
gunAttrs = {
    1: (ct, manual, '12/24', '1/1', '37/96', silent),
    2: (t, manual, '20/80', '3/2', '26/78'),
    3: (all, auto, '12/12', '3/-3', '35/90'),
    4: (all, manual, '7/35', '4/-1', '63/127'),
    5: (all, manual, '8/8', '5/-1', '96/255', charge),

    6: (t, auto, '30/90', '4/3', '35/101'),
    7: (ct, auto, '30/90', '4/1', '34/105'),
    8: (ct, auto, '25/75', '2/1', '33/104', silent),
    9: (t, auto, '30/90', '3/-2', '29/96', zoom),
    10: (t, auto, '35/90', '2/2', '27/91'),
    11: (ct, auto, '25/90', '3/2', '29/93'),

    12: (all, bolt, '10/90', '0/0', '88/210', scope),
    13: (all, bolt, '10/30', '0/0', '105/415', scope, heavy),
    14: (all, auto, '20/90', '3/2', '79/205', scope, heavy),

    15: (all, auto, '20/100', '1/2', '26/88'),
    16: (t, auto, '30/100', '2/2', '29/93'),
    17: (ct, auto, '30/120', '2/2', '28/92'),
    18: (all, auto, '64/120', '2/1', '27/90'),

    19: (all, auto, '150/300', '5/-3', '29/100', heavy),
    20: (all, auto, '100/200', '3/-2', '32/105', heavy),
    21: (all, auto, '7/32/9', '4/1', '12/36', shotgun),
    22: (all, manual, '8/32/10', '2/1', '9/35', shotgun, melee),
    23: (all, manual, '5/32/6', '2/1', '21/35', shotgun, melee),

    24: (all, manual, '0/0', '0/0', '200/400', melee),
    25: (all, manual, '1/0', '10/0', '149/255', melee)
}

gunItems = {
    1: ''
}

shotgunSpreadDef = {

}
