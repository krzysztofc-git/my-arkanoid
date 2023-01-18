import os, pygame

SIZE_SCREEN = WIDTH, HEIGHT = 720, 500

# colors
color_bg = (12, 20, 69) #background
color_platform = (25, 130, 196)
color_platform_outline = (0,0,0)
color_dark = (138, 201, 38) # block level 1
color_darker = (255, 202, 58) # block level 2
color_darkest = (255, 89, 94) # block level 3
color_ball = old_color_ball = (106, 76, 147)

#textures
path = os.path.join('images') #os.pardir, 
file_names = sorted(os.listdir(path))

for file_name in file_names:
    image_name = file_name[:-4].upper()
    globals()[image_name] = pygame.image.load(os.path.join(path, file_name))

# workaround of using dot notation in python dictionaries
class dotdict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

# Platform, named "Combined No-Gap"
PLATFORM_CNG = {
    'IMAGE': {
        'STAND': PLATFORM_CNG_0,
        #'LIST_L': [PLATFORM_CNG_L_0, PLATFORM_CNG_L_1, PLATFORM_CNG_L_2],
        'LIST_R': [PLATFORM_CNG_R_0, PLATFORM_CNG_R_1, PLATFORM_CNG_R_2],
    },
    'GAP': {'X': 6}, # length of flames that shouldn't collide with anything
    'SOUNDS': {'ENGINE': None, 'KNOCK': None},
    #'WIDTH': 128,
    'HEIGHT': 32
}
    
PLATFORM_CNG = dotdict(PLATFORM_CNG)
PLATFORM_CNG.IMAGE = dotdict(PLATFORM_CNG.IMAGE)
PLATFORM_CNG.IMAGE.LIST_L = [pygame.transform.flip(r, True, False) for r in PLATFORM_CNG.IMAGE.LIST_R]
PLATFORM_CNG.GAP = dotdict(PLATFORM_CNG.GAP)
PLATFORM_CNG.SOUNDS = dotdict(PLATFORM_CNG.SOUNDS)

# Platform, named "2"
PLATFORM_2 = {
    'IMAGE': {
        'STAND': PLATFORM_2_0,
        'LIST_R': [PLATFORM_2_R_0, PLATFORM_2_R_1, PLATFORM_2_R_2],
    },
    'GAP': {'X': 6}, # length of flames that shouldn't collide with anything
    'SOUNDS': {'ENGINE': None, 'KNOCK': None},
    #'WIDTH': 128,
    'HEIGHT': 32
}
    
PLATFORM_2 = dotdict(PLATFORM_2)
PLATFORM_2.IMAGE = dotdict(PLATFORM_2.IMAGE)
PLATFORM_2.IMAGE.LIST_L = [pygame.transform.flip(r, True, False) for r in PLATFORM_2.IMAGE.LIST_R]
PLATFORM_2.GAP = dotdict(PLATFORM_2.GAP)
PLATFORM_2.SOUNDS = dotdict(PLATFORM_2.SOUNDS)

BLOCK_CNG = {
    'IMAGE': {
        'LEVEL': [BLOCK_CNG_0, BLOCK_CNG_1, BLOCK_CNG_2]
    },
    'GAP': {'X': 0, 'Y': 0},
    'SOUNDS': {'CRACK': None, 'BREAK': None}
}
BLOCK_CNG = dotdict(BLOCK_CNG)
BLOCK_CNG.IMAGE = dotdict(BLOCK_CNG.IMAGE)
BLOCK_CNG.GAP = dotdict(BLOCK_CNG.GAP)
BLOCK_CNG.SOUNDS = dotdict(BLOCK_CNG.SOUNDS)

BALL_CNG = {
    'IMAGE': {
        'LEVEL': [BALL_CNG_0, BALL_CNG_1, BALL_CNG_2]
    },
    'RADIUS': 8
}

BALL_CNG = dotdict(BALL_CNG)
BALL_CNG.IMAGE = dotdict(BALL_CNG.IMAGE)
