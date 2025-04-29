# app.py
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, callback_context, no_update

# Load dataset
url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTNUbSB7i6_xLP-z36OdxHiypbfY08leVeGsZccKX_46FetbPwuLfMz74lcJqaU8jr-V7VKRKIZxrh0/pub?output=csv'
df = pd.read_csv(url)
df = df.dropna(subset=['elevation_gain', 'distance'])
df['country'] = df['country'].astype(str).str.strip().str.title()

# External Stylesheets (for font)
external_stylesheets = [
    "https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"
]

# Initialize app
app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    title="Race Insights",
    update_title="Loading..."
)
server = app.server  # For Render

# Layout
app.layout = html.Div([
    html.Div([
        html.H1("🏃‍♂️ Race Insights Dashboard", style={
            'textAlign': 'center',
            'fontFamily': 'Roboto',
            'color': '#00CCFF',
            'padding': '10px'
        }),
    ], style={'backgroundColor': '#1e1e1e'}),

    html.Div([
        html.Label("Filter by Distance Range (miles):", style={'color': 'white'}),
        dcc.RangeSlider(
            id='distance-filter',
            min=df['distance'].min(),
            max=df['distance'].max(),
            step=5,
            marks={int(i): str(int(i)) for i in range(0, int(df['distance'].max()) + 1, 50)},
            value=[df['distance'].min(), df['distance'].max()],
            tooltip={"placement": "bottom", "always_visible": True}
        ),
        html.Br(),
        html.Label("Filter by Country:", style={'color': 'white'}),
        dcc.Dropdown(
            id='country-filter',
            options=[{'label': c, 'value': c} for c in sorted(df['country'].dropna().unique())],
            value=None,
            placeholder="Select a country",
            style={'width': '50%'}
        ),
        html.Br(),
        html.Button(
            "Reset Filters",
            id='reset-button',
            n_clicks=0,
            style={
                'marginTop': '20px',
                'padding': '10px 20px',
                'backgroundColor': '#00CCFF',
                'color': 'black',
                'border': 'none',
                'borderRadius': '5px',
                'cursor': 'pointer',
                'fontWeight': 'bold'
            }
        )
    ], style={'padding': '20px', 'backgroundColor': '#1e1e1e'}),

    html.Hr(style={'borderColor': 'white'}),

    html.Div([
        dcc.Loading(
            id="loading-graphs",
            type="circle",
            children=[
                dcc.Graph(id='bar-elevation', style={'overflowX': 'auto', 'height': '600px'}),
                dcc.Graph(id='scatter-elevation-distance', style={'overflowX': 'auto', 'height': '500px'})
            ]
        )
    ], style={'padding': '20px', 'backgroundColor': '#2b2b2b'}),

    html.Div([
        html.H4("Takeaway Insights", style={'marginTop': '30px', 'color': '#00CCFF', 'fontFamily': 'Roboto'}),
        html.P("🏔️ The top 10 races with the highest elevation gain highlight extreme endurance events, often over long distances.", style={'color': 'white'}),
        html.P("📈 The scatter plot reveals a concentration of races with moderate distances and elevation gains, but also outliers with intense climbs.", style={'color': 'white'}),
        html.P("🔍 The filter by country reveals regional patterns — for example, Andorra has multiple races with very high elevation gains despite being a small country.", style={'color': 'white'})
    ], style={'padding': '20px', 'backgroundColor': '#1e1e1e'})
])

# Updated Callback
@app.callback(
    [Output('bar-elevation', 'figure'),
     Output('scatter-elevation-distance', 'figure'),
     Output('country-filter', 'value'),
     Output('distance-filter', 'value')],  # NEW: reset the slider too
    [Input('distance-filter', 'value'),
     Input('country-filter', 'value'),
     Input('reset-button', 'n_clicks'),
     Input('bar-elevation', 'clickData')]
)
def update_graphs(distance_range, selected_country, reset_clicks, clickData):
    ctx = callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    # Defaults
    reset_country_value = no_update
    reset_distance_value = no_update

    # Reset filters if button clicked
    if triggered_id == 'reset-button':
        distance_range = [df['distance'].min(), df['distance'].max()]
        selected_country = None
        clickData = None
        reset_country_value = None
        reset_distance_value = [df['distance'].min(), df['distance'].max()]

    filtered_df = df[df['distance'].between(distance_range[0], distance_range[1])]
    if selected_country:
        filtered_df = filtered_df[filtered_df['country'] == selected_country]

    # Bar Chart
    top_elevation = filtered_df.sort_values(by='elevation_gain', ascending=False).head(10)
    fig1 = px.bar(
        top_elevation,
        x='race',
        y='elevation_gain',
        title='Top 10 Races by Elevation Gain',
        labels={'elevation_gain': 'Elevation Gain (ft)', 'race': 'Race Name'},
        template='plotly_dark',
        text='elevation_gain'
    )
    fig1.update_traces(marker_color='indianred', textposition='outside')
    fig1.update_layout(showlegend=False, xaxis_tickangle=-45, bargap=0.3)

    if not top_elevation.empty:
        highest = top_elevation.iloc[0]
        fig1.add_annotation(
            x=highest['race'],
            y=highest['elevation_gain'] * 1.1,
            text="⬆️ Highest Elevation",
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-30,
            font=dict(color='cyan')
        )

    # Scatter Plot
    fig2 = px.scatter(
        filtered_df,
        x='distance',
        y='elevation_gain',
        size='aid_stations',
        hover_name='race',
        hover_data=['country'],  # Show country on hover
        title='Distance vs Elevation Gain by Race',
        labels={'distance': 'Distance (mi)', 'elevation_gain': 'Elevation Gain (ft)'},
        template='plotly_dark',
        color='elevation_gain',
        color_continuous_scale='Viridis'
    )
    fig2.update_layout(hovermode='closest')

    # Highlight if a bar was clicked
    if clickData and 'points' in clickData and triggered_id != 'reset-button':
        clicked_race = clickData['points'][0]['x']
        fig2.update_traces(
            marker=dict(line=dict(width=2, color='cyan')),
            selector=dict(mode='markers')
        )
        fig2.update_traces(
            selectedpoints=[i for i, race in enumerate(filtered_df['race']) if race == clicked_race],
            selected=dict(marker=dict(size=20, color='yellow', opacity=1)),
            unselected=dict(marker=dict(opacity=0.2))
        )

    # Highlight outlier
    outlier = filtered_df[filtered_df['elevation_gain'] > 14000]
    if not outlier.empty:
        fig2.add_annotation(
            x=outlier.iloc[0]['distance'],
            y=outlier.iloc[0]['elevation_gain'],
            text="Extreme Gain!",
            showarrow=True,
            arrowhead=3,
            ax=20,
            ay=-40,
            font=dict(color='cyan')
        )

    return fig1, fig2, reset_country_value, reset_distance_value

# Run app
if __name__ == '__main__':
    app.run(debug=True, port=8050)
