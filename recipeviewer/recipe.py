from dataclasses import dataclass
import io

# import urllib.parse
import urllib.request

import html5lib
import microdata


@dataclass
class Recipe:
    source_url: str = None

    name: str = None
    image_url: str = None

    lang_raw: str = None
    total_time_raw: str = None
    recipe_yield_raw: str = None
    ingredients_raw: list = None
    instructions_raw: list = None

    # Parsed
    lang: str = None
    ingredients: list = None
    instructions_html: list = None


def extract_recipe_from_url(url):
    with urllib.request.urlopen(url) as response:
        htmldoc = response.read()
        return extract_recipe_from_htmldoc(htmldoc)


def extract_recipe_from_htmldoc(htmldoc):
    def extract_recipe_from_microdata_item(item):
        recipe = Recipe()

        recipe.source_url = str(item.url)

        recipe.name = item.name.strip()

        # Look for the first non-empty image URL
        # (Aarstiderne recipes are tagged twice with 'image', the first without 'src')
        image_urls = [str(url) for url in item.get_all("image") if str(url)]
        recipe.image_url = image_urls[0] if image_urls else None

        recipe.total_time_raw = item.totalTime.strip() if item.totalTime else "???"
        recipe.recipe_yield_raw = (
            item.recipeYield.strip() if item.recipeYield else "???"
        )

        recipe.ingredients_raw = [s.strip() for s in item.get_all("recipeIngredient")]
        recipe.instructions_raw = [
            s.strip() for s in item.get_all("recipeInstructions")
        ]

        return recipe

    # print(pyMicrodata().rdf_from_source(path).decode("utf-8"))

    # Read HTML `lang` attribute
    document = html5lib.parse(htmldoc)
    lang_raw = document.attrib.get("lang")

    # microdata uses html5lib internally
    items = microdata.get_items(htmldoc)
    for item in items:
        itemtype = str(item.itemtype[0])
        if (
            itemtype == "http://schema.org/Recipe"
            or itemtype == "https://schema.org/Recipe"
        ):
            recipe = extract_recipe_from_microdata_item(item)
            recipe.lang_raw = lang_raw
            return recipe

    return None


def pprint_recipe(recipe, ensure_ascii=False):
    import dataclasses
    import json

    recipe_dict = dataclasses.asdict(recipe)
    print(json.dumps(recipe_dict, sort_keys=True, indent=4, ensure_ascii=ensure_ascii))


if __name__ == "__main__":
    import os
    import sys
    import urllib.parse

    if len(sys.argv) < 2:
        print("usage: recipe.py PATH")
        exit(1)

    path = os.path.realpath(sys.argv[1])
    url = urllib.parse.urlunparse(("file", "", path, "", "", ""))

    recipe = extract_recipe_from_url(url)
    assert recipe

    pprint_recipe(recipe)
