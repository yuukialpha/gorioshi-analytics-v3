import pathlib
import datetime
import io

import flask
import gql
import gql.transport.aiohttp
import matplotlib.figure
import matplotlib.backends.backend_agg

app = flask.Flask(__name__)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 600

@app.route("/<key>/<email>/<zone_id>/<int:hours>")
def index(key, email, zone_id, hours):
    transport = gql.transport.aiohttp.AIOHTTPTransport(url="https://api.cloudflare.com/client/v4/graphql", headers={
        "Authorization": f"Bearer {key}",
        "X-Auth-Email": email,
    })
    client = gql.Client(transport=transport)

    query_text = pathlib.Path("query.txt").read_text("UTF-8")
    query = gql.gql(query_text)
    params = {
        "zoneTag": zone_id,
        "start": (datetime.datetime.now() - datetime.timedelta(hours=hours)).astimezone(datetime.timezone.utc).isoformat(timespec="seconds"),
        "end": datetime.datetime.now().astimezone(datetime.timezone.utc).isoformat(timespec="seconds"),
        "max": hours,
    }

    result = client.execute(query, variable_values=params)
    first_group = result["viewer"]["zones"][0]["httpRequests1hGroups"]

    ax1_y = [item["uniq"]["uniques"] for item in first_group]
    ax1_x = range(-len(ax1_y)+1,0+1)
    ax2_y = [item["sum"]["bytes"] for item in first_group]
    ax2_x = range(-len(ax2_y)+1,0+1)
    ax2_2_y = [item["sum"]["cachedBytes"] for item in first_group]
    ax2_2_x = range(-len(ax2_2_y)+1,0+1)

    fig = matplotlib.figure.Figure()
    fig.suptitle(f"Stats for {zone_id}")
    fig.set_size_inches(7, 7)
    ax1, ax2 = fig.subplots(2)
    ax1.set_title("Users")
    ax1.plot(ax1_x, ax1_y)
    ax2.set_title("Bytes")
    ax2.plot(ax2_x, ax2_y)
    ax2.plot(ax2_2_x, ax2_2_y)

    canvas = matplotlib.backends.backend_agg.FigureCanvasAgg(fig)
    img = io.BytesIO()
    canvas.print_png(img)
    img.seek(0)

    return flask.send_file(img, mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="3000", debug=True)
