import json
import re
import matplotlib.pyplot as plt
import numpy as np

def calculate_and_plot_scores(json_path, output_file_task="scores_plot_tasks.png", output_file_overall="scores_plot_overall.png"):
    """
    This function calculates average original and improved scores per task and overall,
    and generates two bar plots:
    1. Average Original vs Improved Scores per Task
    2. Overall Average Original vs Improved Scores
    """
    # Load the JSON file
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    avg_scores = []
    
    for outer_element in data:
        original_scores = []
        improved_scores = []
        
        # Each outer_element is a list of dictionaries
        for entry in outer_element:
            # Parse original score
            original_score_data = entry.get("original_score", {})
            original_score_str = original_score_data.get("score", None)
            original_val = parse_score(original_score_str)
            if original_val is not None:
                original_scores.append(original_val)
            
            # Parse improved score
            improved_score_data = entry.get("improved_score", {})
            improved_score_str = improved_score_data.get("score", None)
            improved_val = parse_score(improved_score_str)
            if improved_val is not None:
                improved_scores.append(improved_val)
        
        # Compute averages for this task (outer element)
        avg_original = sum(original_scores) / len(original_scores) if original_scores else None
        avg_improved = sum(improved_scores) / len(improved_scores) if improved_scores else None
        
        avg_scores.append((avg_original, avg_improved))
    
    # Filter out tasks where either score is None
    filtered_scores = [(o, i) for (o, i) in avg_scores if o is not None and i is not None]
    
    # Create a grouped bar plot for individual tasks
    plot_individual_tasks(filtered_scores, output_file_task)
    
    # Calculate overall averages
    overall_avg_original, overall_avg_improved = calculate_overall_average(avg_scores)
    
    # Create a bar plot for overall averages
    plot_overall_average(overall_avg_original, overall_avg_improved, output_file_overall)

def plot_individual_tasks(filtered_scores, output_file):
    """
    Plots a grouped bar chart comparing average original and improved scores per task.
    """
    n_tasks = len(filtered_scores)
    x = np.arange(n_tasks)
    width = 0.35  # width of the bars
    
    original_vals = [fs[0] for fs in filtered_scores]
    improved_vals = [fs[1] for fs in filtered_scores]
    
    plt.figure(figsize=(14, 8))
    
    # Use a softer, less contrasting color palette
    bar1 = plt.bar(x - width/2, original_vals, width, label='Original', color='#98df8a')  # Soft Green
    bar2 = plt.bar(x + width/2, improved_vals, width, label='Improved', color='#aec7e8')  # Soft Blue
    
    plt.xlabel("Task Index", fontsize=14)
    plt.ylabel("Average Score", fontsize=14)
    plt.title("Average Original vs Improved Scores per Task", fontsize=16)
    plt.xticks(x, [f"Task {i}" for i in range(n_tasks)], rotation=45, fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Calculate and annotate differences centered above each pair of bars
    for i in range(n_tasks):
        original = original_vals[i]
        improved = improved_vals[i]
        diff = improved - original
        # Determine the maximum height of the two bars to position the annotation
        max_height = max(original, improved)
        # Position the text slightly above the taller bar
        plt.text(x[i], max_height + 0.02, f"{diff:+.2f}", ha='center', va='bottom', fontsize=10, color='black')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
    print(f"Individual task scores plot saved as {output_file}")

def plot_overall_average(avg_original, avg_improved, output_file):
    """
    Plots a bar chart comparing overall average original and improved scores.
    """
    labels = ['Original', 'Improved']
    scores = [avg_original, avg_improved]
    colors = ['#98df8a', '#aec7e8']  # Softer colors for overall comparison
    
    plt.figure(figsize=(6, 6))
    bars = plt.bar(labels, scores, color=colors)
    
    plt.xlabel("Score Type", fontsize=10)
    plt.ylabel("Average Score", fontsize=10)
    plt.title("Overall Average Original vs Improved Scores", fontsize=14)
    plt.ylim(0, max(scores) + 0.1)  # Add some space above the highest bar for annotations
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Annotate bars with their scores
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.01, f"{height:.2f}", ha='center', va='bottom', fontsize=11, color='black')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
    print(f"Overall average scores plot saved as {output_file}")

def calculate_overall_average(avg_scores):
    """
    Calculates the overall average original and improved scores across all tasks.
    """
    original_total = 0
    improved_total = 0
    count = 0
    
    for (original, improved) in avg_scores:
        if original is not None and improved is not None:
            original_total += original
            improved_total += improved
            count += 1
    
    avg_original = original_total / count if count > 0 else None
    avg_improved = improved_total / count if count > 0 else None
    return avg_original, avg_improved

def parse_score(score_str):
    """
    Parses the score string to extract a float between 0 and 1.
    Supports formats like "[0.9]", "0.8", etc.
    Returns None if parsing fails.
    """
    # Return None if score is not provided
    if not score_str:
        return None
    
    # Regex to extract a floating point number between 0 and 1
    pattern = r'^\[?\s*(0(?:\.\d+)?|1(?:\.0+)?)\s*\]?$'
    match = re.match(pattern, score_str.strip())
    if match:
        val = float(match.group(1))
        return val
    return None

if __name__ == "__main__":
    json_path = "results/improved_results.json"
    calculate_and_plot_scores(json_path, 
                              output_file_task="scores_plot_tasks.png", 
                              output_file_overall="scores_plot_overall.png")
    # Calculate overall averages for printing
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    avg_scores = []
    for outer_element in data:
        for entry in outer_element:
            original_score_data = entry.get("original_score", {})
            original_score_str = original_score_data.get("score", None)
            original_val = parse_score(original_score_str)
            if original_val is not None:
                original_scores = [original_val]
            else:
                original_scores = []
            
            improved_score_data = entry.get("improved_score", {})
            improved_score_str = improved_score_data.get("score", None)
            improved_val = parse_score(improved_score_str)
            if improved_val is not None:
                improved_scores = [improved_val]
            else:
                improved_scores = []
            
            avg_scores.append((original_val, improved_val))
    
    overall_avg_original, overall_avg_improved = calculate_overall_average(avg_scores)
    print(f"Overall Average Original Score: {overall_avg_original:.3f}")
    print(f"Overall Average Improved Score: {overall_avg_improved:.3f}")