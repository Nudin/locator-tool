import configparser
from flask import Flask, jsonify, request, redirect
from flask_mwoauth import MWOAuth
from oauthlib.common import to_unicode

config = configparser.ConfigParser()
config.read('../config.ini')

app = Flask(__name__)
app.secret_key = config.get('auth', 'secret_key')
app.config.update(PROPAGATE_EXCEPTIONS=True)

mwoauth = MWOAuth(base_url='https://commons.wikimedia.org/w',
                  clean_url='https://commons.wikimedia.org/wiki',
                  consumer_key=config.get('auth', 'consumer_key'),
                  consumer_secret=config.get('auth', 'consumer_secret'))
app.register_blueprint(mwoauth.bp)

@app.route("/")
def index():
    return redirect('index.html')

@app.route("/user")
def user():
    r = jsonify(user=mwoauth.get_current_user(False))
    return r

@app.route("/edit", methods=['POST'])
def edit():
    pageid = int(request.form['pageid'])
    lat = float(request.form['lat'])
    lng = float(request.form['lng'])
    app.logger.info('Received request pageid=%d, lat=%f, lng=%f', pageid, lat, lng)

    r1 = mwoauth_request({
        'action': 'query',
        'pageids': pageid,
        'prop': 'revisions',
        'rvprop': 'content',
        'meta': 'tokens'
    })
    wikitext = r1['query']['pages'][str(pageid)]['revisions'][0]['*']
    wikitext = to_unicode(wikitext)
    token = r1['query']['tokens']['csrftoken']
    app.logger.info('Obtained token=%s for pageid=%d', token, pageid)

    from location_to_wikitext import add_location_to_wikitext
    new_wikitext = add_location_to_wikitext(lat, lng, wikitext)

    r2 = mwoauth_request({
        'action': 'edit',
        'pageid': str(pageid),
        'summary': '{{Location}}',
        'text': new_wikitext,
        'token': token
    })

    return jsonify(result=r2)

def mwoauth_request(api_query):
    api_query['format'] = 'json'
    return mwoauth.mwoauth.post(mwoauth.base_url + "/api.php?", data=api_query).data

if __name__ == "__main__":
    app.run()
