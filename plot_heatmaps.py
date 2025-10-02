import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

def correlation_heatmap(excel_file, sheet_name=0, output_file="correlation_heatmap.png"):
    # Load Excel
    df = pd.read_excel(excel_file, sheet_name=sheet_name)

    # Option 1: drop the first column (assumed to be file names)
    df_numeric = df.iloc[:, 2:]

    #df_numeric = df.select_dtypes(include='number')

    # Compute correlations
    corr = df_numeric.corr()**2

    # Plot heatmap
    plt.figure(figsize=(20, 14))
    sns.heatmap(corr, annot=False, fmt=".2f", cmap="coolwarm", cbar=True,
                square=True, linewidths=0, annot_kws={"size": 4})
    
    plt.xticks(ticks=np.arange(len(corr.columns)) + 0.5, labels=corr.columns, rotation=90, fontsize=3)
    plt.yticks(ticks=np.arange(len(corr.index)) + 0.5, labels=corr.index, fontsize=3)


    plt.title("Correlation Heatmap", fontsize=16, fontweight="bold")
    plt.tight_layout()

    # Save and show
    plt.savefig(output_file, dpi=300)
    plt.show()

# Example usage
if __name__ == "__main__":
    correlation_heatmap("forROIanalyses/roi_results_DLB.xlsx")