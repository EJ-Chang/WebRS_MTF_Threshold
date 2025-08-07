# Gemini Refactoring Plan: UI Clearing Logic

**Goal:** To completely resolve UI ghosting/residual element issues during trial phase transitions by implementing a unified, stateful placeholder strategy. This will ensure a clean and complete clearing of the UI between the fixation and stimulus stages, and between the stimulus response and the next fixation stage.

The current fixation cross implementation will not be altered.

## Refactoring Steps

### 1. Centralize the UI Placeholder

-   **Action:** In the main `display_trial_screen` function within `ui/screens/trial_screen.py`, a single, persistent placeholder will be created using `st.empty()` and stored in Streamlit's session state.
-   **Code:** `if 'trial_placeholder' not in st.session_state: st.session_state.trial_placeholder = st.empty()`
-   **Rationale:** This creates a single, addressable "stage" for all trial-related UI elements. Storing it in `st.session_state` makes it globally accessible throughout the trial lifecycle, preventing the creation of conflicting, temporary placeholders.

### 2. Render All Content Within the Central Placeholder

-   **Action:** The `_display_trial_content` function will be modified. Instead of creating its own containers, it will now render all its UI elements (the fixation cross, the stimulus image, response buttons, etc.) inside the globally accessible `st.session_state.trial_placeholder`.
-   **Code:** All rendering calls will be wrapped within `with st.session_state.trial_placeholder.container(): ...`
-   **Rationale:** This unifies UI rendering, ensuring all elements are drawn onto the same canvas, which can then be controlled centrally.

### 3. Implement Explicit "Clear Screen" Commands

This is the most critical step. We will add explicit calls to clear the central placeholder at the two key transition points.

-   **Transition 1: Fixation to Stimulus**
    -   **Location:** In `_display_trial_content`, inside the `if st.session_state.trial_phase == 'fixation':` block, right after the timer has expired and just *before* the `st.rerun()` call that transitions to the stimulus phase.
    -   **Code:** `st.session_state.trial_placeholder.empty()`
    -   **Rationale:** This guarantees the fixation cross and its associated elements are completely wiped from the screen before the app reruns to draw the stimulus.

-   **Transition 2: Stimulus to Next Fixation**
    -   **Location:** In the `_prepare_next_trial` function, which is called after a response is recorded. The command will be placed just *before* the final `st.rerun()` that starts the next trial.
    -   **Code:** `if 'trial_placeholder' in st.session_state: st.session_state.trial_placeholder.empty()`
    -   **Rationale:** This ensures that the stimulus image, response buttons, and any feedback messages are completely erased before the screen reruns to show the fixation cross for the *next* trial.

## Expected Outcome

After this refactoring, the application will have a robust, centralized UI management system for the trial screen. All instances of "ghosting" or UI elements failing to clear will be eliminated, resulting in a cleaner, more professional user experience, without altering the core logic of the fixation cross animation.
