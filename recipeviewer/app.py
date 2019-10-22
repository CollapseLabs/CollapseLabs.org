from flask import Flask, render_template

from parser import parse_recipe


app = Flask(__name__)


@app.route("/recipe/")
@app.route("/recipe/<name>")
def recipe(recipe=None):
    # path = "tests/indisk-curry-med-paprika-bladselleri-couscous-och-creme-fraiche2.html"
    path = "tests/gnocchetti-med-mangold-spenat-selleri-och-mozzarella.html"
    recipe = parse_recipe(path)

    return render_template("recipe.html", recipe=recipe)
