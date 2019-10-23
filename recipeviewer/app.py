from flask import Flask, request, render_template, jsonify

from recipe import extract_recipe_from_url, pprint_recipe
from parser import parse_recipe


app = Flask(__name__)


@app.route("/api/parse_recipe")
def api_parse_recipe():
    url = request.args.get("url")
    assert url

    recipe = extract_recipe_from_url(url)
    parse_recipe(recipe)
    pprint_recipe(recipe)

    return jsonify(recipe)


@app.route("/view_recipe")
def view_recipe():
    url = request.args.get("url")
    assert url

    recipe = extract_recipe_from_url(url)
    assert recipe

    parse_recipe(recipe)
    pprint_recipe(recipe)

    return render_template("recipe.html", recipe=recipe)
