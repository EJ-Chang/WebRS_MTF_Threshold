"""
Exp_MTF_Psychometric_YN.py

This script implements a non-adaptive psychophysical experiment to estimate subjective clarity threshold, with stimulus images presented at different MTF levels.

Experimental design:
- Single-interval Y/N judgment task
- Participants view a single image and judge whether it is "clear"
- MTF levels from 10% to 90%, in 10% steps
- Each MTF level is repeated 10 times (total 90 trials)
- Responses and reaction times are recorded to a CSV file

Note: This script does not use staircase or adaptive methods.
Data can be used for offline fitting of psychometric functions.

Author: EJ
Last reviewed: 2025-06
"""
 
import os
import numpy as np
from psychopy import visual, core, event, gui, data, monitors
from datetime import datetime
import csv
import cv2

def get_project_root():
    """Get the absolute path to the project root directory.
    
    Returns:
        str: Absolute path to the project root directory
    """
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to reach the project root
    return os.path.dirname(script_dir)

# Create random number generator
rng = np.random.default_rng(seed=int(datetime.now().timestamp()))


def create_window():
    """Create and configure the experiment window.

    Returns:
        visual.Window: Configured PsychoPy window object
    """
    win = visual.Window(
        size=[1920, 1080],
        fullscr=False,  # Not fullscreen mode
        screen=0,
        winType='pyglet',
        allowGUI=True,  # Allow GUI operation
        allowStencil=False,
        monitor='testMonitor',
        color=[0.5, 0.5, 0.5],
        colorSpace='rgb',
        units='pix',
        useFBO=True,
        waitBlanking=True,
        useRetina=True,
        multiSample=False
    )

    win.winHandle.activate()
    win.winHandle.set_visible(True)
    win.winHandle.set_vsync(True)
    return win


def create_stimuli(win):
    """Create the stimuli used in the experiment.

    Args:
        win (visual.Window): PsychoPy window object

    Returns:
        tuple: Contains fixation, trial number, instruction, prompt, rest text, and end text stimuli
    """
    # Set default font
    default_font = 'Arial'
    
    fixation = visual.TextStim(
        win, 
        text='+', 
        height=50, 
        color='white', 
        font=default_font,
        fontFiles=[]
    )
    
    # Trial number display (updated dynamically during experiment)
    trial_number = visual.TextStim(
        win,
        text='',
        height=40,
        color='white',
        pos=(0, 50),  # Displayed above fixation
        font=default_font,
        fontFiles=[]
    )
    
    # Instruction (visual prompt, English retained)
    instruction = visual.TextStim(
        win,
        text='You will see an image.\n Decide if it is clear or not.\nY = Yes, N = No\n\nPress SPACE to start.',
        height=30,
        color='white',
        font=default_font,
        fontFiles=[]
    )
    
    # Choice prompt (visual prompt, English retained)
    prompt = visual.TextStim(
        win,
        text='Is this image clear?\nY = Yes, N = No',
        height=30,
        color='white',
        font=default_font,
        fontFiles=[]
    )
    
    # Break prompt
    rest_text = visual.TextStim(
        win,
        text='Break time.\nPress SPACE to continue.',
        height=30,
        color='white',
        font=default_font,
        fontFiles=[]
    )
    
    # End prompt
    end_text = visual.TextStim(
        win,
        text='End of experiment.\nPress any key to exit.',
        height=30,
        color='white',
        font=default_font,
        fontFiles=[]
    )
    
    return fixation, trial_number, instruction, prompt, rest_text, end_text


def load_stimuli(stimuli_dir):
    """Load all pre-processed image stimuli into memory.

    Args:
        stimuli_dir (str): Path to the stimulus image folder

    Raises:
        FileNotFoundError: If the stimulus folder or image file is not found

    Returns:
        dict: Dictionary with MTF value as key and corresponding image array as value
    """
    if not os.path.exists(stimuli_dir):
        raise FileNotFoundError(f"Stimulus image directory not found: {stimuli_dir}\nPlease run preprocess_mtf_images.py to generate images first.")
    
    stimuli = {}
    for filename in os.listdir(stimuli_dir):
        if filename.startswith('mtf_') and filename.endswith('.png'):
            mtf_value = int(filename[4:7])  # Extract MTF value from filename
            filepath = os.path.join(stimuli_dir, filename)
            # Directly load image into memory
            img = cv2.imread(filepath)
            if img is None:
                raise FileNotFoundError(f"Cannot load image: {filepath}")
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = img.astype(float) / 255.0
            stimuli[mtf_value] = img
    
    if not stimuli:
        raise FileNotFoundError(f"No MTF stimulus images found in directory {stimuli_dir}")
    
    return stimuli


def create_image_stimuli(win, img_stimuli, mtf_value):
    """Get the image stimulus array for the specified MTF value.

    Args:
        win (visual.Window): PsychoPy window object
        img_stimuli (dict): Dictionary of image stimuli, key is MTF value
        mtf_value (int): Specified MTF level

    Returns:
        ndarray: Image array corresponding to the MTF level
    """
    return img_stimuli[mtf_value]


def run_clarity_yn_experiment():
    """Run the main experiment procedure (clarity Y/N task)."""
    # Get project root directory
    project_root = get_project_root()
    
    # Experiment parameters
    mtf_values = list(range(10, 95, 10))  # 10%, 20%, ..., 90%
    trials_per_mtf = 10  # Each MTF value presented 10 times

    # Experiment info dialog
    exp_info = {
        'subject': '001',
        'session': '001',
        'stimuli_dir': os.path.join(project_root, 'mtf_stimuli')  # 使用絕對路徑
    }
    dlg = gui.DlgFromDict(exp_info, title='MTF Threshold Experiment')
    if not dlg.OK:
        core.quit()

    # Create window and stimuli
    win = create_window()
    fixation, trial_number, instruction, prompt, rest_text, end_text = create_stimuli(win)

    try:
        # Load pre-processed images into memory
        stimuli_images = load_stimuli(exp_info['stimuli_dir'])
    except FileNotFoundError as e:
        print(f"Error: {e}")
        win.close()
        core.quit()
        return

    # Create PsychoPy ImageStim objects for each MTF value
    img_stimuli = {}
    for mtf_value, img_array in stimuli_images.items():
        filepath = os.path.join(exp_info['stimuli_dir'], f'mtf_{mtf_value:03d}.png')
        img_stimuli[mtf_value] = visual.ImageStim(
            win,
            image=filepath,
            size=[960, 1080],
            units='pix',
            interpolate=False
        )

    # Prepare trial list: each MTF value repeated trials_per_mtf times, shuffled
    trial_list = []
    for mtf in mtf_values:
        if mtf in img_stimuli:
            trial_list.extend([mtf] * trials_per_mtf)
    rng.shuffle(trial_list)

    # Create data file in data directory
    data_dir = os.path.join(project_root, 'data')  # 使用絕對路徑
    os.makedirs(data_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = os.path.join(data_dir, f"MTF_Threshold_{exp_info['subject']}_{timestamp}.csv")
    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['trial', 'mtf_value', 'response', 'response_time'])

    # Show instruction (English visual prompt)
    instruction.setText('You will see an image.\nIs it clear?\nY / ← = Yes, N / → = No\n\nPress SPACE to start.')
    instruction.draw()
    win.flip(clearBuffer=True)
    event.clearEvents()
    event.waitKeys(keyList=['space'])

    # Update prompt text as well
    prompt.setText('Is this image clear?\nY / ← = Yes, N / → = No')

    # Main experiment loop
    trial_count = 0
    for mtf_value in trial_list:
        trial_count += 1

        # Break every 20 trials
        if trial_count > 1 and (trial_count - 1) % 20 == 0:
            rest_text.draw()
            win.flip(clearBuffer=True)
            event.clearEvents()
            event.waitKeys(keyList=['space'])

        # Show trial number (in English)
        trial_number.setText(f'Trial: {trial_count}')
        trial_number.draw()
        win.flip(clearBuffer=True)
        core.wait(1)

        # Show fixation
        fixation.draw()
        win.flip(clearBuffer=True)
        core.wait(0.5)

        # Show image stimulus
        img_stimuli[mtf_value].draw()
        win.flip(clearBuffer=True)
        core.wait(1)

        # Show choice prompt (English visual prompt)
        prompt.draw()
        win.flip(clearBuffer=True)

        # Wait for response
        event.clearEvents()
        start_time = core.getTime()
        response_key = None
        while True:
            keys = event.getKeys(keyList=['y', 'n', 'left', 'right', 'escape'])
            if keys:
                response_time = core.getTime() - start_time
                if 'escape' in keys:
                    win.close()
                    core.quit()
                    return
                
                # Take only the first valid key
                response_key = keys[0]
                break
            core.wait(0.001)
            win.winHandle.activate()

        # Convert response to value: y=1 (clear), n=0 (not clear)
        response_value = 1 if response_key in ['y', 'left'] else 0

        # Record data
        with open(filename, 'a', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow([
                trial_count,
                mtf_value,
                response_value,
                f'{response_time:.3f}'
            ])

        core.wait(0.5)

    # Show end message
    end_text.draw()
    win.flip(clearBuffer=True)
    event.clearEvents()
    event.waitKeys()

    print(f"\nExperiment completed. Data saved to {filename}")

    win.close()
    core.quit()


if __name__ == "__main__":
    run_clarity_yn_experiment()