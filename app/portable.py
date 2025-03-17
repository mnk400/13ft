import flask
import requests
from flask import request
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

app = flask.Flask(__name__)
googlebot_headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.119 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
}

def add_base_tag(html_content, original_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    parsed_url = urlparse(original_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
    
    # Handle paths that are not root, e.g., "https://x.com/some/path/w.html"
    if parsed_url.path and not parsed_url.path.endswith('/'):
        base_url = urljoin(base_url, parsed_url.path.rsplit('/', 1)[0] + '/')
    base_tag = soup.find('base')
    
    print(base_url)
    if not base_tag:
        new_base_tag = soup.new_tag('base', href=base_url)
        if soup.head:
            soup.head.insert(0, new_base_tag)
        else:
            head_tag = soup.new_tag('head')
            head_tag.insert(0, new_base_tag)
            soup.insert(0, head_tag)
    
    return str(soup)

def bypass_paywall(url):
    """
    Bypass paywall for a given url
    """
    if url.startswith("http"):
        response = requests.get(url, headers=googlebot_headers)
        response.encoding = response.apparent_encoding
        return add_base_tag(response.text, response.url)

    try:
        return bypass_paywall("https://" + url)
    except requests.exceptions.RequestException as e:
        return bypass_paywall("http://" + url)

def get_archive_is_url(url):
    """
    Get archive.is url for a given url
    """
    if not url.startswith("http"):
        url = "https://" + url
    archive_url = f"https://archive.is/{url}"
    return archive_url


@app.route("/")
def main_page():
    return flask.send_from_directory(".", "index.html")


@app.route("/favicon.ico")
def get_favicon():
    return flask.send_from_directory(".", "favicon.ico")


@app.route("/article", methods=["POST"])
def show_article():
    link = flask.request.form["link"]
    try:
        return bypass_paywall(link)
    except requests.exceptions.RequestException as e:
        return str(e), 400
    except e:
        raise e

@app.route("/archive", methods=["POST"])
def show_archive():
    link = flask.request.form["link"]
    return flask.redirect(get_archive_is_url(link))


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>", methods=["GET"])
def get_article(path):
    full_url = request.url
    parts = full_url.split("/", 4)
    if len(parts) >= 5:
        url_parts = parts[4].split("/")
        if "archive" in url_parts[-1]:
            actual_url = "https://" + "/".join(url_parts[1:-1]).lstrip("/")
            return flask.redirect(get_archive_is_url(actual_url))
        actual_url = "https://" + parts[4].lstrip("/")
        try:
            return bypass_paywall(actual_url)
        except requests.exceptions.RequestException as e:
            return str(e), 400
        except e:
            raise e
    else:
        return "Invalid URL", 400


app.run(host="0.0.0.0", port=5001, debug=False)
