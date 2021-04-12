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

screen_width = 720
screen_height = 480

blank_picture = Image.new('RGBA', size=(screen_width, screen_height), color=(0,0,0,255))

image_no_signal = blank_picture.copy()
image_no_signal.paste(Image.open("no_signal.bmp").convert("RGBA"))


class CrtNoiseLine: 
    
    noised_line = None    
    
    def __init__(self):
        self.line_width = screen_width
        self.line_height = random.randrange(1,int(screen_height/15))
        self.noised_line = self.white_noise_pygame_image(line_width, line_height)
        self.line_increment = random.randrange(10,20)
        self.is_living = False
            
    def display_line(self):       
        #TODO may remove the comented line, it's how to do a simple line without noise
        #img = Image.new('RGBA', size=(line_width, line_height), color=(127,127,127,127))
        #raw_str  = img.tobytes("raw", 'RGBA')
        #pygame_image = pygame.image.fromstring(raw_str, img.size, 'RGBA')   
        #pygame_image = self.white_noise_pygame_image(line_width, line_height) white noise line
        if self.is_living == True:
            self.screen.blit(self.noised_line , (0, self.offset_line))        
            self.offset_line = (self.offset_line + line_increment)%screen_height
        
        if self.offset_line == 0:
            self.is_living = False
        
    def white_noise_pygame_image(self, width, height):
        pil_map = Image.new("RGBA", (width, height), 255)
        random_grid = map(lambda x: (
                ((int(random.random() * 256),)*3) + (127,)
            ), [0] * width * height)
        pil_map.putdata(list(random_grid))        
        noise_str = pil_map.tobytes("raw", 'RGBA')
        noise_image = pygame.image.fromstring(noise_str, (width,height), 'RGBA')
        return noise_image
        
    def revive(self):
        self.is_living = True


class SpotiCrtFrameBuffer :
    screen = None
    PIL_spotify_image = image_no_signal
    pygame_spotify_image = None
    track = None
    glitch_images = []
    offset_line = 0
    
    def __init__(self):

        self.track_picture_updated = False
        self.track_updated = False
        self.glitcher = ImageGlitcher()
        
        disp_no = os.getenv("DISPLAY")
        if disp_no:
            print("I'm running under X display = {0}".format(disp_no))

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
        
        self.pygame_spotify_image = self.PIL_to_pygame(self.PIL_spotify_image)
        
        self.noised_lines = []
        for i in range(0,5):
            self.noised_lines.append(CrtNoiseLine())
 
    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."
    
    def get_spotify_image(self, spotify_reader):
        new_width = screen_height 
        
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
                    self.PIL_spotify_image = blank_picture.copy()
                    self.PIL_spotify_image.paste(image_PIL.resize((new_width, new_height), Image.ANTIALIAS))
                    self.pygame_spotify_image = self.PIL_to_pygame(self.PIL_spotify_image)
                    self.compute_glitch_images(random.randrange(10,50))
                    self.track_picture_updated = True   
            else:
                self.PIL_spotify_image = image_no_signal
                self.pygame_spotify_image = self.PIL_to_pygame(self.PIL_spotify_image)
                self.compute_glitch_images(random.randrange(10,50))
        self.track = new_track
            
    def get_spotify_image_timer(self, spotify_reader, period):
        self.get_spotify_image(spotify_reader)
        t = Timer(period, self.get_spotify_image_timer, args=(spotify_reader,period))
        t.start()
            
        
    def display_spotify_image(self):
        self.screen.blit(self.pygame_spotify_image, (0, 0))
        
    def compute_glitch_images(self, number):
        print("compute glitch")
        self.glitch_images = []
        glitch_factor = random.random()*2+1
        for i in range(0,number):
            glitch_img = self.glitcher.glitch_image(self.PIL_spotify_image , glitch_factor, color_offset=True, scan_lines=False).convert("RGBA")
            raw_str  = glitch_img.tobytes("raw", 'RGBA')
            self.glitch_images.append(pygame.image.fromstring(raw_str, glitch_img.size, 'RGBA').convert())

    def display_glitch_images(self):
        for glitch_image in self.glitch_images:
            self.screen.blit(glitch_image, (0, 0))  
            self.display_lines()
            pygame.display.flip()
    
    def display_lines(self):
        for line in self.noised_lines:
            if line.is_living == False:
                if random.random()*10 >9:
                    line.revive()
            line.display_line()
            
    #TODO may be removed since now in CrtNoiseLine class
    def white_noise_pygame_image(self, width, height):
        pil_map = Image.new("RGBA", (width, height), 255)
        random_grid = map(lambda x: (
                ((int(random.random() * 256),)*3) + (127,)
            ), [0] * width * height)
        pil_map.putdata(list(random_grid))        
        noise_str = pil_map.tobytes("raw", 'RGBA')
        noise_image = pygame.image.fromstring(noise_str, (width,height), 'RGBA')
        return noise_image
        
    def PIL_to_pygame(self, PIL_image):
        raw_str  = PIL_image.tobytes("raw", 'RGBA')
        return pygame.image.fromstring(raw_str, PIL_image.size, 'RGBA').convert()
            
 
scope = SpotiCrtFrameBuffer()
spotify_reader = SpotifyReader()
scope.get_spotify_image_timer(spotify_reader, 5)
scope.display_spotify_image()
pygame.display.flip()

while(True):
    scope.compute_glitch_images(random.randrange(10,50))
    scope.display_glitch_images()
    sleep(0.2)
    loop_max = random.randrange(2,10)*60
    for i in range(0,loop_max):       
        scope.display_spotify_image()
        scope.display_lines()
        pygame.display.update()
        if scope.track_picture_updated == True:
            scope.track_picture_updated  = False  
            scope.display_glitch_images()          
            scope.display_spotify_image()
            pygame.display.flip()
            print("Break")
            break