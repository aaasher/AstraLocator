from maindash import app
from layout import app_layout

server = app.server
app.layout = app_layout

if __name__ == '__main__':

    app.run_server(
        host='127.0.0.1',
        port=8050,
        debug=True
        # debug=False
    )


