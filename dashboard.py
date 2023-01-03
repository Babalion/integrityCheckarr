import os
import pathlib
import subprocess
from datetime import datetime

import dash
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from dash import dcc, html, dash_table, Input, Output, State

# %% Load old list with all movies, when exist
LIST_PATH = './Testing/movieFileList.csv'
# TODO add log-rotation
LOG_PATH = './Testing/movieFileLog.csv'
COLLECTION_PATH = '/home/chris/qnapts230/gemeinsamedaten/Filme/Kinofilme'

# FIXME catch if there is no old file
moviesListOld = pd.read_csv(LIST_PATH, index_col=0, keep_default_na=False,
                            dtype={'path': 'string', 'modificationTimestamp': np.float64, 'valid': 'string',
                                   'modState': 'string'})

moviesListOld['fileName'] = moviesListOld['path'].apply(lambda p: p.replace(COLLECTION_PATH + '/', ''))
moviesListOld['fileType'] = moviesListOld['path'].apply(lambda p: pathlib.Path(p).suffix)
moviesListOld['fileSizeGb'] = moviesListOld['path'].apply(lambda p: os.stat(p).st_size / (1024 ** 3))
moviesListOld['timeHr'] = moviesListOld['modificationTimestamp'].apply(
    lambda ts: datetime.fromtimestamp(ts).strftime("%m/%d/%Y, %H:%M:%S"))
moviesListOld['integrity'] = moviesListOld['valid'].apply(lambda v: 'ok' if v == '' else 'error')
# %% Create the app
app = dash.Dash()

# define layout constants
quarter_width = '24%'

# Create some data
labels = ['modified', 'added', 'deleted', 'unchanged']
values = [len(moviesListOld[moviesListOld['modState'] == 'modified'].index),
          len(moviesListOld[moviesListOld['modState'] == 'added'].index),
          len(moviesListOld[moviesListOld['modState'] == 'deleted'].index),
          len(moviesListOld[moviesListOld['modState'] == 'unchanged'].index)]

app.layout = html.Div(children=[
    # Add a header
    html.H1(children='Integrity Checkarr'),
    html.Div(children=[
        html.H2(f'Total number of movies: {len(moviesListOld.index)}'),
        html.H2(f'Total size: {np.round(moviesListOld.fileSizeGb.sum(), 1)}GB'),
    ], style={'width': '100%', 'display': 'inline-block'}),

    # Add a pie chart
    html.Div(children=[dcc.Graph(
        id='pie-chart-valid',
        figure={
            'data': [
                go.Pie(labels=list(moviesListOld.integrity.value_counts().to_dict().keys()),
                       values=moviesListOld.integrity.value_counts().to_list())
            ],
            'layout': {
                'title': 'File Integrity'
            }
        }
    )], style={'width': quarter_width, 'display': 'inline-block'}),

    # Add a pie chart
    html.Div(children=[dcc.Graph(
        id='pie-chart-file-status',
        figure={
            'data': [
                go.Pie(labels=list(moviesListOld.modState.value_counts().to_dict().keys()),
                       values=moviesListOld.modState.value_counts().to_list())
            ],
            'layout': {
                'title': 'File status'
            }
        }
    )], style={'width': quarter_width, 'display': 'inline-block'}),

    # Add a pie chart
    html.Div(children=[dcc.Graph(
        id='pie-chart-file-types',
        figure={
            'data': [
                go.Pie(labels=list(moviesListOld.fileType.value_counts().to_dict().keys()),
                       values=moviesListOld.fileType.value_counts().to_list())
            ],
            'layout': {
                'title': 'File Types'
            }
        }
    )], style={'width': quarter_width, 'display': 'inline-block'}),

    # Add a pie chart
    html.Div(children=[
        dcc.Graph(id='graph2', figure=px.histogram(moviesListOld.fileSizeGb.to_list())),
    ], style={'width': quarter_width, 'display': 'inline-block'}),

    html.Div([
        html.Button('Start integrity check', id='submit-val', n_clicks=0),
        html.Div(id='container-button-basic',
                 children='Enter a value and press submit')
    ], style={'width': quarter_width, 'display': 'inline-block'}),

    # Add a table
    dash_table.DataTable(
        id='table',
        columns=[
            {'name': 'Filename', 'id': 'filename'},
            {'name': 'Integrity', 'id': 'valid'},
            {'name': 'Status', 'id': 'status'},
            {'name': 'Modification Date', 'id': 'modification_date'},
            {'name': 'File Size (GB)', 'id': 'file_size'}
        ],
        style_cell={'textAlign': 'left',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                    'maxWidth': 100,
                    },
        editable=True,
        data=[{'filename': r.fileName,
               'valid': r.valid,
               'status': r.modState,
               'modification_date': r.timeHr,
               'file_size': np.round(r.fileSizeGb, 2),
               }
              for i, r in moviesListOld.iterrows()],
        style_data_conditional=[
            {
                'if': {
                    'column_id': 'file_size',
                },
                'textAlign': 'left'
            },
            {
                'if': {
                    'filter_query': '{status} = added',
                    'column_id': 'status'
                },
                'backgroundColor': 'green',
                'color': 'white'
            },
            {
                'if': {
                    'filter_query': '{valid} contains [',  # TODO check if ffmpeg errors always contain this bracket
                    # 'column_id': 'valid'
                },
                'backgroundColor': 'tomato',
                'color': 'white'
            },
            {
                'if': {
                    'filter_query': '{status} = deleted',
                    'column_id': 'status'
                },
                'backgroundColor': 'tomato',
                'color': 'white'
            },
            {
                'if': {
                    'filter_query': '{status} = modified',
                    'column_id': 'status'
                },
                'backgroundColor': 'blue',
                'color': 'white'
            },
        ],
    )

])


@app.callback(
    Output('container-button-basic', 'children'),
    Input('submit-val', 'n_clicks'),
)
def update_output(n_clicks):
    scriptpy = "main"
    p = subprocess.Popen(['pgrep', '-f', f'{scriptpy}.py'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    if len(out.strip()) == 0:  # script not launched yet
        if n_clicks > 0:  # after first click
            subprocess.Popen(['python', f'{scriptpy}.py'])
            return 'Script is running...'
        else:
            return 'Script is not yet launched.'


# def update_output(n_clicks, value):
#    print(f'button clicked with {n_clicks}')
#    if n_clicks > 0:
#        p = subprocess.Popen(['pgrep', '-f', f'{scriptpy}.py'], stdout=subprocess.PIPE)
#        out, err = p.communicate()
#
#        if len(out.strip()) == 0:
#            os.system(f"python {scriptpy}")


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
