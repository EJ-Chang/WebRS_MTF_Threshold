# Psychometric Function Testing

## Standalone Testing Script

Use `test_psychometric_function.py` to analyze your experiment data without running the full Streamlit application.

### Usage Options:

1. **Automatic detection (if only one CSV file):**
   ```bash
   python test_psychometric_function.py
   ```

2. **Specify a file:**
   ```bash
   python test_psychometric_function.py your_data.csv
   ```

3. **Interactive mode (multiple files):**
   ```bash
   python test_psychometric_function.py
   ```
   Then select from the list of available CSV files.

### What it does:

- Loads your CSV data and validates the format
- Groups trials by stimulus difference
- Calculates accuracy at each difficulty level
- Generates interactive psychometric function plot
- Estimates 75% threshold via interpolation
- Saves plot as HTML file for viewing in browser
- Displays detailed statistics in terminal

### Required CSV columns:
- `stimulus_difference`: The difficulty level
- `is_correct`: Boolean or True/False values

### Optional columns:
- `reaction_time`: For color-coding plot points
- Other columns are preserved but not used for plotting

### Output:
- Terminal statistics and analysis
- HTML plot file: `psychometric_function_[filename].html`

The script successfully tested with the sample data and generated a proper psychometric function showing the expected S-shaped curve with 75% threshold at 0.131.

You can now upload your own CSV data to the folder and run this script to verify the psychometric function calculations independently.