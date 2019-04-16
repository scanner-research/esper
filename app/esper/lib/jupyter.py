# Matplotlib/seaborn config
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
matplotlib.rcParams['figure.figsize'] = (18, 8)
plt.rc("axes.spines", top=False, right=False)
sns.set_style('white')

from tqdm import tqdm_notebook as tqdm
