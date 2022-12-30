import glob
import os
import subprocess
from datetime import datetime

import numpy as np
import pandas as pd

# %% Load old list with all movies, when exist
LIST_PATH = './Testing/movieFileList.csv'
LOG_PATH = './Testing/movieFileLog.csv'
COLLECTION_PATH = './Testing/MovieCollection'

# FIXME catch if there is no old file
moviesListOld = pd.read_csv(LIST_PATH, index_col=0,
                            dtype={'path': 'string', 'modificationTimestamp': np.float64, 'valid': 'string'})

# %% create the current list with all movies

# search all files inside collection path
# *.mkv means file name with .mkv extension
# TODO specify more filetypes
dir_path = r'{}/**/*.mkv'.format(COLLECTION_PATH)
movieListNew = []
for file in glob.glob(dir_path, recursive=True):
    movieListNew += [file]
moviesListNewDf = pd.DataFrame({'path': movieListNew})
moviesListNewDf['path'] = moviesListNewDf['path'].astype('string')
# save timestamps of files
moviesListNewDf['modificationTimestamp'] = moviesListNewDf['path'].apply(lambda x: os.path.getmtime(x))

# %% compare and calculate which files changed
mergeList = pd.merge(moviesListNewDf, moviesListOld, how='outer', indicator='Exist')
mergeList.sort_values(["path", "modificationTimestamp"], axis=0, ascending=True, inplace=True, ignore_index=True)
mergeList['modState'] = mergeList['path'].apply(lambda _: 'INVALID').astype('string')

mergeList.loc[:, 'modState'][mergeList['path'].duplicated()] = 'modified'
mergeList.drop_duplicates('path', keep='last', inplace=True)
print('The following files were modified:')
print(mergeList[mergeList['modState'] == 'modified']['path'].to_numpy())

# FIXME check if modified file has older date than before?
# FIXME check if there are other than two modified duplicate files?

mergeList.loc[:, 'modState'][
    (mergeList['Exist'] == 'left_only').mul(~mergeList['path'].duplicated(keep=False))] = 'added'
print('The following files were added:')
print(mergeList[mergeList['modState'] == 'added']['path'].to_numpy())

mergeList.loc[:, 'modState'][(mergeList['Exist'] == 'right_only').mul(
    ~mergeList['path'].duplicated(keep=False)).mul(mergeList['modState'] == 'INVALID')] = 'deleted'
print('The following files were deleted:')
print(mergeList[mergeList['modState'] == 'deleted']['path'].to_numpy())

print('The following files did not change:')
mergeList.loc[:, 'modState'][mergeList['Exist'] == 'both'] = 'unchanged'
print(mergeList[mergeList['modState'] == 'unchanged']['path'].to_numpy())

mergeList.drop('Exist', axis=1, inplace=True)

# %% check all files which changed
print('Checking files now...')

# TODO add multithreading
# TODO add progress-bar
# TODO add intermediate save-point

for i, f in mergeList.iterrows():
    if f.modState == 'added' or f.modState == 'modified':
        now = datetime.now()
        print(f'{now.strftime("%H:%M:%S")}: Check: {f.path}')
        mergeList.loc[i, 'valid'] = subprocess.run(
            ['ffmpeg', '-v', 'error', '-i', f['path'], '-map', '0:1', '-f', 'null', '-'],
            capture_output=True).stderr.decode('utf-8')
        if mergeList.loc[i, 'valid'] != '':
            print(f'Error in decode: {mergeList.loc[i, "valid"]}')

# %% store new list
print(f'\nCheck finished. You can find more information in the log file at {LOG_PATH}')
mergeList.to_csv(LOG_PATH)
mergeList[mergeList['modState'] != 'deleted'].to_csv(LIST_PATH)

# %% TODO add log-rotation
