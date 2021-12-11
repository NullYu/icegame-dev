# combined data
# format:
# itemName:(price, count)

# blocks (panel1)
blocks = {
    'wool': (20, 16),
    'minecraft:sandstone': (80, 16),
    'minecraft:planks': (160, 12),
    'minecraft:netherbrick': (2000, 12),
    'minecraft:obsidian': (4000, 4),
    'minecraft:ladder': (120, 4),
    'minecraft:web': (80, 2)
}
# tools (panel2)
tools = {
    'minecraft:stone_pickaxe': (280, 1),
    'minecraft:iron_pickaxe': (860, 1),
    'minecraft:diamond_pickaxe': (2000, 1),
    'minecraft:stone_axe': (480, 1),
    'minecraft:iron_axe': (1080, 1),
    'minecraft:diamond_axe': (2500, 1),
    'minecraft:shears': (160, 1)
}
# weapons (panel3)
weapons = {
    'minecraft:wooden_sword': (5, 1),
    'minecraft:stone_sword': (120, 1),
    'minecraft:iron_sword': (800, 1),
    'minecraft:diamond_sword': (2500, 1),
    'minecraft:bow': (1600, 1, []),  # durIII
    'minecraft:bow1': (2400, 1, [(20, 2)]),  # durIII+punchII
    'minecraft:bow11': (3200, 1, [(20, 1), (21, 1)]),  # durIII+punch+flame
    'minecraft:bow111': (2000, 1, [(21, 1)]),  # durIII+flame
    'minecraft:bow1111': (4000, 1, [(22, 1)]),  # durIII+inf
    'minecraft:arrow': (400, 4)
}
# armor (panel4)
armor = {
    'chain_half': (480, 1),
    'iron_half': (880, 1),
    'diamond_half': (3000, 1),
    'chain': (920, 1),
    'iron': (2000, 1),
    'diamond': (8000, 1)
}
# misc (panel5)
misc = {
    'minecraft:snowball': (80, 8),
    'minecraft:tnt': (320, 1),
    'minecraft:pumpkin': (1000, 1),
    'minecraft:slime_ball': (4000, 1),
    'minecraft:ender_pearl': (4000, 1),
    'minecraft:golden_apple': (300, 1)
}