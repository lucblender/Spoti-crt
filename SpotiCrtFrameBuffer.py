import os
import pygame
from time import sleep
import random
from SpotiApiConnector import *
from urllib.request import urlopen
import io 
from PIL import Image, ImageDraw, ImageFont
from glitch_this import ImageGlitcher
import random
import threading
import signal
import sys

screen_width = 720
screen_height = 480

pos_image = (42,22)

blank_picture = Image.open('background.bmp').convert("RGBA")
play_picture = Image.open('play.bmp').convert("RGBA")
pause_picture = Image.open('pause.bmp').convert("RGBA")

image_no_signal = blank_picture.copy()
image_no_signal.paste(Image.open("no_signal.bmp").convert("RGBA"), pos_image)


class CrtNoiseLine: 
    
    noised_line = None 
    
    def __init__(self):
        self.line_width = screen_width
        self.line_height = random.randrange(1,int(screen_height/5))
        self.noised_line = self.white_noise_pygame_image(self.line_width, self.line_height)
        self.line_increment = random.randrange(3,7)
        self.is_living = False
        self.offset_line = 0
            
    def display_line(self, screen):       
        #TODO may remove the comented line, it's how to do a simple line without noise
        #img = Image.new('RGBA', size=(line_width, line_height), color=(127,127,127,127))
        #raw_str  = img.tobytes("raw", 'RGBA')
        #pygame_image = pygame.image.fromstring(raw_str, img.size, 'RGBA')   
        #pygame_image = self.white_noise_pygame_image(line_width, line_height) white noise line
        if self.is_living == True:
            screen.blit(self.noised_line , (0, self.offset_line))        
            self.offset_line = (self.offset_line + self.line_increment)%screen_height
        
        if self.offset_line == 0:
            self.is_living = False
        
    def white_noise_pygame_image(self, width, height):
        transparency_max = 50
        pil_map = Image.new("RGBA", (width, height), 255)
        random_grid = map(lambda x: (
                ((int(random.random() * 256),)*3) + ((int((x/width)*(transparency_max/height)) if (int((x/width)*(transparency_max/height)))<(transparency_max/2) else transparency_max- int((x/width)*(transparency_max/height))),)
            ), range(0, width * height))
            
            
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
    t = None
    glitch_t = None
    
    def __init__(self):

        self.track_picture_updated = False
        self.track_updated = False
        self.glitcher = ImageGlitcher()
        self.glitch_mutex = threading.Lock()
        
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
        self.compute_glitch_images(random.randrange(10,50))
        
        self.noised_lines = []
        for i in range(0,5):
            self.noised_lines.append(CrtNoiseLine())
 
    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."
        
    def crop_text(self, text, font_local, size, draw_image):
        w, h = draw_image.textsize(text, font = font_local)
        if w > size:
            remove_char = 3
            while draw_image.textsize(text[:-remove_char]+"...", font = font_local)[0] > size:
                remove_char+=1
                w, h = draw_image.textsize(text, font = font_local) 
            return text[:-remove_char]+"..."
        else:
            return text    
    
    def get_spotify_image(self, spotify_reader):
        new_width = 339
        
        new_track = spotify_reader.get_current_track_info()
        
        if new_track != self.track:    
            self.track_updated = True
            if new_track  != None:
                old_album_uri = self.track.album_uri if self.track != None else ""
                
                if  old_album_uri != new_track.album_uri or self.track.album_name != new_track.album_name or self.track.title != new_track.title or new_track.duration_percent != self.track.duration_percent or new_track.is_playing != self.track.is_playing:  
                    image_uri = new_track.album_uri
                    image_str = urlopen(image_uri).read()
                    image_file = io.BytesIO(image_str)        
                    image_PIL = Image.open(image_file).convert("RGBA")
                    new_height = int(image_PIL.height * (new_width/image_PIL.width))
                    self.PIL_spotify_image = blank_picture.copy()
                    self.PIL_spotify_image.paste(image_PIL.resize((new_width, new_height), Image.ANTIALIAS), pos_image)
                    
                    font25Medium = ImageFont.truetype('./Noir/NoirStd-Medium.ttf', 27)
                    font25Regular = ImageFont.truetype('./Noir/NoirStd-Regular.ttf', 27)
                    font15Medium = ImageFont.truetype('./Noir/NoirStd-Medium.ttf', 21)
                    font15Regular = ImageFont.truetype('./Noir/NoirStd-Regular.ttf', 21)
                    
                    padding_width = 415
                    white = (255,)*3
                    grey = (75,)*3
                    PIL_draw_image = ImageDraw.Draw(self.PIL_spotify_image)
                    PIL_draw_image.text((padding_width, 70), self.crop_text(new_track.artists_name[0],font25Medium,264,PIL_draw_image), font = font25Medium, fill = grey)                    
                    PIL_draw_image.text((padding_width, 115), "Title", font = font15Regular, fill = white)
                    PIL_draw_image.text((padding_width, 150), self.crop_text(new_track.title,font25Regular,264,PIL_draw_image), font = font25Regular, fill = grey)
                    PIL_draw_image.text((padding_width, 200), "Album", font = font15Regular, fill = white)
                    PIL_draw_image.text((padding_width, 235), self.crop_text(new_track.album_name,font25Regular,264,PIL_draw_image), font = font25Regular, fill = grey)
                    PIL_draw_image.text((padding_width, 285), new_track.duration, font = font15Regular, fill = grey) 
                    
                    rectangle_width = 220
                    rectangle_height = 4
                    
                    rectangle_x = 440
                    rectangle_y = 343
                    
                    PIL_draw_image.rectangle([(rectangle_x,rectangle_y), (rectangle_x+rectangle_width,rectangle_y+rectangle_height)], fill = (50,)*3)
                    
                    rectangle_width = int(rectangle_width*new_track.duration_percent/100)
                    
                    PIL_draw_image.rectangle([(rectangle_x,rectangle_y), (rectangle_x+rectangle_width,rectangle_y+rectangle_height)], fill = (250,)*3)
                    
                    if new_track.is_playing:
                        self.PIL_spotify_image.paste(play_picture, (415,335))
                    else:
                        self.PIL_spotify_image.paste(pause_picture, (415,335))
                    
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
        self.t = threading.Timer(period, self.get_spotify_image_timer, args=(spotify_reader,period))
        self.t.start()
            
        
    def display_spotify_image(self):
        self.screen.blit(self.pygame_spotify_image, (0,0))
        
    def compute_glitch_images(self, number):
        self.glitch_mutex.acquire()
        self.glitch_images = []
        glitch_factor = random.random()*2+1
        for i in range(0,number):
            glitch_img = self.glitcher.glitch_image(self.PIL_spotify_image , glitch_factor, color_offset=True, scan_lines=False).convert("RGBA")
            self.glitch_images.append(self.PIL_to_pygame(glitch_img))
        
        self.glitch_mutex.release()

    def threaded_compute_glitch_images(self, number):
        self.glitch_t = threading.Thread(target=self.compute_glitch_images, args=(number,))
        self.glitch_t.daemon = True
        self.glitch_t.start()
        return self.glitch_t

    def display_glitch_images(self):        
        self.glitch_mutex.acquire()
        for glitch_image in self.glitch_images:
            self.screen.blit(glitch_image, (0,0))  
        self.glitch_mutex.release()
            
    def display_glitch_image(self, index): 
        if self.glitch_mutex.locked() == True:
            return False
        self.glitch_mutex.acquire()
        if index >= self.number_glitch_images():
            index = index%self.number_glitch_images()
        self.screen.blit(self.glitch_images[index], (0,0))          
        self.glitch_mutex.release()
        return True
            
    def number_glitch_images(self):
        return len(self.glitch_images)
    
    def display_lines(self):
        probability = 500
        for line in self.noised_lines:
            if line.is_living == False:
                if random.random()*probability > probability-1:
                    line.revive()
            line.display_line(self.screen)
            
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
scope.get_spotify_image_timer(spotify_reader, 2)
scope.display_spotify_image()
pygame.display.flip()

loop_index = 0
loop_max = random.randrange(2,10)*60

glitch_index = 0

        
def exit_gracefully(signum, frame):
    if scope.t != None:
        scope.t.cancel()
        
    try:
        scope.glitch_mutex.release()
    except:
        pass
    sys.exit()
        
signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)

while(True):
    
    if loop_index >= loop_max:
        displayed = scope.display_glitch_image(glitch_index)
        if displayed == False:
            scope.display_spotify_image()
        glitch_index += 1
        if glitch_index >= scope.number_glitch_images():              
            loop_max = random.randrange(2,10)*60
            loop_index = 0
            glitch_index = 0
            scope.threaded_compute_glitch_images(random.randrange(10,50))
            
    else:               
        scope.display_spotify_image()
        loop_index += 1
    
    scope.display_lines()
    
    pygame.display.update()
            