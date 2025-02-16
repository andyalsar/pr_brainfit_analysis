import pandas as pd
import numpy as np
from scipy import stats

def calculate_consistency_scores(df):
    """Calculate consistency scores for each group."""
    consistency_scores = {}
    
    for group in df['standardized_group'].unique():
        group_data = df[df['standardized_group'] == group]
        
        # Calculate day-to-day consistency
        daily_stats = group_data.groupby('date').agg({
            'stress_score': ['mean', 'std', 'count'],
            'heart_rate': ['mean', 'std']
        })
        
        # Calculate coefficient of variation
        cv_stress = (daily_stats['stress_score']['std'] / daily_stats['stress_score']['mean']).mean()
        cv_hr = (daily_stats['heart_rate']['std'] / daily_stats['heart_rate']['mean']).mean()
        
        # Calculate temporal consistency
        temporal_consistency = group_data.groupby(
            group_data['local_time'].dt.hour
        )['stress_score'].std().mean()
        
        consistency_scores[group] = {
            'cv_stress': cv_stress,
            'cv_heart_rate': cv_hr,
            'temporal_consistency': temporal_consistency,
            'daily_variation': daily_stats['stress_score']['std'].mean()
        }
    
    return consistency_scores

def identify_outliers(df, method='iqr'):
    """Identify outliers in group data."""
    outliers = {}
    
    for group in df['standardized_group'].unique():
        group_data = df[df['standardized_group'] == group]
        
        if method == 'iqr':
            Q1 = group_data['stress_score'].quantile(0.25)
            Q3 = group_data['stress_score'].quantile(0.75)
            IQR = Q3 - Q1
            
            outliers[group] = group_data[
                (group_data['stress_score'] < (Q1 - 1.5 * IQR)) |
                (group_data['stress_score'] > (Q3 + 1.5 * IQR))
            ]
        elif method == 'zscore':
            z_scores = stats.zscore(group_data['stress_score'])
            outliers[group] = group_data[abs(z_scores) > 3]
    
    return outliers


def compare_group_variability(df):
    """Compare variability between groups."""
    if df is None or df.empty:
        return {}  # Return empty dict instead of None
        
    comparisons = {}
    
    # Calculate various variability metrics
    for group in df['standardized_group'].unique():
        group_data = df[df['standardized_group'] == group]
        
        if len(group_data) == 0:
            continue
            
        # Intraday variability
        intraday_var = group_data.groupby('date')['stress_score'].std().mean()
        if pd.isna(intraday_var):
            intraday_var = 0
            
        # Interday variability
        daily_means = group_data.groupby('date')['stress_score'].mean()
        interday_var = daily_means.std() if len(daily_means) > 1 else 0
        
        # User-to-user variability
        user_means = group_data.groupby('user_id')['stress_score'].mean()
        user_var = user_means.std() if len(user_means) > 1 else 0
        
        # Calculate stability score (avoid log(0))
        stability = 1 / (1 + np.log1p(intraday_var + interday_var + 1e-10))
        
        comparisons[group] = {
            'intraday_variability': float(intraday_var),
            'interday_variability': float(interday_var),
            'user_variability': float(user_var),
            'stability_score': float(stability)
        }
    
    # Perform statistical tests between groups only if we have at least 2 groups
    groups = list(df['standardized_group'].unique())
    if len(groups) >= 2:
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                group1_data = df[df['standardized_group'] == groups[i]]['stress_score']
                group2_data = df[df['standardized_group'] == groups[j]]['stress_score']
                
                if len(group1_data) > 0 and len(group2_data) > 0:
                    try:
                        # Levene's test for equality of variances
                        stat, p_value = stats.levene(group1_data, group2_data)
                        
                        comparisons[f'{groups[i]}_vs_{groups[j]}'] = {
                            'levene_statistic': float(stat),
                            'p_value': float(p_value)
                        }
                    except Exception as e:
                        print(f"Warning: Could not compute Levene test for {groups[i]} vs {groups[j]}: {str(e)}")
                        comparisons[f'{groups[i]}_vs_{groups[j]}'] = {
                            'levene_statistic': 0.0,
                            'p_value': 1.0
                        }
    
    return comparisons

