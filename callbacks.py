import pandas as pd
import numpy as np
import plotly.express as px
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from maindash import app
import json
from flask import request
from datetime import datetime, timedelta
from sklearn.metrics.pairwise import haversine_distances
import plotly.figure_factory as ff

pd.options.mode.chained_assignment = None
map_box_token = 'pk.eyJ1IjoiYXNoZXJhc2hlciIsImEiOiJja3BncjV0d28yZHVvMnBsbGx5aGp4d3lrIn0.sqhH34AnR9FQCC2tysD3vg'

# load data
competition_data = pd.read_csv('data/competition_data.csv')
metric_rent = pd.read_csv('data/metric_rent.csv')
metric_traffic = pd.read_csv('data/metric_traffic.csv')
metric_rt = pd.merge(metric_rent, metric_traffic[['point_index', 'metric_traffic']],
                     on='point_index', how='left')
competition_data['comps_array'] = np.array(competition_data.to_dict('records'))


def first_elem(lst: list):
    try:
        elem = lst[0]
        return elem
    except Exception as exc:
        return None


def get_categories(json_path: str = 'data/bcats_raw.json'):
    with open(json_path) as data_file:
        data_loaded = json.load(data_file)
    return data_loaded


def haversine_est(point_1, point_2=(55.7525, 37.6231)):
    lon1, lat1, lon2, lat2 = map(np.radians, [point_1[1], point_1[0], point_2[1], point_2[0]])
    x = (lon2 - lon1) * np.cos(0.5*(lat2+lat1))
    y = lat2 - lat1
    return 6371 * np.sqrt(x*x + y*y)


def find_optimal(sub_cat,
                 imp_rent,
                 imp_traffic,
                 imp_comps,
                 center_dist,
                 top,
                 blur):

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

    df_ranked = pd.merge(metric_rt, count_comps, on='point_index', how='left').fillna(0)

    # leave only certain points, that are X km far from city center
    df_ranked['dist'] = df_ranked.apply(
        lambda x: haversine_est([x['point_lat'], x['point_lon']]), axis=1
    )
    df_ranked = df_ranked[df_ranked['dist'] < center_dist]

    # compute weighted rating
    tot = sum([imp_rent, imp_traffic, imp_comps])
    w_r, w_t, w_c = imp_rent / tot, imp_traffic / tot, imp_comps / tot

    df_ranked['rank_rent'] = (1 / (df_ranked['metric_rent'] + 1)).rank(pct=True)
    df_ranked['rank_traffic'] = df_ranked['metric_traffic'].rank(pct=True)
    df_ranked['rank_comps'] = (1 / (df_ranked['count_comps'] + 1)).rank(pct=True)

    df_ranked['total_rank'] = (w_r * df_ranked['rank_rent']
                               + w_t * df_ranked['rank_traffic']
                               + w_c * df_ranked['rank_comps'])

    # apply blur to total rank
    if blur > 0:
        y = df_ranked[['point_lat', 'point_lon']].to_numpy()
        ranks = df_ranked['total_rank']

        d = haversine_distances(
            np.radians(
                df_ranked[
                    ['point_lat', 'point_lon']
                ].to_numpy()
            )
        ) * 6371000 / 1000

        rank_blured = np.empty(len(d))

        for i, distances_row in enumerate(d):
            idx = distances_row.argsort()[:blur]
            top_k_ranks = ranks.iloc[idx].to_numpy()
            top_k_dist = distances_row[idx]
            rank_blured[i] = np.mean(top_k_ranks / (top_k_dist + 1))

        df_ranked['total_rank'] = rank_blured

    # get top X points from final data
    df_ranked = df_ranked.sort_values(by='total_rank', ascending=False)[:top]
    # convert to json
    return df_ranked.to_json(orient='records', force_ascii=False, indent=4)


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
    Input('info-imp-slider-dist', 'value')
)
def upd_main(sub_cat,
             imp_comps,
             imp_rent,
             imp_traffic,
             center_dist):

    data = [(str(datetime.utcnow()),
             request.remote_addr,
             first_elem(request.access_route),
             request.user_agent.string,
             sub_cat,
             imp_comps,
             imp_rent,
             imp_traffic,
             center_dist)
            ]
    print('USER_UPD_MAIN', data)

    jsn = find_optimal(sub_cat,
                       imp_rent,
                       imp_traffic,
                       imp_comps,
                       center_dist,
                       top=10000,
                       blur=0)

    df_jsn = pd.read_json(jsn)

    px.set_mapbox_access_token(map_box_token)

    fig = ff.create_hexbin_mapbox(
        data_frame=df_jsn,
        lat="point_lat",
        lon="point_lon",
        color="total_rank",
        agg_func=np.mean,
        nx_hexagon=int(center_dist / 0.1),
        opacity=0.5,
        labels={"color": "Рейтинг локации (0 - 1)"},
        color_continuous_scale="plotly3_r",
        show_original_data=True,
        min_count=1,
        zoom=11.5,
        original_data_marker=dict(size=4, opacity=0.5, color="deeppink")
    )
    fig.update_layout(margin=dict(b=0, t=0, l=0, r=0), width=1220, height=1100)

    return fig, json.dumps(json.loads(jsn)[:10], indent=2, ensure_ascii=False)


if __name__ == '__main__':
    print('ok')