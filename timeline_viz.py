import dash
from dash import html, dcc, Input, Output, State
from collections import defaultdict
import plotly.graph_objects as go

import utils
from plot_history import search_history, get_clusters


app = dash.Dash(__name__)

node_ids = list()

point_urls_values = []
point_titles_values = []

selected_urls = []
selected_titles = []

def generate_color_dict(clusters):
    num_clusters = len(clusters)
    colors = {cluster: f"hsl({(i / num_clusters) * 360}, 70%, 60%)" for i, cluster in enumerate(sorted(clusters))}
    return colors

def create_line_plot_figure(data_points):
    global point_urls_values
    global point_titles_values

    # Preparing data for plotting
    x_values = [point[0].start_time.to_pydatetime() for point in data_points]
    y_values = [point[1] for point in data_points]
    urls_values = [point[2] for point in data_points]
    titles_values = [point[3] for point in data_points]
    cluster_values = [point[4] for point in data_points]

    cluster_to_color = generate_color_dict(set(cluster_values))

    # Organizing data by cluster
    clustered_data = defaultdict(list)
    for x, y, url, title, cluster in zip(x_values, y_values, urls_values, titles_values, cluster_values):
        clustered_data[cluster].append((x, y, url, title))

    # Create a Plotly figure
    fig = go.Figure()

    # Adding traces for each cluster
    for cluster, points in clustered_data.items():
        x_cluster = [point[0] for point in points]
        y_cluster = [point[1] for point in points]
        color = cluster_to_color[cluster]
        fig.add_trace(go.Scatter(
            x=x_cluster,
            y=y_cluster,
            mode='lines+markers',
            marker=dict(color=color),  # Apply a unique color per cluster
            line=dict(color=color),    # Same color for lines
            name=f'Cluster {cluster}',   # Label each trace with the cluster number
            hoverinfo='text',
            text=[point[3] for point in points]  # hover text from titles
        ))
        point_urls_values.extend([point[2] for point in points])
        point_titles_values.extend([point[3] for point in points])

    # Update layout with titles and hover mode
    fig.update_layout(
        title='Browser History',
        xaxis_title='Time',
        yaxis_title='Num URLs',
        xaxis=dict(type='date', tickformat='%d %b %Y %H:%M'),
        margin=dict(b=0, l=0, t=40, r=0),
        hovermode='closest',
        legend_title_text='Cluster'  # Add legend title
    )

    return fig

# initial_points = search_history(text=None)
initial_points = get_clusters()
initial_figure = create_line_plot_figure(initial_points)

app.layout = html.Div([
    # Use a Div to encapsulate each input section for better control over spacing and layout
    html.Div([
        html.Label('Search Text: ', htmlFor='input-search'),
        dcc.Input(id='input-search', type='text', placeholder='Enter search term'),
        html.Label(' Embedding Distance Threshold: ', htmlFor='input-distance-threshold'),
        dcc.Input(id='input-distance-threshold', type='number', placeholder='Enter threshold', value=1.2),
        html.Button('Search', id='button-search'),
    ], style={'margin-bottom': '10px'}),  # Add a bottom margin for spacing between sections

    html.Div([
        html.Label('Time Bins:', htmlFor='input-time-bins'),
        dcc.Dropdown(
            id='input-time-bins',
            options=[
                {'label': 'Year', 'value': 'Y'},
                {'label': 'Month', 'value': 'M'},
                {'label': 'Week', 'value': 'W'},
                {'label': 'Day', 'value': 'D'},
                {'label': 'Hour', 'value': 'H'}
            ],
            value='M',  # Default selection
            clearable=False,  # Prevents user from clearing the selection
            placeholder='Select a time bin'
        ),
    ], style={'margin-bottom': '20px'}),  # Add a larger bottom margin before the graph

    html.Div([
        dcc.Graph(id='output-graph', figure=initial_figure, config={'staticPlot': False}),
    ], style={'margin-bottom': '20px'}),  # Ensure there is spacing around the graph

    dcc.Markdown(
        id='output-urls',
        children='',  # Placeholder text or initial content
        style={
            'white-space': 'pre-wrap',
            'border': '1px solid #ccc',  # Optionally add a border for better visibility
            'padding': '10px',  # Add padding inside the div
            'margin-bottom': '10px'  # Add bottom margin
        }
    ),
    html.Div(
        html.Button('Open URLs', id='button-open')
    )
], style={'margin': '20px'})


app.layout.children.append(html.Div(id='dummy-div', style={'display': 'none'}))

@app.callback(
    Output('dummy-div', 'children'),  # Dummy output, not used in UI
    [Input('button-open', 'n_clicks')],
    [],
    prevent_initial_call=True
)
def open_urls(n_clicks):
    global selected_urls
    if n_clicks:
        utils.open_urls(selected_urls)
    else:
        raise dash.exceptions.PreventUpdate

@app.callback(
    Output('output-urls', 'children'),
    [Input('output-graph', 'clickData')],
    prevent_initial_call=True
)
def display_url(clickData):
    global selected_urls
    global selected_titles
    if clickData:
        node_index = clickData['points'][0]['pointIndex']
        print(node_index)
        selected_urls = point_urls_values[node_index]
        selected_titles = point_titles_values[node_index]
        
        # Format URLs and titles as Markdown links
        markdown_links = "\n".join(
            [f"[{title}]({url})" for title, url in zip(selected_titles, selected_urls)]
        )
        
        return markdown_links
    else:
        raise dash.exceptions.PreventUpdate

@app.callback(
    Output('output-graph', 'figure'),
    [Input('button-search', 'n_clicks'),
     Input('input-time-bins', 'value')],
    [State('input-search', 'value'),
     State('input-distance-threshold', 'value')],
    prevent_initial_call=True
)
def update_graph(n_clicks, time_bin, search_text, distance_threshold):
    global node_ids
    global initial_graph_height
    ctx = dash.callback_context

    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'button-search' or trigger_id == 'input-time-bins':
        print(time_bin)
        data_points = search_history(text=search_text, distance_threshold=distance_threshold, time_bin=time_bin)
        return create_line_plot_figure(data_points=data_points)
    else:
        return dash.no_update

if __name__ == '__main__':
    app.run_server(debug=False)
