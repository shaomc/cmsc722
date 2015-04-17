"""
##############################################################################
# sample_gathering_agent.py
#
# The implementation of the SampleGatheringAgent class, which is resposible
# for acting randomly in a game, and collecting samples
##############################################################################
"""

from    numpy               import      *
from 	sys                 import      exit
from	pylab               import      *
from    os                  import      mkdir
from    os.path             import      exists
from    random              import      randint
from    player_agent        import      PlayerAgent
from    samples_manager     import      SamplesManager
from    run_ale             import      run_ale
from    common_constants    import      actions_map
from    game_settings       import      AstrixSettings, SpaceInvadersSettings, \
                                        FreewaySettings, SeaquestSettings


class SampleGatheringAgent(PlayerAgent):
    """
        A player agent that acts randomly in a game, and gathers samples.
        These samples are later used to detect the game background, and
        also detect object classes.
        
        Instance Variables:
            - num_samples       Number of samples to collect
            - act_contin_count  Number of frames we should repeat a
                                randomly selected action
            - samples_count     Number of samples we have collected
                                so far
            - reset_count_down  sometimes we need to send reset
                                action for a number of frames
            - curr_action       The action taken in the previous step
            - curr_action_count Number of times we have taken this action
            - samples_manager   Instance of SampleManager class, responsible
                                for gathering samples
            - rand_run_only     When true, we will just do a random-run, without
                                actually gathering any samples

    """
    def __init__(self, game_settings, samples_name, num_samples, 
                 action_continuity_count, working_directory = ".",
                 rand_run_only = False):
        PlayerAgent.__init__(self, game_settings, working_directory)
        #TODO: Update this, to properly support the new GameSettings framework
        self.samples_manager    = SamplesManager(samples_name, working_directory)
        self.num_samples        = num_samples
        self.act_contin_count   = action_continuity_count
        self.samples_count      = 0
        self.curr_action        = None
        self.curr_action_count  = 0
        self.restart_delay      = 0
        self.initial_delay      = 100
        self.episode_status     = 'uninitilized'
        self.reward_history     = []
        self.episode_counter    = 0
        self.episode_reward     = 0
        self.rand_run_only      = rand_run_only

    def agent_step(self, screen_matrix, console_ram, reward = None):
        """
            The main method. Given a 2D array of the color indecies on the
            screen (and potentially the reward recieved), this method 
            will decides the next action based on the learning algorithm.
            Here, we are using random actions, and we save each new 
        """
        # See if we ar in the inital-delay period. 
        if self.initial_delay > 0:
            # We do nothing, until the game is ready to be restarted.
            self.initial_delay -= 1
            print "Initial delay:", self.initial_delay
            return actions_map['player_a_noop']
        
        # At the very begining, we have to restart the game
        if self.episode_status == "uninitilized":
            if self.game_settings.first_action is not None:
                # Perform the very first action next (this is hard-coded)
                self.episode_status = "first_action"
            else:
                self.episode_status = "ended"
            self.restart_delay = self.game_settings.delay_after_restart
            return actions_map['reset']
        
        # See if we are in the restart-delaying state
        if self.restart_delay > 0:
            print "Restart delay:", self.restart_delay
            self.restart_delay -= 1
            return actions_map['player_a_noop']
        
        # See if we should apply the very first action
        if self.episode_status == "first_action":
            print "Sending first action:", self.game_settings.first_action
            self.episode_status = 'ended'
            return actions_map[self.game_settings.first_action]
    
        # See if we are the end of the game
        if self.game_settings.is_end_of_game(screen_matrix, console_ram):
            # End the current episode and send a Reset command
            print "End of the game. Restarting."
            if self.game_settings.first_action is not None:
                self.episode_status = "first_action"
            else:
                self.episode_status = "ended"
            self.restart_delay = self.game_settings.delay_after_restart
            return actions_map['reset']
        
        if reward is None:
            reward = self.game_settings.get_reward(screen_matrix, console_ram)
            if reward != 0:
                print "reward = ", reward
        self.episode_reward += reward

        if  self.episode_status == 'ended':
            # Log the rewards recieved in previous episode        
            print "Epsidoe #%d: Sum Reward = %f" %(self.episode_counter,
                                                   self.episode_reward)
            self.reward_history.append(self.episode_reward)
            self.episode_counter += 1
            self.episode_reward = 0
            self.episode_status = 'started'


        if  self.curr_action is None or \
            self.curr_action_count >= self.act_contin_count:
            # Choose a new radnom aciton
            act_ind = randint(0, self.num_actions - 1)
            new_act = actions_map[self.game_settings.possible_actions[act_ind]]
            self.curr_action = new_act
            self.curr_action_count = 0
        else:
            # Repeat the previous action
            new_act = self.curr_action
            self.curr_action_count += 1
        
        if self.rand_run_only:
            return new_act
    
        # Generate a new sample
        self.samples_manager.add_sample(screen_matrix, array(console_ram),
                                        new_act, reward)
        self.samples_count += 1
        if self.samples_count >= self.num_samples:
            # We have enough samples
            self.samples_manager.save_to_disk()
            print "Collected %d samples."%self.samples_count
            print "Plottign thumbnails..."
            self.samples_manager.export_screen_thumbnails("thumbnails",
                                                          every_x_frames = 1)
            print "done."
            exit(0)
        
        return new_act

def collect_random_samples(game_settings, samples_name, num_samples,
                           action_continuity_count, working_directory,
                           save_reward_history, plot_reward_history,
                           rand_run_only = False):
    "Runs A.L.E, and collects the specified number of ransom samples"
    if not exists(working_directory):
        mkdir(working_directory)
    player_agent = SampleGatheringAgent(game_settings, samples_name,  
                                        num_samples, action_continuity_count,
                                        working_directory, rand_run_only)
    run_ale(player_agent, game_settings, working_directory,
                save_reward_history, plot_reward_history)

if __name__ == "__main__":
    game_settings = FreewaySettings()
    game_settings.uses_screen_matrix = True
    save_reward_history = True
    plot_reward_history = True
    rand_run_only = False
    samples_name = "samples_random"
    working_directory = "./"
    num_samples = 1000
    action_continuity_count = 0
    collect_random_samples(game_settings, samples_name, num_samples, 
                            action_continuity_count, working_directory,
                            save_reward_history, plot_reward_history,
                            rand_run_only)
