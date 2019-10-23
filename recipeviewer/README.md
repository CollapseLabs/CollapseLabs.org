# recipeviewer

To install:

    python3 -m venv env
    source ./env/bin/activate

    pip install -r requirements.txt

For recipe extraction:

    python recipe.py tests/9616-spinach-lasagna.html

Currently there is support for webpages marked up using HTML5 Microdata. The data extraction is implemented using the  [microdata](https://github.com/edsu/microdata) library. See also:

* https://schema.org/Recipe
* https://search.google.com/structured-data/testing-tool


For recipe parsing / annotation:

    python parser.py tests/9616-spinach-lasagna.html

This parses the ingredient list and adds annotations to the instructions e.g. to emphasize mentioned ingredients to identify timer durations.

For UI:

    flask run

    open http://127.0.0.1:5000/view_recipe?url=https%3A%2F%2Fcooking.nytimes.com%2Frecipes%2F9616-spinach-lasagna
