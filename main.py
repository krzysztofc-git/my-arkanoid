# !!!
# Please DO NOT COPY the code. Read README.md file to learn more.

# Review only

from random import randint
import pygame
from pygame.locals import *
import resources as rs
import binary_cursors as bc
import ctypes, os, time
from collections import deque
from PIL import Image, ImageOps
import numpy as np
import sounds

# setting up basic components and display options
pygame.init()
screen = pygame.display.set_mode(rs.SIZE_SCREEN)
pygame.display.set_caption('My Arkanoid')
os.environ['SDL_VIDEO_CENTERED'] = '1'

# fixing DPI issues (when DPI scale is enabled in Windows - optional)
ctypes.windll.user32.SetProcessDPIAware()

# limiting game speed (clock) to fps (visible later in the game loop)
clock = pygame.time.Clock()
fps = 60

class Platform(pygame.sprite.Sprite):
    def __init__(self, platform_resource_default=rs.PLATFORM_CNG):
        super().__init__()
        self.p_r_d = platform_resource_default
        self.reset()

    # class method reset can be useful when there is need to restart the game
    def reset(self, platform_resource=0):
        # by default choosing self.p_r_d (if no arguments given or = 0)
        if platform_resource == 0:
            self.platform_resource = self.p_r_d

        width_from_image = self.platform_resource.IMAGE.STAND.get_width()
        height_from_image = self.platform_resource.IMAGE.STAND.get_height()

        # platform_height = platform_resource.IMAGE.STAND.get_height()
        self.width = self.platform_resource.WIDTH
        self.height = self.platform_resource.HEIGHT
        self.aspect_ratio = 1

        # following if statements are about keeping aspect ratio of the image
        # if width and/or height parameters are missing in a platform resource
        if self.width is None and self.height is not None:
            self.aspect_ratio = self.height / height_from_image
            self.width = int(width_from_image * self.aspect_ratio)
        if self.width is not None and self.height is None:
            self.aspect_ratio = self.width / width_from_image
            self.height = int(height_from_image * self.aspect_ratio)
        if self.width is None and self.height is None:
            self.width = width_from_image
            self.height = height_from_image

        self.image = self.platform_resource.IMAGE.STAND

        # making some parts of platform not touchable (e.g. flames)
        self.gap_x = self.platform_resource.GAP.X * self.aspect_ratio

        # defining rect from a 'STAND' platform texture
        self.rect = self.image.get_rect()

        # setting default position of platform (to center)
        self.rect.bottom = rs.HEIGHT - self.height - 5
        self.rect.x = rs.WIDTH // 2 - self.width // 2

        # (*) updating width and height of the rect object to scaled one
        self.rect.width, self.rect.height = self.width, self.height

        # physics values of the platform
        self.movement_x = 0

        # reading current time once, in order to follow animation frames later (FPS)
        self.start_frame = time.time()

    def draw(self, space):
        # (*) scaling 'pixelart' textures is not scaling their 'hitbox' by default
        self.image_scaled = pygame.transform.scale(self.image, (self.width, self.height))
        space.blit(self.image_scaled, self.rect)
        # space.fill((0,0,0), self.rect)

    def fly_right(self):
        self.movement_x = 10

    def fly_left(self):
        self.movement_x = -10

    def fly_stop(self):
        self.movement_x = 0

    def update(self):
        # moving horizontally
        self.rect.x += self.movement_x

        # animation of engine moving
        if self.movement_x > 0:
            self._move(self.platform_resource.IMAGE.LIST_R)
        if self.movement_x < 0:
            self._move(self.platform_resource.IMAGE.LIST_L)

    def get_keys(self, event):
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_RIGHT]:
            self.fly_right()
        if pressed[pygame.K_LEFT]:
            self.fly_left()
        if event.type == pygame.KEYUP:
            if not pressed[pygame.K_RIGHT] and not pressed[pygame.K_LEFT]:
                self.fly_stop()
                self.image = self.platform_resource.IMAGE.STAND

        # not letting the platform to go outside borders of screen
        self.is_at_left_corner_of_screen = self.rect.left < 0 - self.gap_x
        self.is_at_right_corner_of_screen = self.rect.right > rs.WIDTH + self.gap_x

        if self.is_at_left_corner_of_screen:
            self.image = self.platform_resource.IMAGE.STAND
            self.rect.left = 0 - self.gap_x
        if self.is_at_right_corner_of_screen:
            self.image = self.platform_resource.IMAGE.STAND
            self.rect.right = rs.WIDTH + self.gap_x

    def _move(self, image_list):
        # reducing FPS of the platform animations
        num_images = len(image_list)
        inner_fps = 4
        current_image = int((time.time() - self.start_frame) * inner_fps % num_images)
        self.image = image_list[current_image]


class Block(pygame.sprite.Sprite):
    def __init__(self, block_resource, pos_x, pos_y, level, width=0, height=0):
        super().__init__()
        self.image_list = block_resource.IMAGE.LEVEL
        if width != 0 and height != 0:
            self.width = width
            self.height = height
        else:
            self.width = self.image_list[0].get_width()
            self.height = self.image_list[0].get_height()
            # print("Block: ", self.width, self.height)
        self.image = pygame.surface.Surface([self.width, self.height])
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = pos_x, pos_y
        self.level = level

    def draw(self, space):
        # troubleshooting if block value given is wrong
        if self.level >= len(self.image_list):
            raise ValueError("Block level too high ->", self.level)
        elif self.level < 0:
            raise ValueError("Block level too low ->", self.level)

        # specific texture is selected based on block's level
        # widths are simpler in this class so additional rect scaling may not be required
        self.image_scaled = pygame.transform.scale(self.image_list[self.level], (self.width, self.height))

        space.blit(self.image_scaled, self.rect)


class Ball(pygame.sprite.Sprite):
    def __init__(self, ball_resource_default=rs.BALL_CNG, pos_x=0, pos_y=0, level=0, platform_default=None,
                 level_class=0):
        super().__init__()
        self.b_r_d = ball_resource_default
        self.p_d = platform_default
        self.reset(self.b_r_d, pos_x, pos_y, level, self.p_d, level_class)

    def reset(self, ball_resource=0, pos_x=0, pos_y=0, level=0, platform=0, level_class=0):
        # by default choosing self.b_r_d (if no arguments given or = 0)
        if ball_resource == 0:
            self.ball_resource = self.b_r_d
        else:
            self.ball_resource = ball_resource

        if platform == 0:
            self.platform = self.p_d
        else:
            self.platform = platform

        self.image_list = self.ball_resource.IMAGE.LEVEL
        self.width = self.ball_resource.RADIUS * 2
        self.height = self.ball_resource.RADIUS * 2
        self.image = self.image_list[0]
        self.rect = self.image.get_rect()

        # (*) updating width and height of the rect object to scaled one
        self.rect.width, self.rect.height = self.width, self.height

        # if other platform is passed as a parameter, ball is centered to it
        if platform is None:
            self.rect.x, self.rect.y = pos_x, pos_y
        else:
            self.rect.midbottom = platform.rect.midtop
        self.level = level

        # physics values of the platform
        self.movement_x = 2
        self.movement_y = -2

        # reading current time once, in order to follow animation frames later (FPS)
        self.start_frame = time.time()
        if level_class != 0:
            level_class.add_ball(self)

        self.count_shift = randint(0, 5)

    def draw(self, space):
        # (*) like with platform, rect is being scaled to a scaled image
        self.image_scaled = pygame.transform.scale(self.image, (self.width, self.height))
        space.blit(self.image_scaled, self.rect)

    def update(self):
        # moving in 2D
        self.rect.x += self.movement_x
        self.rect.y += self.movement_y

        # animation of ball moving, as changing levels
        if self.movement_x or self.movement_y:
            self._move(self.ball_resource.IMAGE.LEVEL)

    def _move(self, image_list):
        # reducing FPS of the ball animations
        num_images = len(image_list)
        inner_fps = 4
        current_image = int((time.time() - self.start_frame) * inner_fps % num_images)
        # to change starting frame of animation
        unshifted_numbers = list(range(0, num_images))
        shifted_numbers = deque(unshifted_numbers)
        shifted_numbers.rotate(self.count_shift)
        shifted_numbers = list(shifted_numbers)
        self.image = image_list[shifted_numbers[current_image]]

        # checking collisions with screen borders
        # hits wall -> mirror movement x
        if self.rect.left < 0 or self.rect.right > rs.WIDTH:
            self.movement_x *= -1
            sounds.sound_play('hit_wall')

        # hits ceiling -> mirrors movement y
        if self.rect.top < 0:
            self.movement_y *= -1
            sounds.sound_play('hit_wall')

        # hits bottom -> disappears (dies)
        if self.rect.bottom > rs.HEIGHT:
            self.kill()
            # object would still exist and move after .kill()
            self.movement_x = 0
            self.movement_y = 0
            self.rect.x, self.rect.y = 0, 0


class Level:
    def __init__(self, platform, ball):
        self.platform = platform
        self.set_of_blocks = pygame.sprite.Group()
        self.set_of_blocks.add(platform)
        self.set_of_balls = pygame.sprite.Group()

    def update(self):
        # balls collisions with blocks and platform
        # collision sensitivity / thresh - should adjust if ball is getting through a block
        collision_sensitivity = 5
        for selected_ball in self.set_of_balls:
            collided_blocks = pygame.sprite.spritecollide(selected_ball, self.set_of_blocks, False)

            if collided_blocks:
                for selected_block in collided_blocks:
                    gap_x = 0
                    gap_y = 0  # may be useful when adding features
                    # when block has hitbox gaps (is a Platform)
                    if type(selected_block) == Platform:
                        print("Found platform in blocks,",selected_ball.rect.right)
                        gap_x = selected_block.gap_x
                        print( gap_x - selected_block.rect.left)
                        sounds.sound_play('hit_platform')

                    # o| |  collides from left of block
                    if abs(selected_ball.rect.right - gap_x - selected_block.rect.left) < collision_sensitivity and selected_ball.movement_x > 0:
                        selected_ball.movement_x *= -1
                    #  | |o collides from right of block
                    if abs(selected_ball.rect.left + gap_x - selected_block.rect.right) < collision_sensitivity and selected_ball.movement_x < 0:
                        selected_ball.movement_x *= -1
                    #  _o_  collides from top of block
                    if abs(selected_ball.rect.bottom + gap_y - selected_block.rect.top) < collision_sensitivity and selected_ball.movement_y > 0:
                        selected_ball.movement_y *= -1
                    #  `o`  collides from bottom of block
                    if abs(selected_ball.rect.top - gap_y - selected_block.rect.bottom) < collision_sensitivity and selected_ball.movement_y < 0:
                        selected_ball.movement_y *= -1

                    # decision about removing a block
                    if type(selected_block) != Platform:
                        print(selected_block.level)
                        if selected_block.level > 0:
                            selected_block.level -= 1
                            sounds.sound_play('hit_block')
                        else:
                            selected_block.kill()
                            sounds.sound_play('destroy_block')
        # updates of group elements
        for ball in self.set_of_balls:
            ball.update()
        for block in self.set_of_blocks:
            if getattr(block, "update", None):
                block.update()

    def draw(self, space):
        for block in self.set_of_blocks:
            block.draw(space)
        for ball in self.set_of_balls:
            ball.draw(space)

    def add_ball(self, ball):
        self.set_of_balls.add(ball)

    def is_game_over(self):
        return not len(self.set_of_balls)

    def is_won(self):
        return not (len(self.set_of_blocks) - 1)  # -1 because platform is there too


class Level_1(Level):
    def __init__(self, platform, ball):
        super().__init__(platform, ball)
        self.rows = 3
        self.cols = 10
        self.width_block_predicted = rs.WIDTH // self.cols
        self.height_block_predicted = rs.BLOCK_CNG.IMAGE.LEVEL[0].get_height()
        self._create_blocks()


    def _create_blocks(self):
        for row in range(self.rows):
            for col in range(self.cols):
                block_x = col * self.width_block_predicted
                block_y = row * self.height_block_predicted
                # setting level of the block based on its row number
                if row == 0:
                    level = 2
                elif row == 1:
                    level = 1
                else:
                    level = 0
                # adding block to blocks list with its features
                block = Block(rs.BLOCK_CNG, block_x, block_y, level, self.width_block_predicted,
                              self.height_block_predicted)
                self.set_of_blocks.add(block)

class Level_custom(Level):
    def __init__(self, platform, ball, image_url):
        super().__init__(platform, ball)
        
        # self.add_ball(ball)
        # self._create_bonuses()

        #import png pixelmap of rgb of dimensions 10x15
        i = Image.open(image_url)
        i = i.rotate(90, expand=True)
        i = ImageOps.flip(i)
        pixels = i.load()  # this is not a list, nor is it list()'able
        
        width, height = i.size
        print(width,height)

        self.rows = width
        self.cols = height
        self.width_block_predicted = rs.WIDTH // self.cols
        self.height_block_predicted = rs.BLOCK_CNG.IMAGE.LEVEL[0].get_height()

        self.all_pixels = []
        for x in range(width):
            for y in range(height):
                cpixel = pixels[x, y]
                self.all_pixels.append(cpixel)

        #print(self.all_pixels)
        self.all_pixels = np.array(self.all_pixels)
        #print(self.all_pixels)
        self.all_pixels = self.all_pixels.reshape(self.rows,self.cols,4)
        #print(self.all_pixels)
        self.all_pixels = self.all_pixels.tolist()

        self._create_blocks()
    

    def _create_blocks(self):
        #print(self.all_pixels)
        
        count_row = 0
        for row in range(self.rows):
            count_col = 0
            for col in range(self.cols):
                block_x = col * self.width_block_predicted
                block_y = row * self.height_block_predicted

                # adding block to blocks list with its features
                #if red
                select_pixel = self.all_pixels[count_row][count_col]
                #print(select_pixel, end=' ')
                # red color -> level 2
                if select_pixel == [255,0,0,255]:
                    block = Block(rs.BLOCK_CNG, block_x, block_y, 2, self.width_block_predicted, self.height_block_predicted)
                    self.set_of_blocks.add(block)
                    print('x', end=' ')
                # green color -> level 0
                elif select_pixel == [0,255,0,255]:
                    block = Block(rs.BLOCK_CNG, block_x, block_y, 0, self.width_block_predicted, self.height_block_predicted)
                    self.set_of_blocks.add(block)
                    print('y', end=' ')
                # blue color -> level 1
                elif select_pixel == [0, 0, 255, 255]:
                    block = Block(rs.BLOCK_CNG, block_x, block_y, 1, self.width_block_predicted, self.height_block_predicted)
                    self.set_of_blocks.add(block)
                    print('z', end=' ')
                else:
                    print(' ', end=' ')
                count_col += 1
            count_row += 1
            print('')

class Level_2(Level_custom):
    def __init__(self, platform, ball):
        super().__init__(platform, ball, "level2.png")


class Level_3(Level_custom):
    def __init__(self, platform, ball):
        super().__init__(platform, ball, "level3.png")


# creating instance of objects
player = Platform()
ball = Ball(platform_default=player)

# menu
lot_of_balls_mode = True
dot_cursor = True
level_select = 0
game_started = False
skin_select = 0

levels = [Level_1, Level_2, Level_3]
levels_desc = ["Level 1: flat-land", "Level 2: noodles", "Level 3: video game"]
#print("Available levels: ")

# for i in range(len(levels)):
#     print(i+1,"-",levels[i])
# print(len(levels)+1,"- select custom...")
# #level_select = int(input("Select your level: ")) - 1
# if level_select == len(levels):
#     my_url = input("Input file name with '.png' located in game directory: ")
#     current_level = Level_custom(player, ball, my_url)
# else:
#     current_level = levels[level_select](player, ball)


# partly solving not-detecting-KEYUP-event bug when moving mouse
# instead of mouse, keyboard should be used to control the game
pygame.event.set_blocked(pygame.MOUSEMOTION)

# less distracting mouse cursor
if dot_cursor:
    cursor = pygame.cursors.compile(bc.dot)
    pygame.mouse.set_cursor((8,8), (0, 0), *cursor)



#function for outputting text
def draw_text(text, text_col, x, y, size = 25, font_family = 'Arial'):
    font = pygame.font.SysFont(font_family, size)
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))



run = True
# game loop
while run:
    clock.tick(fps)

    screen.fill(rs.color_bg)

    # closing the game by window 'X' button
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        # Debug keys - optional
        if event.type == pygame.KEYDOWN:
            pressed = pygame.key.get_pressed()
            # b -> reset the ball
            if pressed[pygame.K_b]:
                ball.reset(platform=player, level_class=current_level)
            # s -> stop / start the ball
            if pressed[pygame.K_p]:
                if ball.movement_x != 0 and ball.movement_y != 0:
                    backup_movement_x = ball.movement_x
                    backup_movement_y = ball.movement_y
                    ball.movement_x = 0
                    ball.movement_y = 0
                    #game_started = False
                else:
                    ball.movement_x = backup_movement_x
                    ball.movement_y = backup_movement_y
                    #game_started = True
            # i -> prints information about the ball
            if pressed[pygame.K_i]:
                print(ball.rect, ball)
                print("game over:", current_level.is_game_over(), ", won:", current_level.is_won())
            if pressed[pygame.K_s]:
                game_started = True
                current_level = levels[level_select](player, ball)
                sounds.sound_play('start')

                # resets a ball so the ball is in the level balls
                # makes current_level accessible to ball and vice versa
                # (adds the starter ball to current_level.set_of_balls)
                ball.reset(platform=player, level_class=current_level)

                # more balls
                if lot_of_balls_mode:
                    for i in range(10):
                        other_ball = Ball(pos_x=randint(player.rect.x, player.rect.x + player.rect.width),
                                        pos_y=randint(player.rect.y - 200, player.rect.y - 100))
                        other_ball.movement_x *= -1 if randint(0, 1) else 1
                        other_ball.movement_y *= -1 if randint(0, 1) else 1
                        current_level.add_ball(other_ball)
            if pressed[pygame.K_l]:
                if level_select < len(levels) - 1:
                    level_select += 1
                else:
                    level_select = 0
                current_level = levels[level_select](player, ball)
            if pressed[pygame.K_g]:
                lot_of_balls_mode = not lot_of_balls_mode
            if pressed[pygame.K_h]:
                if not skin_select:
                    player = Platform(rs.PLATFORM_2)
                else:
                    player = Platform()
                skin_select = not skin_select

    player.get_keys(event)

    if game_started:
        if not current_level.is_game_over() and not current_level.is_won():
            # player.update()
            # ball.update()
            current_level.update()

            # player.draw(screen) # commented because Platform is in Level.set_of_blocks
            # ball.draw(screen)
            current_level.draw(screen)  # it draws player (Platform) too

            # for b in current_level.set_of_blocks:
            #     if b.rect.x == 360 and b.rect.y == 64 and b.level == 0:
            #         b.kill()
        elif current_level.is_won():
            #game won screen
            draw_text('Game won', rs.color_ball, 100, rs.HEIGHT // 2 + 100)
            sounds.sound_play('game_won')
            pygame.display.update()
            time.sleep(2)
            run = False
        elif current_level.is_game_over():
            #game over screen
            draw_text('Game over', rs.color_ball, 100, rs.HEIGHT // 2 + 100)
            sounds.sound_play('game_over')
            pygame.display.update()
            time.sleep(2)
            run = False
    else:
        #menu screen
        draw_text('Press S to start', rs.color_ball, 100, rs.HEIGHT // 2 + 100)
        draw_text('Press L to change level (selected: {})'.format(levels_desc[level_select]), rs.color_ball, 100, rs.HEIGHT // 2 + 150, 20)
        draw_text('Press G to enable bonus balls (selected: {})'.format(lot_of_balls_mode), rs.color_ball, 100, rs.HEIGHT // 2 + 170, 20)
        draw_text('Press H to change platform skin (selected: {})'.format(skin_select + 1), rs.color_ball, 100, rs.HEIGHT // 2 + 190, 20)

    pygame.display.update()

pygame.quit()
