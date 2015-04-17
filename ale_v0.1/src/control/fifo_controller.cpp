/* *****************************************************************************
 * A.L.E (Atari 2600 Learning Environment)
 * Copyright (c) 2009-2010 by Yavar Naddaf
 * Released under GNU General Public License www.gnu.org/licenses/gpl-3.0.txt
 *
 * Based on: Stella  --  "An Atari 2600 VCS Emulator"
 * Copyright (c) 1995-2007 by Bradford W. Mott and the Stella team
 *
 * *****************************************************************************
 *  fifo_controller.cpp
 *
 *  The implementation of the FIFOController class, which is a subclass of 
 * GameConroller, and is resposible for sending the Screens/RAM content to 
 * whatever external program we are using through FIFO pipes, and apply the 
 * actions that are sent back
 **************************************************************************** */

#include "fifo_controller.h"


/* *********************************************************************
    Constructor
 ******************************************************************** */ 
FIFOController::FIFOController(OSystem* _osystem) : 
    GameController(_osystem) {
	p_fout = fopen("ale_fifo_out", "w");
	p_fin = fopen("ale_fifo_in", "r");
	 if (p_fout == NULL || p_fin == NULL) {
		cerr << "A.L.E expects two FIFO pipes to exist:\n";
		cerr << "\t ale_fifo_out (A.L.E will send its output here)\n";
		cerr << "\t ale_fifo_in (A.L.E will get its input from here)\n";
		exit(-1);
	}
		
	// Send the width and height of the screen through the pipe
	char out_buffer [50];
    cout << "i_screen_width = " << i_screen_width << " - i_screen_height =" <<   i_screen_height << endl;
	sprintf (out_buffer, "%d-%d\n", i_screen_width, i_screen_height);
	fputs(out_buffer, p_fout);
	fflush (p_fout);
	// Get confirmation that the values were sent
	char in_buffer [50];
	cerr<< "A.L.E: waiting for a reply ..." << endl;
	fgets (in_buffer, 50, p_fin);
	char * token = strtok (in_buffer,",\n");
	b_send_screen_matrix = atoi(token);
	token = strtok (NULL,",\n");
	b_send_console_ram = atoi(token);
	token = strtok (NULL,",\n");
	i_skip_frames_num = atoi(token);
	i_skip_frames_counter = i_skip_frames_num;
	cerr << "A.L.E: send_screen_matrix is: " << b_send_screen_matrix << endl;
	cerr << "A.L.E: send_console_ram is: " << b_send_console_ram << endl;
	cerr << "A.L.E: i_skip_frames_num is: " << i_skip_frames_num	<< endl;
	// Initialize our copy of frame_buffer 
	pi_old_frame_buffer = new int [i_screen_width * i_screen_height];
	for (int i = 0; i < i_screen_width * i_screen_height; i++) {
		pi_old_frame_buffer[i] = -1;
	}

}
        
/* *********************************************************************
    Deconstructor
 ******************************************************************** */
FIFOController::~FIFOController() {
	if (pi_old_frame_buffer != NULL) 
		delete [] pi_old_frame_buffer;
	if (p_fout != NULL) 
		fclose(p_fout);
	if (p_fin != NULL) 
		fclose(p_fin);

}
        
/* *********************************************************************
    This is called on every iteration of the main loop. It is resposible 
    passing the framebuffer and the RAM content to whatever AI module we 
    are using, and applying the returned actions.
 * ****************************************************************** */
void FIFOController::update() {
	Action player_a_action, player_b_action;
	// 0- See if we are skipping this frame
	if (i_skip_frames_counter < i_skip_frames_num) {
		// skip this frame
		i_skip_frames_counter++;
		if (e_previous_a_action == RESET || e_previous_b_action == RESET ) {
			player_a_action = PLAYER_A_NOOP;
			player_b_action = PLAYER_B_NOOP;
			e_previous_a_action = PLAYER_A_NOOP;
			e_previous_b_action = PLAYER_B_NOOP;
		} else {
			player_a_action = e_previous_a_action;
			player_b_action = e_previous_b_action;
		}
	} else {
		// don't skip this frame
		i_skip_frames_counter = 0;
		// 1- Send the updated pixels in the screen through the pipe
		string final_str = "";
		if (b_send_console_ram) {
			// 1.1 - Get the ram content (128 bytes)
			for(int i = 0; i< 128; i++) {
				char buffer[5];
				int ram_byte = read_ram(i);
				sprintf (buffer, "%03i", ram_byte);
				final_str += buffer;
			}
		}
		if (b_send_screen_matrix) {
			// The next section is taken from FrameBufferSoft
			for (int i = 0; i < i_screen_width * i_screen_height; i++) {
				uInt8 v = pi_curr_frame_buffer[i];
				if (v != pi_old_frame_buffer[i]) {
					char buffer[50];
					int ind_j = i / i_screen_width;
					int ind_i = i - (ind_j * i_screen_width);
					sprintf (buffer, "%03i%03i%03i", ind_i, ind_j, v);
					final_str += buffer;
					pi_old_frame_buffer[i] = v;
				}
			}
		} else {
			final_str += "NADA";
		}
		final_str += "\n\0";
		fputs(final_str.c_str(), p_fout);
		fflush (p_fout);
		
		// 2- Read the new action from the pipe
		// the action is sent as player_a_action,player_b_action
		char in_buffer [50];
		fgets (in_buffer, 50, p_fin);
		char * token = strtok (in_buffer,",\n");
		player_a_action = (Action)atoi(token);
		token = strtok (NULL,",\n");
		player_b_action = (Action)atoi(token);
	}
	e_previous_a_action = player_a_action;
	e_previous_b_action = player_b_action;
	apply_action(p_global_event_obj, player_a_action, player_b_action);
}


