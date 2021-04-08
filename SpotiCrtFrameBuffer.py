import os
import pygame
from time import sleep
import random
import SpotiCrtDisplay
from urllib.request import urlopen
import io 
from PIL import Image
from glitch_this import ImageGlitcher
import random

new_width = 480

glitcher = ImageGlitcher()


class pyscope :
    screen = None
    spotify_image = None
    
    def __init__(self):
        "Ininitializes a new pygame screen using the framebuffer"
        # Based on "Python GUI in Linux frame buffer"
        # http://www.karoltomala.com/blog/?p=679
        
        disp_no = os.getenv("DISPLAY")
        if disp_no:
            print("I'm running under X display = {0}".format(disp_no))
        
        # Check which frame buffer drivers are available
        # Start with fbcon since directfb hangs with composite output
        drivers =  ['directfb']#directfb, 'fbcon', 'svgalib', 'windib', 'x11', 'dga', 'ggi', 'vgl', 'aalib']
        found = False
        for driver in drivers:
            # Make sure that SDL_VIDEODRIVER is set
            try:
                pygame.display.init()
            except:
                pass
            
            os.putenv('SDL_VIDEODRIVER', driver)
            try:
                pygame.display.init()
            except pygame.error:
                print('Driver: {0} failed.'.format(driver))
                continue
            found = True
            break
    
        if not found:
            raise Exception('No suitable video driver found!')
        
        size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        print("Framebuffer size: %d x %d" % (size[0], size[1]))
        self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
        # Clear the screen to start
        self.screen.fill((0, 0, 0))        
        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.display.update()
 
    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."
    
    def get_spotify_image(self):
        image_uri = SpotiCrtDisplay.get_current_track_info().album_uri
        image_str = urlopen(image_uri).read()
        image_file = io.BytesIO(image_str)        
        image_PIL = Image.open(image_file).convert("RGBA")
        new_height = int(image_PIL.height * (new_width/image_PIL.width))
        self.spotify_image = image_PIL.resize((new_width, new_height), Image.ANTIALIAS)
        
    def display_spotify_image(self):
        raw_str  = self.spotify_image.tobytes("raw", 'RGBA')
        pygame_image = pygame.image.fromstring(raw_str, self.spotify_image.size, 'RGBA')
    
        self.screen.blit(pygame_image, (0, 0))
        pygame.display.update()

    def display_glitch_images(self, number):
        glitch_images = []
        for i in range(0,number):
            glitch_img = glitcher.glitch_image(self.spotify_image , 6, color_offset=True, scan_lines=False).convert("RGBA")#.convert('1')
            raw_str  = glitch_img.tobytes("raw", 'RGBA')
            glitch_images.append(pygame.image.fromstring(raw_str, glitch_img.size, 'RGBA').convert())
        
        for i in range(0,number):
            self.screen.blit(glitch_images[i], (0, 0))
            pygame.display.update()
 
# Create an instance of the PyScope class
scope = pyscope()
scope.get_spotify_image()
scope.display_spotify_image()
for i in range(0,10):
    scope.display_glitch_images(random.randrange(15,50))
    sleep(0.2)
    scope.display_spotify_image()
    sleep(random.randrange(5,30))
sleep(1000)