import pandas as pd
import audmetric as am
from matplotlib import pyplot as plt
import seaborn as sns
import audeer

df_truth = pd.read_csv('vtv_pv_truth.csv')
df_pred = pd.read_csv('vtv_pv_predicted.csv')

# Check mean absolute error for VtV and PV
mae_vtv = am.mean_absolute_error(df_truth.vtv, df_pred.vtv,)
mae_pv = am.mean_absolute_error(df_truth.pv, df_pred.pv)
print(f'Mean Absolute Error for VtV: {mae_vtv:.3f}, PV: {mae_pv:.3f}')

# check Pearson's for VtV and PV
pearson_vtv = am.pearson_cc(df_truth.vtv, df_pred.vtv)
pearson_pv = am.pearson_cc(df_truth.pv, df_pred.pv)
print(f'Pearson correlation for VtV: {pearson_vtv:.3f}, PV: {pearson_pv:.3f}')

df_plot_truth = pd.DataFrame({
    'VtV': df_truth.vtv,
    'pV': df_truth.pv})
df_plot_pred = pd.DataFrame({
    'VtV': df_pred.vtv,
    'pV': df_pred.pv})
df_plot_VtV = pd.DataFrame({
    'truth': df_truth.vtv,
    'pred': df_pred.vtv})
df_plot_pV = pd.DataFrame({
    'truth': df_truth.pv,
    'pred': df_pred.pv})

audeer.mkdir('images')
sns.scatterplot(data=df_plot_truth, x='pV',
                y='VtV', color='red', label='truth')
sns.scatterplot(data=df_plot_pred, x='pV', y='VtV', color='blue', label='pred')
plt.title(
    f'MAE pV {mae_pv:.3f}, VtV {mae_vtv:.3f}, Pearson pV {pearson_pv:.3f}, VtV {pearson_vtv:.3f}')
plt.savefig('images/vtv_pv_scatter.png')
plt.close()
plt.clf()

sns.regplot(data=df_plot_pV, x='truth', y='pred', color='blue', label='pred')
plt.title(f"pV: PCC: {pearson_pv:.3f}")
plt.savefig('images/pv_regression.png')
plt.close()
plt.clf()

sns.regplot(data=df_plot_VtV, x='truth', y='pred', color='blue', label='pred')
plt.title(f"VtV, PCC:{pearson_vtv:.3f}")
plt.savefig("images/vtv_regression.png")
plt.close()
plt.clf()
