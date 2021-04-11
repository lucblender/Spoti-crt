import os
import pygame
from time import sleep
import random
from SpotiCrtDisplay import *
from urllib.request import urlopen
import io 
from PIL import Image
from glitch_this import ImageGlitcher
import random
from threading import Timer

new_width = 480

glitcher = ImageGlitcher()

blank_picture = Image.new('RGBA', size=(720, 480), color=(0,0,0,255))

image_no_signal = blank_picture.copy()
image_no_signal.paste(Image.open("no_signal.bmp").convert("RGBA"))



class SpotiCrtFrameBuffer :
    screen = None
    spotify_image = image_no_signal
    track = None
    glitch_images = []
    offset_line = 0
    
    def __init__(self):
        "Ininitializes a new pygame screen using the framebuffer"
        # Based on "Python GUI in Linux frame buffer"
        # http://www.karoltomala.com/blog/?p=679
        
        self.track_picture_updated = False
        self.track_updated = False
        
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
    
    def get_spotify_image(self, spotify_reader):
        new_track = spotify_reader.get_current_track_info()
        
        if new_track != self.track:    
            self.track_updated = True
            if new_track  != None:
                old_album_uri = self.track.album_uri if self.track != None else ""
                if old_album_uri != new_track.album_uri:           
                    print("track_picture_updated")
                    image_uri = new_track.album_uri
                    image_str = urlopen(image_uri).read()
                    image_file = io.BytesIO(image_str)        
                    image_PIL = Image.open(image_file).convert("RGBA")
                    image_PIL.save("toto.bmp")
                    new_height = int(image_PIL.height * (new_width/image_PIL.width))
                    self.spotify_image = blank_picture.copy()
                    self.spotify_image.paste(image_PIL.resize((new_width, new_height), Image.ANTIALIAS))
                    self.compute_glitch_images(random.randrange(10,50))
                    self.track_picture_updated = True   
            else:
                self.spotify_image = image_no_signal
                self.compute_glitch_images(random.randrange(10,50))
        self.track = new_track
            
    def get_spotify_image_timer(self, spotify_reader, period):
        self.get_spotify_image(spotify_reader)
        t = Timer(period, self.get_spotify_image_timer, args=(spotify_reader,period))
        t.start()
            
        
    def display_spotify_image(self):
        print("display")
        raw_str  = self.spotify_image.tobytes("raw", 'RGBA')
        pygame_image = pygame.image.fromstring(raw_str, self.spotify_image.size, 'RGBA')
        self.screen.fill((0,0,0))
        self.screen.blit(pygame_image, (0, 0))
        #self.screen.blit(self.white_noise_pygame_image(720,480), (0,0))
        pygame.display.flip()
        
    def compute_glitch_images(self, number):
        print("compute glitch")
        self.glitch_images = []
        for i in range(0,number):
            glitch_img = glitcher.glitch_image(self.spotify_image , 5, color_offset=True, scan_lines=False).convert("RGBA")#.convert('1')
            raw_str  = glitch_img.tobytes("raw", 'RGBA')
            self.glitch_images.append(pygame.image.fromstring(raw_str, glitch_img.size, 'RGBA').convert())

    def display_glitch_images(self):
        for glitch_image in self.glitch_images:
            self.screen.blit(glitch_image, (0, 0))                        
            pygame.display.flip()
            
    def display_line(self):
        line_width = pygame.display.Info().current_w
        line_height = int(pygame.display.Info().current_h/15)
        img = Image.new('RGBA', size=(line_width, line_height), color=(50,50,50,127))
        raw_str  = img.tobytes("raw", 'RGBA')
        pygame_image = pygame.image.fromstring(raw_str, img.size, 'RGBA')   
        self.screen.blit(pygame_image, (0, 0))
        pygame.display.flip()    
    
    def display_line(self):
        line_width = pygame.display.Info().current_w
        line_height = int(pygame.display.Info().current_h/15)
        img = Image.new('RGBA', size=(line_width, line_height), color=(50,50,50,127))
        raw_str  = img.tobytes("raw", 'RGBA')
        pygame_image = pygame.image.fromstring(raw_str, img.size, 'RGBA')   
        #pygame_image = self.white_noise_pygame_image(line_width, line_height) white noise line
        self.screen.blit(pygame_image, (0, self.offset_line))
        pygame.display.flip()
        self.offset_line = (self.offset_line + 1)%480
        
    def white_noise_pygame_image(self, width, height):
        pil_map = Image.new("RGBA", (width, height), 255)
        random_grid = map(lambda x: (
                ((int(random.random() * 256),)*3) + (20,)
            ), [0] * width * height)
        pil_map.putdata(list(random_grid))        
        noise_str = pil_map.tobytes("raw", 'RGBA')
        noise_image = pygame.image.fromstring(noise_str, (width,height), 'RGBA')
        return noise_image
            
 
scope = SpotiCrtFrameBuffer()
spotify_reader = SpotifyReader()
scope.get_spotify_image_timer(spotify_reader, 5)
scope.display_spotify_image()
while(True):
    scope.compute_glitch_images(random.randrange(10,50))
    scope.display_glitch_images()
    sleep(0.2)
    scope.display_spotify_image()
    for i in range(0,random.randrange(2,10)):
        sleep(1)
        if scope.track_picture_updated == True:
            scope.track_picture_updated  = False  
            scope.display_glitch_images()          
            scope.display_spotify_image()
            print("Break")
            break