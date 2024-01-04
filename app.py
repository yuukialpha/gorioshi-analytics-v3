import pathlib
import datetime
import io

import flask
import gql
import gql.transport.aiohttp
import matplotlib.figure
import matplotlib.backends.backend_agg

app = flask.Flask(__name__)

query_texts = [
    pathlib.Path("query.txt").read_text("UTF-8"),
    pathlib.Path("query2.txt").read_text("UTF-8"),
]

@app.route("/<key>/<email>/<zone_id>/<scale_type>/<int:scale>")
def index(key, email, zone_id, scale_type, scale):
    if scale_type == "hourly":
        query_text = query_texts[0]
        before = { "hours": scale }
        method = "httpRequests1hGroups"
        fmt = lambda dt: dt.isoformat(timespec="seconds")
    elif scale_type == "daily":
        query_text = query_texts[1]
        before = { "days": scale }
        method = "httpRequests1dGroups"
        fmt = lambda dt: dt.date().strftime("%Y-%m-%d")
    else:
        return flask.jsonify({"error": "Unknown scale type!"}), 404

    transport = gql.transport.aiohttp.AIOHTTPTransport(url="https://api.cloudflare.com/client/v4/graphql", headers={
        "Authorization": f"Bearer {key}",
        "X-Auth-Email": email,
    })
    client = gql.Client(transport=transport)

    query = gql.gql(query_text)
    params = {
        "zoneTag": zone_id,
        "start": fmt((datetime.datetime.now() - datetime.timedelta(**before)).astimezone(datetime.timezone.utc)),
        "end": fmt(datetime.datetime.now().astimezone(datetime.timezone.utc)),
        "max": scale,
    }

    result = client.execute(query, variable_values=params)
    first_group = result["viewer"]["zones"][0][method]

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
    ax1.plot(ax1_x, ax1_y, marker="*")
    ax2.set_title("Bytes")
    ax2.plot(ax2_x, ax2_y, marker="*")
    ax2.plot(ax2_2_x, ax2_2_y, marker="*")

    canvas = matplotlib.backends.backend_agg.FigureCanvasAgg(fig)
    img = io.BytesIO()
    canvas.print_png(img)
    img.seek(0)

    return flask.send_file(img, mimetype="image/png")

@app.after_request
def add_header(res):
    res.headers["Cache-Control"] = "public, max-age=600, s-maxage=600"
    res.headers["CDN-Cache-Control"] = "max-age=600"
    return res

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="3000", debug=True)
