"""
##############################################################################
# run_ale.py
#
# Runs A.L.E and communicate with it through FIFO pipes. Saves the current
# screen as a numpy array, and sends it to the given player_agent to get the
# next action. Sends back teh returned action to A.L.E, and the loop goes on,
# until A.L.E exits.
##############################################################################
"""
from    pylab               import  *
from    numpy               import  * 
from    subprocess          import  Popen, PIPE
from    random              import  randint
from    common_constants    import  actions_map
from    cPickle             import  dump, load
import  common_constants


def run_ale( player_agent, game_settings, working_directory = ".",
                save_reward_history = True, plot_reward_history = False, 
                ale_location = None, rom_location = None,
                ale_bin_file = None):
    """
        Runs A.L.E with the given ROM file, and communicates with it through
        FIFO pipes. On each time-step, it sends the current screen to
        the player_agent object, and sends the action returned by it back to
        A.L.E
    """
    if ale_location is None:
        ale_location = "../"  
                            
                
    if rom_location is None:
        rom_location =  "./"
        
    if ale_bin_file is None:
        ale_bin_file = "ale"
    
    rom_file            = game_settings.rom_file
    update_screen_matrix= game_settings.uses_screen_matrix
    update_console_ram  = game_settings.uses_console_ram
    skip_frames_num     = game_settings.skip_frames_num
                
    # Run A.L.E
    args = [ale_location + ale_bin_file, "-game_controller", "fifo",
            rom_location + rom_file]
    p = Popen(args, stdin=PIPE, close_fds=True)
    
    # Open the input/output pipes
    try: 
        fin  = open('ale_fifo_out')
        fout = open('ale_fifo_in', 'w')
    except IOError, e:
        print e
        print   """
                For this function to work, it needs two FIFO Pipes created:
                    ale_fifo_out (A.L.E writes its output here)
                    ale_fifo_in  (A.L.E reads its input from here)
                In *NIX based operating systems, this can achieved by:
                    > mkfifo ale_fifo_out
                    > mkfifo ale_fifo_in
                """
        exit()
    
    # We first get the width and height of the screen from A.L.E
    str_in = fin.readline()
    str_in_split = str_in.split('-')
    width   = int(str_in_split[0])
    height  = int(str_in_split[1])
    if width > 0 and height > 0:
        fout.write("%d,%d,%d\n"%(update_screen_matrix, update_console_ram,
                                 skip_frames_num))
        fout.flush()
    else:
        exit("Invalid width and height (%d, %d) recieved from A.L.E")
    # update the common_constants stettings
    common_constants.screen_height = height
    common_constants.screen_width = width
    # Now, for each frame of the game, we recieve a screen update
    screen_matrix = zeros((height, width), int32) - 2
    while p.poll() is None:
        # We get an (index,update) for every updated pixel.
        # The update pairs are seperated by '-'. If there is no update, we will
        # recieve: "NADA\n"
        # 1- Read in the update string from the pipe
        in_line = fin.readline()
        if in_line == "" and p.poll() is not None:
            # make sure the A.L.E process has not died
            break
        # The first 128 * 3 characters contain the Console RAM
        if update_console_ram:
            ram_ind = 128 * 3
            ram_str = in_line[0:ram_ind]
            try:
                ram_array = gen_ram_array(ram_str)
            except ALECommunicationError:
                print "Communication broke with A.L.E"
                break
            update_str = in_line[ram_ind:]
        else:
            ram_array = None
            update_str = in_line
        
        # Update the screen-matrix
        if update_screen_matrix:
            try:
                update_screeen_matrix(screen_matrix, update_str)
            except ALECommunicationError:
                print "Communication broke with A.L.E"
                break
        else:
            screen_matrix = None

        # 2- get the actiosn from the player agent
        player_a_action = player_agent.agent_step(screen_matrix, ram_array)
        
        # 3- Send back the new actions
        if p.poll() is not None:
            break   # make suret he ALE process has not died
        fout.write("%d,%d\n"%(player_a_action, actions_map['player_b_noop']))
        fout.flush()
    
    if save_reward_history:
        # save the reward history
        fout = open(working_directory + "/" + "reward_history.pik", 'wd')
        dump(player_agent.reward_history, fout)
        fout.close()
    if plot_reward_history:
        # Plot the reward history
        plot(player_agent.reward_history)
        # plot the moving average
        smoothed_rewards = get_moving_average(player_agent.reward_history,
                                              num_steps = 20)
        figure()
        plot(smoothed_rewards)
        show()

def _index_to_ij(index, height, width):
    "Converts the index to i and j of our screen matrix"
    j = index / width
    i = index % width
    return i, j


def gen_ram_array(ram_str):
    "Converts the string containng the Console RAM to an array"
    curr_ind = 0
    ram_array = []
    for i in range(128):
        try:
            byte_val = int(ram_str[curr_ind:curr_ind+3])
        except ValueError:
            raise ALECommunicationError
        ram_array.append(byte_val)
        curr_ind += 3
    return ram_array

def print_ram_content(ram_array):
    "Prints the content of the Console ram, is similar format as A.L.E debug"
    for i in range(8):
        for j in range(16):
            byte_val = ram_array[i*16 + j]
            right_int = byte_val & 15
            left_int = (byte_val-right_int) >> 4
            # print "%03i\t"%byte_val,
            print "%1x%1x"%(left_int, right_int),
        print

def update_screeen_matrix(screen_matrix, update_str):
    "Updates the current screen matrix, based on the update string"
    if update_str != "NADA\n":               
        line_ptr = 0
        line_length = len(update_str) - 1
        while (line_ptr < line_length):
            try:
                i = int(update_str[line_ptr:line_ptr+3])
                j = int(update_str[line_ptr+3:line_ptr+6])
            except ValueError:
                raise ALECommunicationError
            value = int(update_str[line_ptr+6:line_ptr+9])
            screen_matrix[j, i] = value
            line_ptr += 9


def export_screen_matrix_to_png(screen_matrix, filename):
    "Saves the current screen matrix as a png file"
    # 1- Generate a random color map
    M = screen_matrix
    color_ind_list = M[M.nonzero()].tolist()
    tmp_dict = {}
    unique_color_inds = tmp_dict.fromkeys(color_ind_list).keys()
    random_color_map = {}
    for unique_color_ind in unique_color_inds:
        r = randint(1, 255)
        g = randint(1, 255)
        b = randint(1, 255)
        random_color_map[unique_color_ind] = (r,g,b)
    random_color_map[0] = (0, 0, 0)
    from PIL import Image
    plot_height, plot_width = shape(screen_matrix)
    rgb_array = zeros((plot_height, plot_width , 3), uint8)
    counter = 0 
    for i in range(plot_height):
        for j in range(plot_width):
            pixel_int = screen_matrix[i, j]
            r,g,b = random_color_map[pixel_int]
            rgb_array[i,j,0] = r
            rgb_array[i,j,1] = g
            rgb_array[i,j,2] = b
    pilImage = Image.fromarray(rgb_array, 'RGB')
    pilImage.save(filename)
    print "random_color_map: \n", random_color_map
    exit()


def get_moving_average(vec, num_steps):
    moving_average_vec = []
    for i in range(num_steps, len(vec) - num_steps):
        sum = 0
        sum += vec[i]
        for j in range(1, num_steps + 1):
            sum += vec[i - j]
            sum += vec[i + j]
        average = float(sum) / float(2 * num_steps + 1)
        moving_average_vec.append(average)
    return moving_average_vec

class ALECommunicationError(ValueError):
    "This class is thrown when the communication breaks down with A.L.E"
    pass
