import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from numpy import select
from numpy.random import choice
from urllib.parse import quote
import json
import pandas as pd
import plotly.graph_objs as go
import plotly.plotly as py

from Credentials import credentials
from spotifyScrape import spotifyScrape

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

songs_df = pd.read_csv('all_songs.csv')
artist_averages = pd.read_csv('artist_averages.csv')
artist_averages['color'] = select([artist_averages.genre == 'country', artist_averages.genre == 'metal', artist_averages.genre == 'pop', artist_averages.genre == 'rap', artist_averages.genre == 'rock', artist_averages.genre == 'soul'],
                        ['rgb(255,0,0)', 'rgb(0,255,0)', 'rgb(0,0,255)', 'rgb(255,165,0)', 'rgb(0,165,255)', 'rgb(165,255,0)'],
                        default='rgb(0,0,0)')
metrics = ['acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'speechiness', 'valence']

# Dash App
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'Spotify Data Comparator'
server = app.server

app.layout = html.Div([

    html.Div([
        html.Div([
            html.H3([
                ' ',
                html.Img(src=app.get_asset_url('logo.png'), style={'height':'5%', 'width':'5%'}),
                ' Spotify Data Comparator | ',
                html.A('more projects', href='http://saisenberg.com', target='_blank', style={'color':'green', 'display':'inline-block', 'font-size':24}),
                ' | ',
                html.A('my github', href='https://github.com/saisenberg', target='_blank', style={'color':'green', 'display':'inline-block', 'font-size':24}),
            ], # H3 list
            style={'display':'inline-block'}),
        ]),
    ], style={'color':'green', 'background-color':'black'}),

    html.Div([
        html.H6('Genre:', style={'font-size':16}),
        dcc.Dropdown(
            id = 'genre-dropdown',
            options = [{'label':str(genre), 'value':str(genre)} for genre in sorted(list(songs_df.genre.unique()))],
            value = 'rap',
            clearable = False
        ), # Dropdown - genre
    ], style={'width':'15%', 'display':'inline-block', 'marginTop':10, 'marginLeft':10, 'marginBottom':10, 'marginRight':10}),

    html.Div([
        html.H6('Artist:', style={'font-size':16}),
        dcc.Dropdown(
            id = 'artist-dropdown',
        ), # Dropdown - artist
    ], style={'width':'15%', 'display':'inline-block', 'marginTop':10, 'marginLeft':10, 'marginBottom':10, 'marginRight':10}),

    html.Div([
        html.H6('Album(s):', style={'font-size':16}),
        dcc.Dropdown(
            id = 'album-dropdown',
            multi = True,
        ), # Dropdown - album
    ], style={'width':'36%', 'display':'inline-block', 'marginTop':10, 'marginLeft':10, 'marginBottom':10, 'marginRight':10}),

    html.Br(),

    html.Div([
        html.H6('X-axis metric:', style={'font-size':16}),
        dcc.Dropdown(
            id = 'x-axis-dropdown',
            options = [{'label':str(metric), 'value':str(metric)} for metric in metrics],
            value = 'danceability',
            clearable = False
        ), # Dropdown - x-axis metric
    ], style={'width':'15%', 'display':'inline-block', 'marginTop':0, 'marginLeft':10, 'marginBottom':10, 'marginRight':10}),

    html.Div([
        html.H6('Y-axis metric:', style={'font-size':16}),
        dcc.Dropdown(
            id = 'y-axis-dropdown',
            options = [{'label':str(metric), 'value':str(metric)} for metric in metrics],
            value = 'valence',
            clearable = False
        ), # Dropdown - y-axis metric
    ], style={'width':'15%', 'display':'inline-block', 'marginTop':0, 'marginLeft':10, 'marginBottom':10, 'marginRight':10}),

    html.Div([
        html.H6(' ', style={'display':'inline-block', 'marginTop':0, 'marginBottom':0}),
        html.A('What do these metrics mean?', href='https://developer.spotify.com/documentation/web-api/reference/tracks/get-audio-features/', target='_blank', style={'font-size':12, 'font-style':'italic', 'marginTop':0, 'marginBottom':10})
    ], style={'width':'25%', 'marginBottom':10}),

    html.Div([
        html.Div([
            html.H5([' Song/album comparison'], style={'display':'inline-block', 'font-size':22}),
        ]),
    ], style={'color':'green', 'background-color':'black'}),

    html.Div([
        html.Div([
            dcc.Graph(id='graph1')
        ], className='six columns'),
        html.Div([
            dcc.Graph(id='graph2')
        ], className='six columns')
    ], className='row'),

    html.Br(),

    html.Div([
        html.Div([
            dcc.Graph(id='graph3')
        ])
    ]),

    html.Div([
        html.Div([
            html.H5([' Artist comparison'], style={'display':'inline-block', 'font-size':22}),
        ]),
    ], style={'color':'green', 'background-color':'black'}),

    html.Br(),

    html.Div([
        html.Div([
            dcc.Graph(id='graph4', style={'height':'500px'})
        ])
    ]),

    html.Br(),

    html.Div([
        html.Div([
            html.H5([' Download artist data'], style={'display':'inline-block', 'font-size':22}),
        ]),
    ], style={'color':'green', 'background-color':'black'}),

    html.Div([
        html.H6('Artist (case-sensitive):', style={'font-size':16}),
        dcc.Input(
            id ='search-artist',
            type='text',
            style={'width':'90%'}
        ), # Input - artist
    ], style={'width':'18%', 'display':'inline-block', 'marginTop':10, 'marginLeft':10, 'marginBottom':10}),

    html.Button(id='search-button', n_clicks=0, children='SUBMIT'),
    html.A('DOWNLOAD', id='download-table', download='rawdata.csv', href='', target='_blank', style={'color':'green', 'display':'inline-block', 'marginLeft':10, 'marginRight':10}),
    html.H6(id='error-message', style={'color':'green', 'display':'inline-block', 'font-size':14, 'marginLeft':10, 'marginRight':10}),

    html.Div(id='hidden-album-colors', style={'display':'none'}),

    html.Hr(),
    html.Br()

], style={'font-family':'monospace', 'font-weight':'bold'} # div
) # app.layout


# Callbacks
@app.callback(
    Output('hidden-album-colors', 'children'),
    [Input('artist-dropdown', 'value')]
)
def set_album_colors(selected_artist):
    filtered_songs_df = songs_df[songs_df.artist_name == selected_artist]
    colors_dict = {album:f"rgb({choice(256)},{choice(256)},{choice(256)})" for album in filtered_songs_df.album_name.unique()}
    return(json.dumps(colors_dict))

@app.callback(
    Output('artist-dropdown', 'options'),
    [Input('genre-dropdown', 'value')]
)
def update_artist_dropdown(selected_genre):
    df = songs_df[songs_df.genre == selected_genre]
    artists = sorted(list(df.artist_name.unique()))
    return([{'label':artist, 'value':artist} for artist in artists])

@app.callback(
    Output('album-dropdown', 'options'),
    [Input('artist-dropdown', 'value')]
)
def update_album_dropdown(selected_artist):
    df = songs_df[songs_df.artist_name == selected_artist]
    albums = sorted(list(df.album_name.unique()))
    return([{'label':album, 'value':album} for album in albums])

@app.callback(
    Output('graph1', 'figure'),
    [Input('artist-dropdown', 'value'),
     Input('album-dropdown', 'value'),
     Input('x-axis-dropdown', 'value'),
     Input('y-axis-dropdown', 'value'),
     Input('hidden-album-colors', 'children')]
    ) # callback
def update_graph1(selected_artist, selected_album, selected_x_axis, selected_y_axis, colors_dict):
    filtered_songs_df = songs_df[songs_df.artist_name == selected_artist]
    if selected_album:
        filtered_songs_df = songs_df[songs_df.album_name.isin(selected_album)]
    colors_dict = json.loads(colors_dict)
    colors_col = list(filtered_songs_df['album_name'].map(colors_dict))
    traces = []
    for num, i in enumerate(filtered_songs_df.song_name):
        songs_df_by_song = filtered_songs_df[filtered_songs_df.song_name == i]
        traces.append(go.Scatter(
            name = i,
            x = songs_df_by_song[selected_x_axis],
            y = songs_df_by_song[selected_y_axis],
            mode = 'markers',
            opacity = 0.25,
            hoverlabel= {'namelength':-1},
            marker = {
                'size':12,
                'color':colors_col[num],
                'line':{'width':0.5, 'color':'white'}
            } # marker
        ) # go.Scatter
        ) # traces
    return{
        'data':traces,
        'layout':go.Layout(
            title = go.layout.Title(text='Song metrics', xref='paper', x=0, font={'size':18}),
            xaxis = {'title':selected_x_axis, 'range':[0, 1], 'tickvals':[0.2,0.4,0.6,0.8,1], 'showgrid':False, 'automargin':True, 'tickformat':'.2f',
                     'titlefont':{'size':18},
                     'tickfont':{'size':14}},
            yaxis = {'title':selected_y_axis, 'range':[0, 1], 'tickvals':[0.2,0.4,0.6,0.8,1], 'showgrid':False, 'automargin':True, 'tickformat':'.2f',
                     'titlefont':{'size':18},
                     'tickfont':{'size':14}},
            hovermode = 'closest',
            font = {'family':'Droid Sans, monospace', 'size':18},
            showlegend = False
        ) # go.Layout
    } # return

@app.callback(
    Output('graph2', 'figure'),
    [Input('artist-dropdown', 'value'),
    Input('x-axis-dropdown', 'value'),
    Input('y-axis-dropdown', 'value'),
    Input('hidden-album-colors', 'children')]
)
def update_graph2(selected_artist, selected_x_axis, selected_y_axis, colors_dict):
    filtered_songs_df = songs_df[songs_df.artist_name == selected_artist]
    filtered_songs_df = pd.merge(filtered_songs_df, filtered_songs_df.groupby('album_name')['duration_ms'].sum(), left_on='album_name', right_on='album_name').rename(columns={'duration_ms_x':'duration_ms', 'duration_ms_y':'total_album_ms'})
    album_averages = pd.DataFrame(index=filtered_songs_df.album_name.unique())
    for metric in [selected_x_axis, selected_y_axis]:
        new_col_name = 'weighted_' + metric
        filtered_songs_df[new_col_name] = filtered_songs_df[metric] * (filtered_songs_df['duration_ms']/filtered_songs_df['total_album_ms'])
        album_averages = pd.merge(album_averages, filtered_songs_df.groupby('album_name')[new_col_name].sum(), left_index=True, right_index=True)
    colors_dict = json.loads(colors_dict)
    colors_col = list(album_averages.index.map(colors_dict))
    traces = []
    for num, i in enumerate(album_averages.index):
        album_averages_by_album = album_averages[album_averages.index==i]
        traces.append(go.Scatter(
            name = i,
            x = album_averages_by_album['weighted_'+selected_x_axis],
            y = album_averages_by_album['weighted_'+selected_y_axis],
            mode = 'markers',
            opacity = 0.25,
            hoverlabel= {'namelength':-1},
            marker = {
                'size':12,
                'color':colors_col[num],
                'line':{'width':0.5, 'color':'white'}
            } # marker
        ) # go.Scatter
        ) # traces
    return{
        'data':traces,
        'layout':go.Layout(
            title = go.layout.Title(text='Album averages', xref='paper', x=0, font={'size':18}),
            xaxis = {'title':selected_x_axis, 'range':[0, 1], 'tickvals':[0.2,0.4,0.6,0.8,1], 'showgrid':False, 'automargin':True, 'tickformat':'.2f',
                     'titlefont':{'size':18},
                     'tickfont':{'size':14}},
            yaxis = {'title':selected_y_axis, 'range':[0, 1], 'tickvals':[0.2,0.4,0.6,0.8,1], 'showgrid':False, 'automargin':True, 'tickformat':'.2f',
                     'titlefont':{'size':18},
                     'tickfont':{'size':14}},
            hovermode = 'closest',
            font = {'family':'Droid Sans, monospace', 'size':18},
            showlegend = False
        ) # go.Layout
    } # return

@app.callback(
    Output('graph3', 'figure'),
    [Input('artist-dropdown', 'value')]
)
def update_graph3(selected_artist):
    filtered_songs_df = songs_df[songs_df.artist_name == selected_artist]
    filtered_songs_df = pd.merge(filtered_songs_df, filtered_songs_df.groupby('album_name')['duration_ms'].sum(), left_on='album_name', right_on='album_name').rename(columns={'duration_ms_x':'duration_ms', 'duration_ms_y':'total_album_ms'})
    album_averages = pd.DataFrame(filtered_songs_df.groupby('album_name')['album_release_date'].first())
    for metric in metrics:
        new_col_name = 'weighted_' + metric
        filtered_songs_df[new_col_name] = filtered_songs_df[metric] * (filtered_songs_df['duration_ms']/filtered_songs_df['total_album_ms'])
        album_averages = pd.merge(album_averages, filtered_songs_df.groupby('album_name')[new_col_name].sum(), left_index=True, right_index=True)
    album_averages['album_release_date'] = pd.to_datetime(album_averages.album_release_date)
    album_averages = album_averages.sort_values('album_release_date')
    traces = []
    for metric in metrics:
        trace = go.Scatter(
            x = album_averages['album_release_date'],
            y = album_averages['weighted_'+metric],
            mode = 'lines+markers',
            name = metric,
            opacity = 0.40
        )
        traces.append(trace)
    return{
        'data':traces,
        'layout':go.Layout(
            title = go.layout.Title(text='Album averages (over time)', xref='paper', x=0, font={'size':18}),
            xaxis = {'title':None, 'showgrid':False, 'automargin':True, 'tickangle':45,
                     'titlefont':{'size':18},
                     'tickfont':{'size':10},
                     'tickvals':list(album_averages.album_release_date),
                     'ticktext':list(album_averages.index)},
            yaxis = {'title':'metric', 'range':[-0.15, 1], 'tickvals':[0.2,0.4,0.6,0.8,1], 'showgrid':False, 'automargin':True, 'tickformat':'.2f',
                     'titlefont':{'size':18},
                     'tickfont':{'size':14}},
            font = {'family':'Droid Sans, monospace', 'size':18},
        )
    }

@app.callback(
    Output('graph4', 'figure'),
    [Input('x-axis-dropdown', 'value'),
     Input('y-axis-dropdown', 'value')]
)
def update_graph4(selected_x_axis, selected_y_axis):
    traces = []
    for genre in sorted(list(artist_averages.genre.unique())):
        artist_averages_by_genre = artist_averages[artist_averages['genre'] == genre]
        traces.append(go.Scatter(
            name = genre,
            x = artist_averages_by_genre['total_artist_weighted_'+selected_x_axis],
            y = artist_averages_by_genre['total_artist_weighted_'+selected_y_axis],
            mode = 'markers',
            marker = {'size':12, 'color':artist_averages_by_genre.color, 'opacity':0.25},
            text = list(artist_averages_by_genre.artist_name)
            ) # go.Scatter
        ) # traces

    return{
        'data':traces,
        'layout':go.Layout(
            title = go.layout.Title(text='Artist metrics', xref='paper', x=0, font={'size':18}),
            xaxis = {'title':selected_x_axis, 'range':[0, 1], 'tickvals':[0.2,0.4,0.6,0.8,1], 'showgrid':False, 'automargin':True, 'tickformat':'.2f',
                     'titlefont':{'size':18},
                     'tickfont':{'size':14}},
            yaxis = {'title':selected_y_axis, 'range':[0, 1], 'tickvals':[0.2,0.4,0.6,0.8,1], 'showgrid':False, 'automargin':True, 'tickformat':'.2f',
                     'titlefont':{'size':18},
                     'tickfont':{'size':14}},
            hovermode = 'closest',
            font = {'family':'Droid Sans, monospace', 'size':18},
            showlegend = True
        )
    }


@app.callback(
    Output('download-table', 'href'),
    [Input('search-button', 'n_clicks')],
    [State('search-artist', 'value')]
)
def scrape_spotify(n_clicks, search_artist):
    if n_clicks > 0:
        try:
            search_result = spotifyScrape(client_id=credentials['client_id'], client_secret=credentials['client_secret'], artist_name=search_artist, verbose=0)
        except:
            return('Error: Please enter an artist to search')
        if type(search_result) == str:
            return(search_result)
        elif type(search_result) == pd.core.frame.DataFrame:
            csv_string = search_result.to_csv(index=False, encoding='utf-8')
            csv_string = 'data:text/csv;charset=utf-8,' + quote(csv_string)
            return(csv_string)

@app.callback(
    Output('error-message', 'children'),
    [Input('search-button', 'n_clicks'),
     Input('download-table', 'href')],
    [State('search-artist', 'value')]
)
def update_error_message(n_clicks, download_table, search_artist):
    if not n_clicks:
        return('Enter artist name to search')
    elif (type(download_table) == str) & (download_table[0:4]!='data'):
        return(download_table)
    elif (type(download_table) == str) & (download_table[0:4]=='data'):
        return(f'Search for {search_artist} complete!')

if __name__ == '__main__':
    app.run_server(debug=True)
