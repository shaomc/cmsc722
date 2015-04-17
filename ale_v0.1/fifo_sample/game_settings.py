"""
##############################################################################
# game_settings.py
#
# The implementation of the GameSettings class, which is the superclass for
# other game-settings classes. These classes contain game-specific information
# and functionality.
##############################################################################
"""

from    numpy               import      *
from 	sys                 import      exit
from	pylab               import      *
from    os                  import      mkdir
from    os.path             import      exists
from    random              import      randint
from    common_constants    import      actions_map

class GameSettings(object):
    """
        This is the superclass for other game-settings classes.
        These classes contain game-specific data and functionality, such
        as how to determine the reward from the game, or how to tell
        when the game has ended
        
        Instance Variables:
            - rom_file              The location of the game rom file
            - possible_actions      List of allowed actions in the game, or None
                                    for all actions
            - uses_screen_matrix    True means that this games requires the
                                    updated screen-matrix, for either reward
                                    or end-of-game extraction
            - uses_console_ram      True means that this games requires the
                                    updated console RAM content, for either 
                                    reward or end-of-game extraction
            - skip_frames_num       We skip this many frames, after seeing a
                                    frame of the game. Skipping is done to
                                    increase the speed of the simulations
            - delay_after_restart   Delay this number of frames after restarting
                                    Some games do not update the game-state
                                    (either the screen or the RAM values)
                                    for some frames after restarting.
            - first_action          Some games need a specical action at the very
                                    beginning, just to start the game. None means
                                    the game requires no such special action
    """
    
    def __init__(self, rom_file, possible_actions,
                 uses_screen_matrix, uses_console_ram,
                 skip_frames_num, delay_after_restart, first_action):
        self.rom_file           = rom_file
        self.possible_actions   = possible_actions
        self.uses_screen_matrix = uses_screen_matrix
        self.uses_console_ram   = uses_console_ram
        self.skip_frames_num    = skip_frames_num
        self.delay_after_restart= delay_after_restart
        if self.skip_frames_num > 1:
            self.delay_after_restart *= self.skip_frames_num
        self.first_action       = first_action
        
    def get_reward(self, screen_matrix, console_ram):
        """
            Returns the reward, based on either the current screen matrix
            or the contents of the console RAM, or both.
        """
        print "GameSettings.get_reward() is an abstract method. " + \
                "It must be overriden by the subclass"
        exit(-1)
    
    def is_end_of_game(self, screen_matrix, console_ram):
        """
            Returns true if we are currently at the end of the game (based on 
            either the current screen matrix or the contents of the console RAM)
        """
        print "GameSettings.is_end_of_game() is an abstract method. " + \
                "It must be overriden by the subclass"
        exit(-1)
        

class FreewaySettings(GameSettings):
    """
        Contains game-specific data and functionality, such
        as how to determine the reward from the game, or how to tell
        when the game has ended, for the game Freeway
        
        Instance Variables:
            - prev_score        Score in the previous timestep
            - episode_counter   Counts the episodes (A hack to determine end of
                                game)
    """
    def __init__(self):
        GameSettings.__init__(self,
                    rom_file = "freeway.bin",
                    possible_actions    = [ 'player_a_noop', 'player_a_up',
                                            'player_a_down'],
                    uses_screen_matrix  = False,
                    uses_console_ram    = True,
                    skip_frames_num     = 3,
                    delay_after_restart = 1,
                    first_action        = None)
        self.prev_score = 0
        self.episode_counter = 0
        
    def get_reward(self, screen_matrix, console_ram):
        """
            Returns the reward, by reading the score from the console RAM
        """
        byte_val = console_ram[103]
        right_digit = byte_val & 15
        left_digit = (byte_val-right_digit) >> 4        
        score = left_digit * 10 + right_digit
        reward = score - self.prev_score
        if reward < 0:
            reward = 0  # sometimes the score is reset
        self.prev_score = score
        return reward
    
    def is_end_of_game(self, screen_matrix, console_ram):
        """
            Returns true if we are currently at the end of the game (based on 
            either the current screen matrix or the contents of the console RAM)
            Currently I am using a hack, which returns true after 2000 episodes
        """
        
        if self.episode_counter > 2000:
            self.episode_counter = 0
            return True
        else:
            self.episode_counter += 1
            return False
        
        
class SpaceInvadersSettings(GameSettings):
    """
        Contains game-specific data and functionality, such
        as how to determine the reward from the game, or how to tell
        when the game has ended, for the game Space Invaders
        
        Instance Variables:
            - prev_score        Score in the previous timestep
            - prev_lives        Number of lives in the previous step
            - episode_counter   Counts the episodes (A hack to determine end of
                                game)
    """
    def __init__(self):
        GameSettings.__init__(self,
                    rom_file = "spaceinvaders.bin",
                    possible_actions    = [ 'player_a_rightfire',
                                            'player_a_leftfire',
                                            'player_a_noop',
                                            'player_a_left',
                                            'player_a_right'],
                    uses_screen_matrix  = False,
                    uses_console_ram    = True,
                    skip_frames_num     = 2,
                    delay_after_restart = 20,
                    first_action        = None)
        self.prev_score         = 0
        self.episode_counter    = 0
        self.prev_lives         = None
        
    def get_reward(self, screen_matrix, console_ram):
        """
            Returns the reward, by reading the score from the console RAM
            The score is written on two bytes: 104 (lower two digits)
            102 (higher digits)
        """
        score = self.get_score(console_ram)
        reward = score - self.prev_score
        # if reward < 0:
        #     reward = 0  # sometimes the score is reset
        self.prev_score = score
        if reward > 0:
            return 1
        else:
            return 0
    
    def get_score(self, console_ram):
        "Returns the current score in the game"
        score = 0
        lower_digits_val = console_ram[104]
        lower_right_digit = lower_digits_val & 15
        lower_left_digit = (lower_digits_val-lower_right_digit) >> 4
        score += (10 * lower_left_digit) + lower_right_digit
        higher_digits_val = console_ram[102]
        higher_right_digit = higher_digits_val & 15
        higher_left_digit = (higher_digits_val-higher_right_digit) >> 4
        score += (1000 * higher_left_digit) + 100 * higher_right_digit
        return score
    
    def is_end_of_game(self, screen_matrix, console_ram):
        """
            Returns true if we are currently at the end of the game (based on 
            either the current screen matrix or the contents of the console RAM)
            Here we look up number of lives left from RAM and return True when
            we have lost one life
        """
        new_lives = console_ram[73]
        if self.prev_lives is None or self.prev_lives <= new_lives:
            self.prev_lives = new_lives
            return False
        else:
            return True
        
        
class AstrixSettings(GameSettings):
    """
        Contains game-specific data and functionality, such
        as how to determine the reward from the game, or how to tell
        when the game has ended, for the game Astrix
        
        Instance Variables:
            - prev_score        Score in the previous timestep
            - prev_lives        Number of lives in the previous step
            - episode_counter   Counts the episodes (A hack to determine end of
                                game)
    """
    def __init__(self):
        GameSettings.__init__(self,
                    rom_file = "asterix.bin",
                    possible_actions    = [ 'player_a_noop', 'player_a_left',
                                            'player_a_right','player_a_up',
                                            'player_a_down'],
                    uses_screen_matrix  = False,
                    uses_console_ram    = True,
                    skip_frames_num     = 0,
                    delay_after_restart = 100,
                    first_action        = 'player_a_fire')
        self.prev_score         = 0
        self.episode_counter    = 0
        self.prev_lives         = None
        
    def get_reward(self, screen_matrix, console_ram):
        """
            Returns the reward, by reading the score from the console RAM
            The score is written on two bytes: 96 (lower two digits)
            95 (higher digits)
        """
        score = self.get_score(console_ram)
        reward = score - self.prev_score
        if reward < 0:
            reward = 0  # sometimes the score is reset
        self.prev_score = score
        return reward
    
    def get_score(self, console_ram):
        "Returns the current score in the game"
        score = 0
        lower_digits_val = console_ram[96]
        lower_right_digit = lower_digits_val & 15
        lower_left_digit = (lower_digits_val-lower_right_digit) >> 4
        score += (10 * lower_left_digit) + lower_right_digit
        higher_digits_val = console_ram[95]
        higher_right_digit = higher_digits_val & 15
        higher_left_digit = (higher_digits_val-higher_right_digit) >> 4
        score += (1000 * higher_left_digit) + 100 * higher_right_digit
        return score

    def is_end_of_game(self, screen_matrix, console_ram):
        """
            Returns true if we are currently at the end of the game (based on 
            either the current screen matrix or the contents of the console RAM)
            Here we look up number of lives left from RAM and return True when
            we have lost one life
        """
        byte_val = console_ram[83]
        new_lives = byte_val & 15
        if self.prev_lives is None or self.prev_lives <= new_lives:
            self.prev_lives = new_lives
            return False
        else:
            return True

class SeaquestSettings(GameSettings):
    """
        Contains game-specific data and functionality, such
        as how to determine the reward from the game, or how to tell
        when the game has ended, for the game SeaQuest
        
        Instance Variables:
            - prev_score        Score in the previous timestep
            - prev_lives        Number of lives in the previous step
    """
    def __init__(self):
        GameSettings.__init__(self,
                    rom_file = "seaquest.bin",
                    possible_actions    = [ 'player_a_noop', 'player_a_left',
                                            'player_a_right','player_a_up',
                                            'player_a_down',
                                            'player_a_leftfire',
                                            'player_a_rightfire',
                                            'player_a_upfire',
                                            'player_a_downfire',
                                            'player_a_fire'],
                    uses_screen_matrix  = True,
                    uses_console_ram    = True,
                    skip_frames_num     = 3,
                    delay_after_restart = 100,
                    first_action        = None)
        self.prev_score         = 0
        self.prev_lives         = None
        
    def get_reward(self, screen_matrix, console_ram):
        """
            Returns the reward, by reading the score from the console RAM
            The score is written on two bytes: 96 (lower two digits)
            95 (higher digits)
        """
        score = self.get_score(console_ram)
        reward = score - self.prev_score
        if reward < 0:
            reward = 0  # sometimes the score is reset
        self.prev_score = score
        return reward
    
    def get_score(self, console_ram):
        "Returns the current score in the game"
        score = 0
        lower_digits_val = console_ram[58]
        lower_right_digit = lower_digits_val & 15
        lower_left_digit = (lower_digits_val-lower_right_digit) >> 4
        score += (10 * lower_left_digit) + lower_right_digit
        higher_digits_val = console_ram[57]
        higher_right_digit = higher_digits_val & 15
        higher_left_digit = (higher_digits_val-higher_right_digit) >> 4
        score += (1000 * higher_left_digit) + 100 * higher_right_digit
        return score

    def is_end_of_game(self, screen_matrix, console_ram):
        """
            Returns true if we are currently at the end of the game (based on 
            either the current screen matrix or the contents of the console RAM)
            Here we look up number of lives left from RAM and return True when
            we have lost one life
        """
        byte_val = console_ram[59]
        new_lives = byte_val & 15
        if self.prev_lives is None or self.prev_lives <= new_lives:
            self.prev_lives = new_lives
            return False
        else:
            return True
        
class BowlingSettings(GameSettings):
    """
        Contains game-specific data and functionality, such
        as how to determine the reward from the game, or how to tell
        when the game has ended, for the game Bowling
        
        Instance Variables:
            - prev_score        Score in the previous timestep
            - prev_lives        Number of lives in the previous step
            - episode_counter   Counts the episodes (A hack to determine end of
                                game)
    """
    def __init__(self):
        GameSettings.__init__(self,
                    rom_file = "bowling.bin",
                    possible_actions    = [ 'player_a_noop', 'player_a_left',
                                            'player_a_right','player_a_up',
                                            'player_a_down'],
                    uses_screen_matrix  = False,
                    uses_console_ram    = True,
                    skip_frames_num     = 2,
                    delay_after_restart = 100,
                    first_action        = 'player_a_fire')
        self.prev_score         = 0
        self.episode_counter    = 0
        self.prev_lives         = None
        
    def get_reward(self, screen_matrix, console_ram):
        """
            Returns the reward, by reading the score from the console RAM
            The score is written on two bytes: 96 (lower two digits)
            95 (higher digits)
        """
        score = self.get_score(console_ram)
        reward = score - self.prev_score
        if reward < 0:
            reward = 0  # sometimes the score is reset
        self.prev_score = score
        return reward
    
    def get_score(self, console_ram):
        "Returns the current score in the game"
        score = 0
        lower_digits_val = console_ram[96]
        lower_right_digit = lower_digits_val & 15
        lower_left_digit = (lower_digits_val-lower_right_digit) >> 4
        score += (10 * lower_left_digit) + lower_right_digit
        higher_digits_val = console_ram[95]
        higher_right_digit = higher_digits_val & 15
        higher_left_digit = (higher_digits_val-higher_right_digit) >> 4
        score += (1000 * higher_left_digit) + 100 * higher_right_digit
        return score

    def is_end_of_game(self, screen_matrix, console_ram):
        """
            Returns true if we are currently at the end of the game (based on 
            either the current screen matrix or the contents of the console RAM)
            Here we look up number of lives left from RAM and return True when
            we have lost one life
        """
        byte_val = console_ram[83]
        new_lives = byte_val & 15
        if self.prev_lives is None or self.prev_lives <= new_lives:
            self.prev_lives = new_lives
            return False
        else:
            return True
