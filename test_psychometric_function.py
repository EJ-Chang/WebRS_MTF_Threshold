#!/usr/bin/env python3
"""
Standalone Psychometric Function Testing Script

This script allows you to test the psychometric function plotting with your own data.
Simply place your CSV file in the same directory and run this script.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
import sys

def plot_psychometric_function(trial_data, filename=""):
    """Generate and display psychometric function from participant data"""
    if not trial_data:
        print("No trial data available for plotting")
        return
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(trial_data)
    
    print(f"\n=== Psychometric Function Analysis ===")
    if filename:
        print(f"Data file: {filename}")
    print(f"Total trials: {len(df)}")
    
    # Check required columns
    required_cols = ['stimulus_difference', 'is_correct']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"ERROR: Missing required columns: {missing_cols}")
        print(f"Available columns: {list(df.columns)}")
        return
    
    # Group by stimulus difference and calculate accuracy
    grouped = df.groupby('stimulus_difference').agg({
        'is_correct': ['count', 'sum', 'mean'],
        'reaction_time': 'mean' if 'reaction_time' in df.columns else lambda x: np.nan
    }).round(3)
    
    # Flatten column names
    if 'reaction_time' in df.columns:
        grouped.columns = ['n_trials', 'n_correct', 'accuracy', 'mean_rt']
    else:
        grouped.columns = ['n_trials', 'n_correct', 'accuracy']
        grouped['mean_rt'] = np.nan
    
    grouped = grouped.reset_index()
    
    # Filter out groups with very few trials (less than 2)
    grouped = grouped[grouped['n_trials'] >= 2]
    
    if len(grouped) == 0:
        print("WARNING: Not enough data points for psychometric function (need at least 2 trials per stimulus level)")
        return
    
    print(f"\nStimulus levels with sufficient data: {len(grouped)}")
    print("\nData by stimulus difference:")
    print(grouped.to_string(index=False))
    
    # Create the plot
    fig = go.Figure()
    
    # Add data points
    marker_color = grouped['mean_rt'] if not grouped['mean_rt'].isna().all() else 'blue'
    
    fig.add_trace(go.Scatter(
        x=grouped['stimulus_difference'],
        y=grouped['accuracy'],
        mode='markers+lines',
        marker=dict(
            size=grouped['n_trials'] * 3,  # Size represents number of trials
            color=marker_color,
            colorscale='Viridis' if not grouped['mean_rt'].isna().all() else None,
            showscale=True if not grouped['mean_rt'].isna().all() else False,
            colorbar=dict(title="Mean RT (s)") if not grouped['mean_rt'].isna().all() else None
        ),
        line=dict(width=2),
        name='Observed Accuracy',
        hovertemplate=
        'Stimulus Difference: %{x:.3f}<br>' +
        'Accuracy: %{y:.1%}<br>' +
        'Trials: %{text}<br>' +
        ('Mean RT: %{marker.color:.2f}s<extra></extra>' if not grouped['mean_rt'].isna().all() else '<extra></extra>'),
        text=grouped['n_trials']
    ))
    
    # Add threshold line (75% correct)
    fig.add_hline(
        y=0.75, 
        line_dash="dash", 
        line_color="red",
        annotation_text="75% Threshold"
    )
    
    # Estimate threshold (interpolation to 75% point)
    threshold_estimate = None
    if len(grouped) >= 2:
        try:
            # Sort by stimulus difference for proper interpolation
            sorted_data = grouped.sort_values('stimulus_difference')
            threshold_estimate = np.interp(0.75, sorted_data['accuracy'], sorted_data['stimulus_difference'])
            fig.add_vline(
                x=threshold_estimate,
                line_dash="dash",
                line_color="orange",
                annotation_text=f"Est. Threshold: {threshold_estimate:.3f}"
            )
        except Exception as e:
            print(f"Could not estimate threshold: {e}")
    
    # Update layout
    fig.update_layout(
        title="Psychometric Function - Brightness Discrimination",
        xaxis_title="Stimulus Difference (Brightness)",
        yaxis_title="Proportion Correct",
        yaxis=dict(range=[0, 1], tickformat='.0%'),
        width=800,
        height=600,
        showlegend=True
    )
    
    # Save plot as HTML
    output_file = f"psychometric_function_{filename.replace('.csv', '')}.html"
    fig.write_html(output_file)
    print(f"\nPlot saved as: {output_file}")
    
    # Display summary statistics
    print(f"\n=== Summary Statistics ===")
    print(f"Total Trials: {len(df)}")
    overall_accuracy = df['is_correct'].mean()
    print(f"Overall Accuracy: {overall_accuracy:.1%}")
    
    if 'reaction_time' in df.columns:
        avg_rt = df['reaction_time'].mean()
        print(f"Average RT: {avg_rt:.2f}s")
    
    if threshold_estimate is not None:
        print(f"75% Threshold: {threshold_estimate:.3f}")
    else:
        print("75% Threshold: Could not be estimated")
    
    # Show stimulus difference range and distribution
    print(f"\nStimulus Difference Range: {df['stimulus_difference'].min():.3f} - {df['stimulus_difference'].max():.3f}")
    print(f"Unique stimulus levels: {df['stimulus_difference'].nunique()}")
    
    return fig, grouped

def load_and_analyze_csv(csv_file):
    """Load CSV file and analyze psychometric function"""
    try:
        print(f"Loading data from: {csv_file}")
        df = pd.read_csv(csv_file)
        
        print(f"Data loaded successfully! Found {len(df)} trials.")
        print(f"Columns: {list(df.columns)}")
        
        # Convert DataFrame to trial data format
        trial_data = df.to_dict('records')
        
        # Generate psychometric function
        fig, grouped = plot_psychometric_function(trial_data, csv_file)
        
        return True
        
    except FileNotFoundError:
        print(f"ERROR: File '{csv_file}' not found.")
        return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def main():
    """Main function to run the psychometric function test"""
    print("=== Psychometric Function Testing Script ===")
    print("This script analyzes CSV data and generates psychometric function plots.")
    
    # Check for CSV files in current directory
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    if not csv_files:
        print("\nNo CSV files found in current directory.")
        print("Please add your experiment data CSV file to this folder and run again.")
        return
    
    print(f"\nFound {len(csv_files)} CSV file(s):")
    for i, file in enumerate(csv_files, 1):
        print(f"{i}. {file}")
    
    # If command line argument provided, use that file
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        if not target_file.endswith('.csv'):
            target_file += '.csv'
        
        if target_file in csv_files:
            load_and_analyze_csv(target_file)
        else:
            print(f"File '{target_file}' not found.")
    
    # Interactive mode if no arguments
    elif len(csv_files) == 1:
        print(f"\nAnalyzing: {csv_files[0]}")
        load_and_analyze_csv(csv_files[0])
    
    else:
        # Multiple files - let user choose
        try:
            choice = input(f"\nEnter file number (1-{len(csv_files)}) or filename: ").strip()
            
            # Try to parse as number
            try:
                file_idx = int(choice) - 1
                if 0 <= file_idx < len(csv_files):
                    load_and_analyze_csv(csv_files[file_idx])
                else:
                    print("Invalid file number.")
            except ValueError:
                # Try as filename
                if choice in csv_files:
                    load_and_analyze_csv(choice)
                elif choice + '.csv' in csv_files:
                    load_and_analyze_csv(choice + '.csv')
                else:
                    print(f"File '{choice}' not found.")
        
        except KeyboardInterrupt:
            print("\nOperation cancelled.")

if __name__ == "__main__":
    main()