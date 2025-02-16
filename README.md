Basic Stress Pattern Visualizations
Stress Patterns Plot

Shows the average body stress patterns throughout working hours (8 AM - 5 PM) for each team
Solid lines represent mean stress levels
Shaded areas around lines show standard deviation
Higher values indicate higher stress levels
Different colors represent different teams (DALMUIR, KILMALID, KB3)

Stress Patterns Heatmap

Displays stress levels across the day using color intensity
Darker colors typically indicate higher stress
Each row represents a different team
Helps identify peak stress periods and patterns across the day

Activity Distribution Plot

Shows how activity levels are distributed across the day
Stacked bars showing percentage of time spent in different activity levels:

Sedentary
Light
Moderate
Intense


Separated by team and time of day

Productivity Analysis
Productivity Metrics Plot

Shows six key metrics:

Monthly Volume by Site: Raw cask receipts and dispatches
Month-over-Month Changes: Percentage changes in volume
Year-to-Date Progress: Cumulative totals
Rolling Efficiency Metrics: 3-month average of dispatch/receipt ratio
Volume Volatility Analysis: Spread of monthly changes
YTD Receipts vs Dispatches Ratio: Overall efficiency trends



Productivity Correlation Plot

Two main sections:

Stress vs Receipts: Shows relationship between stress levels and cask receipts
Stress vs Efficiency: Shows relationship between stress levels and efficiency ratios


Each point represents a different time period
Helps identify if higher stress correlates with higher or lower productivity

Pattern Analysis
Daily Patterns Plot

Compares stress patterns between high and normal productivity periods
Shows how stress levels vary throughout the day
Helps identify if productive days have different stress patterns

Time Patterns Plot

Shows how stress and activity patterns differ between high and low productivity periods
Includes participation levels throughout the day
Helps identify optimal working patterns

Advanced Analysis
Break Analysis

Shows:

Break Duration Distribution: How long breaks typically last
Break Timing Patterns: When breaks usually occur
Stress Reduction During Breaks: How effective breaks are
Group Comparisons: How break patterns differ between teams



Peak Analysis

Displays:

Peak Distribution by Time: When stress peaks occur
Recovery Time Analysis: How long it takes to recover from peaks
Peak Characteristics: Intensity and frequency of stress peaks
Recovery Success Rates: How well teams recover from high stress



Group Analysis

Shows:

Consistency Scores by Group: How stable stress patterns are
Variability Metrics: Different types of variation in stress levels
Temporal Consistency: How patterns change throughout the day
Group Comparisons: Statistical differences between teams



Monthly Analysis
Monthly Summary Plot

Shows:

Monthly Productivity by Group: Overall output trends
Stress Levels vs Productivity: Relationship analysis
Monthly Stress Score Distribution: How stress varies month to month
Productivity-Stress Efficiency: How effectively stress translates to output



Monthly Comparison

Compares patterns between different months
Helps identify seasonal trends or improvements over time
Shows how stress and productivity patterns evolve

Participation and Coverage
Participation Heatmap

Shows when and how many team members are active
Helps identify coverage patterns and gaps
Useful for understanding team engagement levels

Temporal Pattern Analysis

Shows long-term patterns over weeks and months
Includes:

Weekly trends
Participation rates
Stress level trends
Activity level patterns


            "<b>How to read this dashboard:</b><br><br>" +
            "1. Top: Compare raw productivity and cumulative totals<br>" +
            "2. Second: See how stress levels relate to productivity<br>" +
            "3. Third: Identify when stress occurs during the day<br>" +
            "4. Bottom: Understand how groups structure their work"


analyze_productive_periods:
For each site/group, calculate the 75th percentile of receipts (this is the threshold_percentile parameter)
Any month where receipts are above this threshold for that site is considered a "high productivity" month
All other months are considered "normal productivity" months
The biometric data is then tagged based on which months it falls into


So for each time of day:

Take the mean biometric productivity during high productivity periods
Subtract the mean biometric productivity during normal productivity periods
Plot this difference

For example, if at 10:00:

During high productivity months, the mean biometric productivity is 65
During normal productivity months, the mean biometric productivity is 45
The difference would be 20 (65 - 45)

A positive value means biometric productivity was higher during high productivity periods
A negative value means biometric productivity was actually lower during high productivity periods

create_activity_distribution_plot

The black line (now made lighter with 'rgba(0,0,0,0.3)') represents the total "active" percentage throughout the day. Here's how it's calculated:
pythonCopyactive_pct = [
    sum(d[k] for k in ['light','moderate','intense'])/sum(d.values())*100 
    for d in group_data['activity_level']
]
This calculation:

For each time point, adds up the percentages of all "active" categories (light + moderate + intense activity)
Divides by the total of all categories (including sedentary) to get the percentage
Multiplies by 100 to convert to a percentage

So if at 10:00 AM we have:

sedentary: 60%
light: 20%
moderate: 15%
intense: 5%