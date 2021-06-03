import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import pickle
%matplotlib

#reading in results from pickle
infile = open('data/irodsPerformances_cadaver.out.pickle', 'rb')
davrodsRes = pickle.load(infile)
infile = open('data/irodsPerformances_python0.9.out.pickle', 'rb')
python9 = pickle.load(infile)
infile = open('data/irodsPerformances_icommands-python8.out.pickle', 'rb')
icommpythonRes = pickle.load(infile)
perf = davrodsRes + icommpythonRes + python9

#cleaning data
df = pd.DataFrame(perf)
df.columns = ['data', 'Performance in s', 'checksums', 'client']
df.loc[df['data'].str.contains('2GB'), 'data'] = '2GB'
df.loc[df['data'].str.contains('3GB'), 'data'] = '3GB'
df.loc[df['data'].str.contains('5GB'), 'data'] = '5GB'

df.loc[df['checksums']==True, 'checksums'] = ', -K'
df.loc[df['checksums']==False, 'checksums'] = ''
df['method'] = df['client'] + df['checksums']

groups = df[['Performance in s', 'data', 'method']].groupby(['method'])

x = np.arange(len(df['data'].unique()))
width = 0.1  # the width of the bars
fig, ax = plt.subplots()
rects1 = ax.bar(x - 2.5*width, 
                df['Performance in s'].iloc[groups.groups['icommands']].values, 
                width, label='icommands')
rects2 = ax.bar(x - 1.5*width, 
                df['Performance in s'].iloc[groups.groups['icommands, -K']].values,
                width, label='icommands -K')
rects3 = ax.bar(x - 0.5*width,
                df['Performance in s'].iloc[groups.groups['python-0.8.3']].values,
                width, label='python0.8')
rects4 = ax.bar(x,
                df['Performance in s'].iloc[groups.groups['python-0.8.3, -K']].values,
                width, label='python0.8 -K')
rects5 = ax.bar(x + 0.5*width,
                df['Performance in s'].iloc[groups.groups['python-0.9.0']].values,
                width, label='python0.9')
rects6 = ax.bar(x + 1.5*width,
                df['Performance in s'].iloc[groups.groups['python-0.9.0, -K']].values,
                width, label='python0.9 -K')
rects5 = ax.bar(x + 2.5*width,
                df['Performance in s'].iloc[groups.groups['webdav']].values,
                width, label='cadaver')
ax.set_ylabel('Time in seconds')
ax.set_title('Data transfer Performance')
ax.set_xticks(x)
ax.set_xticklabels(df['data'].unique())
ax.legend()
fig.tight_layout()
