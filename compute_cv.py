import pandas as pd

# Load your Excel file
file_path = "forROIanalyses/roi_results_DLB.xlsx"  # replace with your file path
df = pd.read_excel(file_path)

# If your Excel has a column for subject IDs, drop it for CV calculation
# For example, assume the first column is 'SubjectID'
roi_data = df.iloc[:, 2:]  # all columns except the first

# Compute mean and standard deviation for each ROI
roi_mean = roi_data.mean()
roi_std = roi_data.std()

# Compute coefficient of variation (CV = std / mean)
roi_cv = roi_std / roi_mean

# Sort ROIs by CV (lowest first)
roi_cv_sorted = roi_cv.sort_values()

# Display results
print("ROIs sorted by coefficient of variation (lowest to highest):")
print(roi_cv_sorted)

# Optionally, save to Excel
#roi_cv_sorted.to_excel("roi_cv_sorted.xlsx", header=["CV"])
