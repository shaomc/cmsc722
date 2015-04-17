"""
##############################################################################
# player_agent.py
#
# The implementation of the PlayerAgent abstract class
##############################################################################
"""

from    numpy           import  *
from 	sys             import  exit
from	pylab           import  *
from    os              import  mkdir
from    os.path         import  exists


class PlayerAgent(object):
    """
        This is an abstract class and should be the Superclass for all
        agent classes that run_ale interacts with
        
        Instance variabls:
            - game_settings         An instance of the GameSettings class
            - curr_screen_matrix    2D array of color indecies
            - curr_console_ram      Content of the Console RAM
            - possible_actions      List of possible actions to choose from
            - num_actions           Number of possible acitons
            - working_directory     The directory to save/load files
    """
    
    def __init__(self, game_settings, working_directory = "."):
        "Constructor"
        self.game_settings = game_settings
        self.curr_screen_matrix = None
        self.curr_console_ram   = None
        possible_actions = game_settings.possible_actions
        if possible_actions is None:
            # If no actions are specified, all actions are possible
            possible_actions = ['player_a_noop',    'player_a_fire', 
                                'player_a_up',      'player_a_right',
                                'player_a_left',    'player_a_down',
                                'player_a_upright', 'player_a_upleft',
                                'player_a_downright','player_a_downleft',
                                'player_a_upfire',  'player_a_rightfire',
                                'player_a_leftfire','player_a_downfire',
                                'player_a_uprightfire','player_a_upleftfire',
                                'player_a_downrightfire','player_a_downleftfire']
        self.possible_actions = possible_actions
        self.num_actions = len(possible_actions)
        self.working_directory = working_directory
        if not exists(self.working_directory):
            mkdir(self.working_directory)

    def agent_step(self, screen_matrix, console_ram, reward=None):
        """
            The main method. given a 2D array of the color indecies on the
            screen, and the content of teh consoel RAM (and potentially the reward recieved, this method 
            will decides the enxt action based on the learning algorithm.
        """
        exit("PlayerAgent.agent_step() is an abstract method, and must be " +
             "overridden by the subclasses")
    
    def plot_current_screen(self, color_map):
        "Plots the current screen"
        rgb_array = zeros((plot_height, plot_width , 3))
        for i in range(plot_height):
            for j in range(plot_width):
                pixel_int = self.curr_screen_matrix[i, j]
                r,g,b = color_map[pixel_int]
                rgb_array[i,j,0] = float(r) / 256.0
                rgb_array[i,j,1] = float(g) / 256.0
                rgb_array[i,j,2] = float(b) / 256.0
        imshow(rgb_array)

    def export_screen_matrix_to_png(self, filename, color_map,
                                    export_folder = None):
        "Saves the current screen matrix as a png file"
        try: 
            from PIL import Image
        except ImportError:
            exit("Unable to import PIL. Python Image Library is required for" +
                 " exporting screen matrix to PNG files")
        plot_height, plot_width = shape(self.curr_screen_matrix)
        rgb_array = zeros((plot_height, plot_width , 3), uint8)
        counter = 0 
        for i in range(plot_height):
            for j in range(plot_width):
                pixel_int = self.curr_screen_matrix[i, j]
                r,g,b = color_map[pixel_int]
                rgb_array[i,j,0] = r
                rgb_array[i,j,1] = g
                rgb_array[i,j,2] = b
        pilImage = Image.fromarray(rgb_array, 'RGB')
        if export_folder is not None:
            export_folder = self.working_directory + "/" + export_folder
            if not exists(export_folder):
                mkdir(export_folder)
        else:
            export_folder = self.working_directory
        pilImage.save(export_folder + "/" + filename)
