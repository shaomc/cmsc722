"""
##############################################################################
# simple_manager.py
#
# Implementation of SamplesManager class, which manages the samples we collect
# from a game
##############################################################################
"""


from    pylab       import  *
from    numpy       import  *
from    scipy       import  sparse
from    numpy       import  matlib
from    math        import  ceil
from    sys         import  exit
from    os          import  mkdir
from    os.path     import  exists
from    cPickle     import  dump, load
from    random      import  randint


class SamplesManager(object):
    """
        This class manages the samples collected from an Atari game.
        Each sample contains a matrix of color numbers, an array of the
        RAM content, and an action, and an optional reward.
        
            
        Object Variables:
            - working_dir           The directory to save/load files
            - samples_name          Name of the samples 
            - num_samples           Number of samples
            - screens               screen[i] is a matrix of color indecies of
                                    the screen capture for sample i
            - ram_contents          ram_contents[i] is an array containing the
                                    the ram content at time-step i
            - rewards               rewards[i] is reward recieved in sample i
            - actions               actions[i] is action performed in sample i
            
    """
    def __init__(self, samples_name, working_dir = "."):
        """
            Constructor
        """
            # Start an uninitilized object
        self.samples_name       = samples_name
        self.num_samples        = 0
        self.screens            = []
        self.ram_contents       = []
        self.rewards            = []
        self.actions            = []
        self.working_dir        = working_dir

    def add_sample(self, new_screen, new_ram, new_action, new_reward = None):
        """
            Adds a new sample to our list of samples.
            new_screen should be a numpy array
        """
        self.screens.append(new_screen.copy())
        self.ram_contents.append(new_ram.copy())
        self.actions.append(new_action)
        self.rewards.append(new_reward)
        self.num_samples += 1
        
    def get_screen_shape(self):
        "Returns the height and width of the screens"
        assert self.num_samples > 0
        return shape(self.screens[0])

    def get_unique_actions(self):
        "Returns the list of unique actions in the samples"
        try:
            # see if we have set it before
            unique_actions = self.unique_actions
        except AttributeError:
            # Nope, lets set them
            action_map = {}
            for a in self.actions:
                action_map[a] = 1
            unique_actions = self.unique_actions = action_map.keys()
        return unique_actions

    def get_unique_color_ind(self):
        "Returns the list of unique color indecies in the samples"
        try:
            # see if we have set it before
            unique_colors = self.unique_color_ind
        except AttributeError:
            # Nope, lets set them
            unique_colors = array([], int32)
            print "Collecting unique color indecies:",
            i = 0
            for screen in self.screens:
                new_inds = unique1d(screen)
                unique_colors = unique1d(concatenate((unique_colors, new_inds)))
                i += 1
                if i % 100:
                    print "\t %d samples proccessed."%i
            print "Done."
            self.unique_color_ind = unique_colors    
            self.save_to_disk()
            
        return self.unique_color_ind
        
    def load_from_disk(self):
        print "Loading the samples object... ",
        fin = open(self.working_dir + "/" + self.samples_name + ".pik")
        loaded_obj = load(fin)
        fin.close()
        self.samples_name   = loaded_obj.samples_name
        self.num_samples    = loaded_obj.num_samples
        self.screens        = loaded_obj.screens
        self.rewards        = loaded_obj.rewards
        self.actions        = loaded_obj.actions
        try:
            self.unique_actions = loaded_obj.unique_actions
        except AttributeError:
            pass
        try:
            self.unique_color_ind = loaded_obj.unique_color_ind
        except AttributeError:
            pass
        print "done."

    def save_to_disk(self):
        "Saves the object to disk"
        print "Saving the samples object to disk... ",
        file_name = self.samples_name + ".pik"
        fout = open(self.working_dir + "/" + file_name, 'wd')
        dump(self, fout, -1)
        fout.close()
        print "done."
    

    def plot(self, sample_num, color_map):
        """
            Plots the indicated sample 
        """
        self.plot_screen_matrix(self.screens[sample_num], color_map)
        
    def plot_screen_matrix(self, screen_matrix, color_map = None):
        """
            Plots the given screen matrix.
            If no color_map is provided, we will generate a random one
        """
        if color_map is None:
            color_map = self._gen_random_color_map()
        plot_height, plot_width = shape(screen_matrix)
        rgb_array = zeros((plot_height, plot_width , 3))
        counter = 0 
        for i in range(plot_height):
            for j in range(plot_width):
                color_index = screen_matrix[i, j]
                r,g,b = color_map[color_index]
                rgb_array[i,j,0] = float(r) / 256.0
                rgb_array[i,j,1] = float(g) / 256.0
                rgb_array[i,j,2] = float(b) / 256.0
        imshow(rgb_array)           
    
    def export_screen_matrix_to_png(self, screen_matrix, filename,
                                    color_map = None):
        "Saves the given screen matrix as a png file"
        try: 
            from PIL import Image
        except ImportError:
            exit("Unable to import PIL. Python Image Library is required for" +
                 " exporting screen matrix to PNG files")
        if color_map is None:
            color_map = self._gen_random_color_map()
        plot_height, plot_width = shape(screen_matrix)
        rgb_array = zeros((plot_height, plot_width , 3), uint8)
        counter = 0 
        for i in range(plot_height):
            for j in range(plot_width):
                color_index = screen_matrix[i, j]
                r,g,b = color_map[color_index]
                rgb_array[i,j,0] = r
                rgb_array[i,j,1] = g
                rgb_array[i,j,2] = b
        pilImage = Image.fromarray(rgb_array, 'RGB')
        pilImage.save(filename)

    
    def export_screen_thumbnails(self, export_dir, color_map = None,
                                 every_x_frames = 10):
        "Saves a screenshot of a portion of teh samples to the given directory"
        if color_map is None:
            color_map = self._gen_random_color_map()
        export_dir = self.working_dir + "/" + export_dir
        if not exists(export_dir):
            mkdir(export_dir)
        print "Exporting sample thumbnails...",
        for i in range(0, self.num_samples, every_x_frames):
            file_name = export_dir + "/sample_num_%d.png"%i
            self.export_screen_matrix_to_png(self.screens[i], file_name,
                                             color_map)
        print "done."

    def _gen_random_color_map(self):
        colors_ind = self.get_unique_color_ind()
        color_ind_to_rgb = {}
        for color_ind in colors_ind:
            r = randint(1, 255)
            g = randint(1, 255)
            b = randint(1, 255)
            color_ind_to_rgb[color_ind] = (r, g, b)
        return color_ind_to_rgb
        