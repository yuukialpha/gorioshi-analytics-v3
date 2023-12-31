import datetime
import io

import flask
import gql
import gql.transport.aiohttp
import matplotlib.figure
import matplotlib.backends.backend_agg

app = flask.Flask(__name__)

@app.route("/<key>/<email>/<zone_id>/<int:hours>")
def index(key, email, zone_id, hours):
    transport = gql.transport.aiohttp.AIOHTTPTransport(url="https://api.cloudflare.com/client/v4/graphql", headers={
        "Authorization": f"Bearer {key}",
        "X-Auth-Email": email,
    })
    client = gql.Client(transport=transport)

    query_text = """{
  viewer {
    zones ( filter: { zoneTag: $zoneTag } ) {
      httpRequests1hGroups (
        limit: $max,
        filter: {
          datetime_geq: $start,
          datetime_lt: $end,
        },
        orderBy: [datetime_ASC]
      ) {
        sum {
          bytes,
          cachedBytes,
          cachedRequests,
          encryptedBytes,
          encryptedRequests,
          pageViews,
          requests,
          threats,
        }
        uniq {
          uniques,
        }
        dimensions {
          date,
          datetime,
        }
      }
    }
  }
}"""
    query = gql.gql(query_text)
    params = {
        "zoneTag": zone_id,
        "start": (datetime.datetime.now() - datetime.timedelta(hours=hours)).astimezone(datetime.timezone.utc).isoformat(timespec="seconds"),
        "end": datetime.datetime.now().astimezone(datetime.timezone.utc).isoformat(timespec="seconds"),
        "max": hours,
    }

    result = client.execute(query, variable_values=params)
    first_group = result["viewer"]["zones"][0]["httpRequests1hGroups"]

    y = [item["uniq"]["uniques"] for item in first_group]
    x = range(-len(y),0)

    fig = matplotlib.figure.Figure()
    ax = fig.add_subplot(111)
    ax.plot(x, y)

    canvas = matplotlib.backends.backend_agg.FigureCanvasAgg(fig)
    img = io.BytesIO()
    canvas.print_png(img)
    img.seek(0)

    return flask.send_file(img, mimetype='image/png')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="3000", debug=True)
