/* *****************************************************************************
 * A.L.E (Atari 2600 Learning Environment)
 * Copyright (c) 2009-2010 by Yavar Naddaf
 * Released under GNU General Public License www.gnu.org/licenses/gpl-3.0.txt
 *
 * Based on: Stella  --  "An Atari 2600 VCS Emulator"
 * Copyright (c) 1995-2007 by Bradford W. Mott and the Stella team
 *
 * *****************************************************************************
 *  fifo_controller.h
 *
 *  The implementation of the FIFOController class, which is a subclass of 
 * GameConroller, and is resposible for sending the Screens/RAM content to 
 * whatever external program we are using through FIFO pipes, and apply the 
 * actions that are sent back
 **************************************************************************** */

#ifndef FIFO_CONTROLLER_H
#define FIFO_CONTROLLER_H


#include "common_constants.h"
#include "game_controller.h"

class FIFOController : public GameController {
    /* *************************************************************************
        This is a subclass of GameConroller, and is resposible for sending the 
        Screens/RAM content to whatever external program we are using through 
        FIFO pipes, and apply the actions that are sent back
.
        
        Instance Variables:
        - pi_old_frame_buffer;  // Copy of frame buffer. Used to detect and
                                // only send the changed pixels
        - p_fout;               // Output Pipe
        - p_fin;                // Input Pipe


    ************************************************************************* */
    public:
        /* *********************************************************************
            Constructor
         ******************************************************************** */
        FIFOController(OSystem* _osystem);
        
        /* *********************************************************************
            Deconstructor
         ******************************************************************** */
        virtual ~FIFOController();
        
        /* *********************************************************************
            This is called on every iteration of the main loop. It is resposible 
            passing the framebuffer and the RAM content to whatever AI module we 
            are using, and applying the returned actions.
         * ****************************************************************** */
        virtual void update();

    protected:
        int* pi_old_frame_buffer;   // Copy of frame buffer. Used to detect and
                                    // only send the changed pixels
        FILE* p_fout;               // Output Pipe
        FILE* p_fin;                // Input Pipe
};
#endif
