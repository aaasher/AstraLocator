import pandas as pd
import numpy as np
import plotly.express as px
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from maindash import app
import json
from flask import request
from datetime import datetime
import h3
from sklearn.neighbors import BallTree


def load_coord_grid(path=None):
    if path is None:
        path = 'data/grid.csv'
    grid = pd.read_csv(path).iloc[:, 1:].to_numpy()
    tree = BallTree(np.deg2rad(grid), metric='haversine')
    return grid, tree


def haversine_exc(point_1, point_2=(55.7525, 37.6231)):
    lon1, lat1, lon2, lat2 = map(np.radians, [point_1[1], point_1[0], point_2[1], point_2[0]])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    return 6367 * 2 * np.arcsin(np.sqrt(a))


pd.options.mode.chained_assignment = None
map_box_token = 'pk.eyJ1IjoiYXNoZXJhc2hlciIsImEiOiJja3BncjV0d28yZHVvMnBsbGx5aGp4d3lrIn0.sqhH34AnR9FQCC2tysD3vg'
px.set_mapbox_access_token(map_box_token)

# load data
# competition
competition_data = pd.read_csv('data/competition_data.csv')
competition_data['comps_array'] = np.array(competition_data.to_dict('records'))
# rent
metric_rent = pd.read_csv('data/metric_rent.csv')
metric_rent['dist'] = metric_rent.apply(lambda x: haversine_exc([x['point_lat'], x['point_lon']]), axis=1)
# traffic
metric_traffic = pd.read_csv('data/metric_traffic.csv')
# grid
grid, tree = load_coord_grid()


def get_categories(json_path: str = 'data/bcats_raw.json'):
    with open(json_path) as data_file:
        data_loaded = json.load(data_file)
    return data_loaded


def point_to_hex(lat, lon):
    coord_matrix = [
        [cords[1], cords[0]]
        for cords in h3.h3_to_geo_boundary(h3.geo_to_h3(lat, lon, 10))
    ]

    return coord_matrix + [coord_matrix[0]]


def df_to_geojson(df, top=10000):
    geojson = {
        'type': 'FeatureCollection',
        'features': [
            {'type': 'Feature',
             'geometry': {
                 'type': 'Polygon',
                 'coordinates': [
                     point_to_hex(row.point_lat, row.point_lon)
                 ]},
             'properties': {
                 'point_index': row.point_index,
                 'point_lat': row.point_lat,
                 'point_lon': row.point_lon,
                 'metric_rent': row.metric_rent,
                 'metric_traffic': row.metric_traffic,
                 'dist': row.dist,
                 'count_comps': row.count_comps,
                 'comps_array': row.comps_array if row.comps_array else [],
                 'rank_rent': row.rank_rent,
                 'rank_traffic': row.rank_traffic,
                 'rank_comps': row.rank_comps,
                 'total_rank': row.total_rank
             },
             'id': row.point_index
             }
            for idx, row in enumerate(df.itertuples()) if idx <= top
        ]
    }
    return geojson


def geojson_to_df(geojson):
    return pd.DataFrame([feature['properties'] for feature in geojson['features']])


def find_optimal(sub_cat,
                 imp_rent,
                 imp_traffic,
                 imp_comps,
                 center_dist,
                 top,
                 blur,
                 hours):

    # leave only certain hours traffic data
    df_ranked = metric_traffic[metric_traffic['group'] == hours].iloc[:, 1:]

    # merge with rent data
    df_ranked = pd.merge(metric_rent, df_ranked[['point_index', 'metric_traffic']],
                         on='point_index', how='left')

    # leave only certain points, that are X km far from city center
    df_ranked = df_ranked[df_ranked['dist'] < center_dist]

    # df_ranked = df_ranked[df_ranked['metric_traffic']>0]

    # leave only certain busnesses here
    count_comps = competition_data[
        competition_data['sub_cat'].isin(sub_cat)
    ][
        ['point_index', 'ya_id', 'comps_array']
    ].groupby(
        'point_index'
    ).agg({
        'ya_id': 'nunique',
        'comps_array': list
    }).reset_index().rename(columns={'ya_id': 'count_comps'})

    df_ranked = pd.merge(df_ranked, count_comps, on='point_index', how='left').fillna(0)

    # apply blur to count comps
    if blur > 0:
        indexes = tree.query(np.deg2rad(df_ranked[['point_lat', 'point_lon']].to_numpy()), k=blur)[1]

        df_ranked.index = df_ranked['point_index'].astype(int)

        rank_matrix = np.concatenate([df_ranked[['count_comps']].reindex(indexes[:, idx]).to_numpy()
                                      for idx in range(0, blur)],
                                     axis=1)

        df_ranked['count_comps'] = np.sum(rank_matrix, axis=1)

    # compute weighted rating
    tot = sum([imp_rent, imp_traffic, imp_comps])
    w_r, w_t, w_c = imp_rent / tot, imp_traffic / tot, imp_comps / tot

    df_ranked['rank_rent'] = (1 / (df_ranked['metric_rent'] + 1)).rank(pct=True)
    df_ranked['rank_traffic'] = df_ranked['metric_traffic'].rank(pct=True)
    df_ranked['rank_comps'] = (1 / (df_ranked['count_comps'] + 1)).rank(pct=True)

    df_ranked['total_rank'] = (w_r * df_ranked['rank_rent']
                               + w_t * df_ranked['rank_traffic']
                               + w_c * df_ranked['rank_comps']).round(5)

    df_ranked = df_ranked.sort_values(by='total_rank', ascending=False)[:top]

    # convert to geojson
    return df_to_geojson(df_ranked)

@app.callback(
    Output("info-cat-dropdown", "options"),
    [Input("info-core-dropdown", "value")]
)
def upd_dropdown(core):
    if core:
        if isinstance(core, list):
            return [{'label': x, 'value': x} for x in get_categories()[core[0]]]
        else:
            return [{'label': x, 'value': x} for x in get_categories()[core]]
    else:
        raise PreventUpdate


@app.callback(
    Output("map-main", "figure"),
    Output("detail-api-output", "value"),

    Input('info-cat-dropdown', 'value'),
    Input('info-imp-slider-comps', 'value'),
    Input('info-imp-slider-rent', 'value'),
    Input('info-imp-slider-traffic', 'value'),
    Input('info-imp-slider-dist', 'value'),
    Input('info-top-dropdown', 'value'),
    Input('info-hours-dropdown', 'value'),

    [State('map-main', 'relayoutData')]

)
def upd_main(sub_cat,
             imp_comps,
             imp_rent,
             imp_traffic,
             center_dist,
             top,
             hours,
             relayout_data):

    data = [(str(datetime.utcnow()),
             request.remote_addr,
             request.access_route,
             request.user_agent.string,
             sub_cat,
             imp_comps,
             imp_rent,
             imp_traffic,
             center_dist)
            ]
    print('USER_UPD_MAIN', data)

    geojs = find_optimal(sub_cat,
                         imp_rent,
                         imp_traffic,
                         imp_comps,
                         center_dist,
                         top,
                         18,
                         hours)

    if relayout_data:
        center_lat = relayout_data.get('mapbox.center', {}).get('lat', 55.7525)
        center_lon = relayout_data.get('mapbox.center', {}).get('lon', 37.6231)
        map_zoom = relayout_data.get('mapbox.zoom', 12.2)
    else:
        center_lat = 55.7525
        center_lon = 37.6231
        map_zoom = 12.2

    fig = px.choropleth_mapbox(geojson_to_df(geojs),
                               geojson=geojs,
                               color="total_rank",
                               locations="point_index",
                               color_continuous_scale="plotly3_r",
                               zoom=map_zoom,
                               opacity=0.8,
                               center={
                                   "lat": center_lat,
                                   "lon": center_lon
                               },
                               hover_data=[
                                   'point_index',
                                   'point_lat',
                                   'point_lon',
                                   'metric_rent',
                                   'metric_traffic',
                                   'count_comps',
                                   'total_rank'
                               ])

    fig.update_layout(margin=dict(b=0, t=0, l=0, r=0), width=1220, height=1100)

    if relayout_data:
        if 'xaxis.range[0]' in relayout_data:
            fig['layout']['xaxis']['range'] = [
                relayout_data['xaxis.range[0]'],
                relayout_data['xaxis.range[1]']
            ]
        if 'yaxis.range[0]' in relayout_data:
            fig['layout']['yaxis']['range'] = [
                relayout_data['yaxis.range[0]'],
                relayout_data['yaxis.range[1]']
            ]

    return fig, json.dumps(geojs['features'][:10], indent=2, ensure_ascii=False)


if __name__ == '__main__':
    print('ok')