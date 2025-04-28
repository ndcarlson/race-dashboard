# app.py
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

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
    title="Race Insights",             # Browser tab title
    update_title="Loading..."           # What shows while loading
)
server = app.server  # For Render deployment

# Layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("🏃‍♂️ Race Insights Dashboard", style={
            'textAlign': 'center',
            'fontFamily': 'Roboto',
            'color': '#00CCFF',
            'padding': '10px'
        }),
    ], style={'backgroundColor': '#1e1e1e'}),

    # Filters Section
    html.Div([
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
        ], style={'marginBottom': '30px'}),

        html.Div([
            html.Label("Filter by Country:", style={'color': 'white'}),
            dcc.Dropdown(
                id='country-filter',
                options=[{'label': c, 'value': c} for c in sorted(df['country'].dropna().unique())],
                value=None,
                placeholder="Select a country",
                style={'width': '50%'}
            ),
        ]),
    ], style={'padding': '20px', 'backgroundColor': '#1e1e1e'}),

    # Divider
    html.Hr(style={'borderColor': 'white'}),

    # Graphs Section with loading spinner
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

    # Insights Section
    html.Div([
        html.H4("Takeaway Insights", style={'marginTop': '30px', 'color': '#00CCFF', 'fontFamily': 'Roboto'}),
        html.P("🏔️ The top 10 races with the highest elevation gain highlight extreme endurance events, often over long distances.", style={'color': 'white'}),
        html.P("📈 The scatter plot reveals a concentration of races with moderate distances and elevation gains, but also outliers with intense climbs.", style={'color': 'white'}),
        html.P("🔍 Use the filters above to explore races by specific distance ranges and countries.", style={'color': 'white'})
    ], style={'padding': '20px', 'backgroundColor': '#1e1e1e'})
])

# Callback
@app.callback(
    [Output('bar-elevation', 'figure'),
     Output('scatter-elevation-distance', 'figure')],
    [Input('distance-filter', 'value'),
     Input('country-filter', 'value')]
)
def update_graphs(distance_range, selected_country):
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
    fig1.update_layout(showlegend=False, xaxis_tickangle=-45)

    if not top_elevation.empty:
        highest = top_elevation.iloc[0]
        fig1.add_annotation(
            x=highest['race'],
            y=highest['elevation_gain'] + 1000,
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
        title='Distance vs Elevation Gain by Race',
        labels={'distance': 'Distance (mi)', 'elevation_gain': 'Elevation Gain (ft)'},
        template='plotly_dark',
        color='elevation_gain',
        color_continuous_scale='Viridis'
    )
    fig2.update_layout(hovermode='closest')

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

    return fig1, fig2

# Run app
if __name__ == '__main__':
    app.run(debug=True, port=8050)
