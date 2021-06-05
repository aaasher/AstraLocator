import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
from callbacks import get_categories
import assets.texts as t

tabs_styles = {'border-radius': '4px'}

tab_style = {
    'border-radius': '4px'
}

tab_selected_style = {
    'border-radius': '4px'
}

app_layout = html.Div(
    id='main',
    children=[
        html.A('Astra.Locator',
               id='dash-info-heading-1'),
        html.Div(
            id='main-container',
            children=[
                html.Div(
                    id='dash-info',
                    children=[
                        html.A('Рекомендатор локаций для размещения и продвижения бизнеса',
                               id='dash-info-heading-2'),
                        dcc.Tabs(
                            id="tabs",
                            style=tabs_styles,
                            children=[
                                dcc.Tab(
                                    className='tab-1',
                                    label='Локатор',
                                    style=tab_style,
                                    selected_style=tab_selected_style,
                                    children=[
                                        dcc.Markdown(t.dashboard_section_text,
                                                     className='dash-info-text'),

                                        html.A('Раздел бизнеса:',
                                               id='info-core-dropdown-text'),
                                        dcc.Dropdown(
                                            id='info-core-dropdown',
                                            options=[{'label': x, 'value': x}
                                                     for x in list(get_categories().keys())],
                                            value='Красота',
                                            multi=False
                                        ),

                                        html.A('Категории бизнеса:',
                                               id='info-cat-dropdown-text'),
                                        dcc.Dropdown(
                                            id='info-cat-dropdown',
                                            options=[{'label': x, 'value': x}
                                                     for x in get_categories()['Красота']],
                                            value=['Салон красоты', 'Парикмахерская'],
                                            multi=True
                                        ),

                                        html.A('Что для вас важно?',
                                               className='info-imp-slider-sub-text'),

                                        html.A('Слабая конкуренция (малое кол-во точек бизнеса аналогичной категории)',
                                               className='info-imp-slider-sub-text-l'),
                                        dcc.Slider(
                                            id='info-imp-slider-comps',
                                            className='imp-slider',
                                            min=0,
                                            max=10,
                                            step=1,
                                            value=10
                                        ),

                                        html.A('Дешевая аренда (низкая сред. стоимость аренды  в месяц помещения 38 кв. метров)',
                                               className='info-imp-slider-sub-text-l'),
                                        dcc.Slider(
                                            id='info-imp-slider-rent',
                                            className='imp-slider',
                                            min=0,
                                            max=10,
                                            step=1,
                                            value=5
                                        ),

                                        html.A('Cильный траффик (данные сейчас рандомные, на хакатоне их получим)',
                                               className='info-imp-slider-sub-text-l'),
                                        dcc.Slider(
                                            id='info-imp-slider-traffic',
                                            className='imp-slider',
                                            min=0,
                                            max=10,
                                            step=1,
                                            value=1

                                        ),

                                        html.A(('В каком радиусе от центра города'
                                                ' рекомендовать локации?'),
                                               className='info-imp-slider-sub-text'),

                                        dcc.Slider(
                                            id='info-imp-slider-dist',
                                            className='imp-slider',
                                            min=0.5,
                                            max=10,
                                            step=0.5,
                                            value=4.5,
                                            marks={km / 10: f'{km / 10} км'
                                                   for km in range(5, 100, 5)}

                                        )

                                    ]
                                ),
                                dcc.Tab(
                                    className='tab-1',
                                    label='Инструкция',
                                    style=tab_style,
                                    selected_style=tab_selected_style,
                                    children=[
                                        dcc.Markdown(t.parameters_section_text,
                                                     className='dash-info-text')
                                    ]
                                ),
                                dcc.Tab(
                                    className='tab-1',
                                    label='Данные',
                                    style=tab_style,
                                    selected_style=tab_selected_style,
                                    children=[
                                        dcc.Markdown(t.data_section_text,
                                                     className='dash-info-text')

                                    ]
                                )
                            ]
                        )
                    ]
                ),

                html.Div(
                    id='dash-map',
                    children=[
                        dcc.Graph(id='map-main')
                    ]
                ),

                html.Div(
                    id='dash-detail',
                    children=[
                        html.A('Топ-10 рекомендованных локаций',
                               className='info-imp-slider-sub-text'),
                        dcc.Textarea(
                            id='detail-api-output',
                            style={'width': '90%',
                                   'height': '90%',
                                   'marginLeft': '40px',
                                   'marginTop': '20px',
                                   },
                        ),
                    ]
                ),

            ]
        )
    ]
)
