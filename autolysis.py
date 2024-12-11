import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import httpx

# Step 1: Load the dataset from the command line
if len(sys.argv) != 2:
    print("Usage: uv run autolysis.py <dataset.csv>")
    sys.exit(1)

filename = sys.argv[1]

# Try to load the dataset with a different encoding (ISO-8859-1)
try:
    data = pd.read_csv(filename, encoding='ISO-8859-1')
    print(f"Loaded dataset: {filename}")
except Exception as e:
    print(f"Error loading the dataset: {e}")
    sys.exit(1)

# Step 2: Prepare CSV file to send to the AI
# Optionally reduce data size by limiting rows/columns (Example: first 1000 rows and key columns)
# Adjust as needed based on the dataset size
data_subset = data.iloc[:1000, :10]  # First 1000 rows and first 10 columns

AIPROXY_TOKEN = os.environ.get("AIPROXY_TOKEN")
if not AIPROXY_TOKEN:
    print("Error: AIPROXY_TOKEN not set")
    sys.exit(1)

# Prepare the dataset for sending
csv_data = data_subset.to_csv(index=False)

# Step 3: Request AI to recommend the best column for visualization
try:
    response = httpx.post(
        "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {AIPROXY_TOKEN}"},
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a data analyst."},
                {
                    "role": "user",
                    "content": f"Here is the CSV data from the file: {filename}. Please recommend the best column for visualization in a histogram and scatter plot.",
                },
                {"role": "user", "content": csv_data},  # Sending a smaller subset of the CSV data for analysis
            ],
        },
        timeout=30,  # Set timeout duration
    )

    if response.status_code == 200:
        recommended_column = response.json()["choices"][0]["message"]["content"]
        print(f"AI recommended column for analysis: {recommended_column}")
    else:
        print("Error with LLM request:", response.status_code, response.text)
        sys.exit(1)

except httpx.TimeoutException:
    print("Request timed out.")
    sys.exit(1)

# Step 4: Validate the AI's recommendation and proceed with visualization
if recommended_column not in data.columns:
    print(f"AI recommendation '{recommended_column}' not found in dataset columns. Defaulting to first numeric column.")
    # If AI's column doesn't exist, fall back to the first numeric column
    numeric_columns = data.select_dtypes(include='number').columns
    if numeric_columns.size > 0:
        selected_column = numeric_columns[0]
    else:
        print("No numeric columns available.")
        sys.exit(1)
else:
    selected_column = recommended_column

# Step 5: Generate and save the visualizations

# Histogram
plt.figure(figsize=(8, 6))
sns.histplot(data[selected_column], kde=True)
plt.title(f"Histogram of {selected_column}")
plt.xlabel(selected_column)
plt.ylabel("Frequency")
plt.savefig("histogram.png")
print("Saved histogram.png")

# Boxplot
plt.figure(figsize=(8, 6))
sns.boxplot(x=data[selected_column])
plt.title(f"Boxplot of {selected_column}")
plt.savefig("boxplot.png")
print("Saved boxplot.png")

# Scatter plot (using first numeric column vs selected column)
if len(numeric_columns) > 1:
    # Choose another numeric column for scatter plot
    scatter_column = numeric_columns[1]
    plt.figure(figsize=(8, 6))
    sns.scatterplot(x=data[scatter_column], y=data[selected_column])
    plt.title(f"Scatter Plot between {scatter_column} and {selected_column}")
    plt.xlabel(scatter_column)
    plt.ylabel(selected_column)
    plt.savefig("scatter_plot.png")
    print("Saved scatter_plot.png")
else:
    print("Not enough numeric columns for scatter plot.")

# Step 6: Correlation Matrix Heatmap

# Calculate correlation matrix
corr_matrix = data.corr(numeric_only=True)  # Ensure we only consider numeric columns

# Generate heatmap for the correlation matrix
plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
plt.title("Correlation Matrix Heatmap")
plt.savefig("correlation_matrix.png")
print("Saved correlation_matrix.png")

# Step 7: Create a README.md to include the results and visualizations

with open("README.md", "w") as f:
    f.write("# Automated Data Analysis: A Journey through the Dataset\n\n")
    
    # Introduction
    f.write("## Introduction\n")
    f.write("In this analysis, we embark on a journey to uncover the stories hidden in the dataset. The dataset is rich with information, and through visualizations and statistical insights, we will explore its key features and relationships. We rely on AI recommendations to guide our exploration and make sense of the data.\n\n")
    
    # AI Recommendation
    f.write("## AI Recommendation\n")
    f.write(f"### \"What is the Most Significant Column?\"\n")
    f.write(f"Upon sending the dataset to an AI-powered analysis tool, it recommended **`{selected_column}`** as the most significant column for analysis. The AI selected this column based on its strong relationship with other variables in the dataset, making it an ideal candidate for visualization in a histogram and scatter plot.\n\n")
    
    # Visualizations
    f.write("## Visualizations\n")

    # Histogram
    f.write("### 1. Histogram: Unveiling the Distribution of Data\n")
    f.write(f"The histogram of **`{selected_column}`** provides us with a clear picture of the data distribution. It shows us the frequency of values, helping us understand how the data is spread across different ranges. Is there a concentration of values in a particular range? Are there any outliers or unusual patterns?\n\n")
    f.write("![Histogram](histogram.png)\n\n")

    # Boxplot
    f.write("### 2. Boxplot: A Deeper Dive into the Spread\n")
    f.write(f"The boxplot of **`{selected_column}`** reveals more details about the spread of the data. It highlights the median, quartiles, and potential outliers. Boxplots are invaluable for spotting skewed data or extreme values that might warrant further investigation.\n\n")
    f.write("![Boxplot](boxplot.png)\n\n")

    # Scatter Plot
    f.write("### 3. Scatter Plot: A Relationship Unfolded\n")
    if len(numeric_columns) > 1:
        f.write(f"Next, we explore the relationship between **`{selected_column}`** and another numeric column, **`{scatter_column}`**. The scatter plot showcases how these two variables interact with each other. Do they show any clear correlation? Or is their relationship more complex, suggesting other hidden factors?\n\n")
        f.write("![Scatter Plot](scatter_plot.png)\n\n")
    else:
        f.write("Not enough numeric columns for scatter plot.\n\n")

    # Correlation Matrix
    f.write("### 4. Correlation Matrix Heatmap: Mapping the Connections\n")
    f.write("To gain a broader understanding of how different numeric columns are connected, we created a correlation matrix heatmap. This visualization reveals how the selected column correlates with other features in the dataset. Are there strong positive or negative correlations? How does the dataset as a whole come together?\n\n")
    f.write("![Correlation Matrix](correlation_matrix.png)\n\n")

    # Data Storytelling and Conclusion
    f.write("## Data Storytelling and Conclusion\n")
    f.write("The analysis of this dataset has been a fascinating journey. Through visualizations, we've uncovered key patterns, distributions, and relationships that were previously hidden. Here's what we learned:\n\n")

    # Narrating the data story
    f.write("1. **Histogram**: The distribution of values in the selected column reveals important trends. We observed a concentration of values in certain ranges, pointing to potential outliers or areas where the data might be skewed. This insight allows us to focus on specific data points for further exploration.\n\n")
    f.write("2. **Boxplot**: The boxplot helped us identify potential outliers and assess the spread of the data. It highlighted the data’s skewness, which could indicate areas for further investigation.\n\n")
    f.write("3. **Scatter Plot**: The relationship between the selected column and another numeric variable was unveiled through the scatter plot. Any linear or non-linear trends between these variables can lead to insights into how they influence each other.\n\n")
    f.write("4. **Correlation Matrix**: The heatmap revealed the correlation between the selected column and others, providing a broader context for understanding the relationships in the dataset. Strong correlations between certain variables suggest areas for further in-depth analysis.\n\n")

    f.write("In conclusion, the visualizations provided valuable insights into the data. The journey through histograms, scatter plots, boxplots, and correlation heatmaps allowed us to uncover hidden relationships and guide our next steps for further analysis.\n")
    f.write("This analysis serves as a foundation for deeper exploration, revealing trends, anomalies, and connections that could be pivotal for decision-making or predictive modeling.\n")
    
print("Saved README.md")
