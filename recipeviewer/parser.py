from dataclasses import dataclass, asdict
import json
import re
import unicodedata


import lxml.html
import nltk
from nltk.stem import SnowballStemmer
import microdata

# from rdflib.plugins.parsers.pyMicrodata import pyMicrodata

stemmer = SnowballStemmer("swedish")


def slugify(s):
    slug = unicodedata.normalize("NFKD", s)
    slug = slug.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    slug = re.sub(r"[-]+", "-", slug)
    return slug


@dataclass
class Recipe:
    name: str = None
    image_url: str = None
    total_time: str = None
    recipe_yield: str = None
    ingredients: list = None
    instructions: list = None
    instructions_html: list = None


def annotate_recipe_instruction(text, ingredients):
    ingredient_namestem_to_id = {}
    for ingredient in ingredients:
        if not ingredient.get("is_staple"):
            namestem = stemmer.stem(ingredient["name"])
            ingredient_namestem_to_id[namestem] = ingredient["id"]

    matches = []
    for namestem in ingredient_namestem_to_id.keys():
        matches.extend(list(re.finditer(rf"(\b({namestem})\w*\b)", text)))

    matches.sort(key=re.Match.start)

    offset = 0
    tuples = [(m.span(1), ingredient_namestem_to_id[m.group(2)]) for m in matches]
    for span, ingredient_id in tuples:
        start, end = span
        begin_tag = f'<span class="instruction-ingredient-{ingredient_id}">'
        end_tag = "</span>"
        text = (
            text[: start + offset]
            + begin_tag
            + text[start + offset : end + offset]
            + end_tag
            + text[end + offset :]
        )
        offset = offset + len(begin_tag) + len(end_tag)

    return text


def parse_recipe_item(item):
    recipe = Recipe()
    recipe.name = item.name.strip()
    recipe.image_url = str(item.image) if str(item.image) else None
    recipe.total_time = item.totalTime.strip()
    recipe.recipe_yield = item.recipeYield.strip()
    ingredient_lines = [
        re.sub(r"\s+", " ", s).strip() for s in item.get_all("recipeIngredient")
    ]
    recipe.ingredients = []
    for line in ingredient_lines:
        ingredient = {}
        m = re.match(r"([\d¼½¾⅓⅔\-–]+) (.+)", line)
        if m:
            ingredient["amount"] = m.group(1)
            ingredient["name"] = m.group(2)
        else:
            ingredient["name"] = line

        m = re.match(r"((burk|påse|knippe|förpackning) )?(.+)", ingredient["name"])
        if m:
            ingredient["unit"] = m.group(2)
            ingredient["name"] = m.group(3)

        m = re.match(r"(.+) \((.+)\)", ingredient["name"])
        if m:
            ingredient["name"] = m.group(1)
            ingredient["comment"] = m.group(2)

        if ingredient["name"] in ["olivolja", "salt", "svartpeppar", "vinäger"]:
            ingredient["is_staple"] = True

        ingredient["id"] = slugify(ingredient["name"])
        recipe.ingredients.append(ingredient)

    recipe.ingredient_map = {}
    for ingredient in recipe.ingredients:
        recipe.ingredient_map[ingredient["id"]] = ingredient

    text = item.get("recipeInstructions")
    text = re.sub(r"\d+\.\xa0", "\n\n", text)
    text = re.sub(r"Gör så här:", "", text)
    recipe.instructions = [line.strip() for line in text.split("\n") if line.strip()]

    recipe.instructions_html = []
    for line in recipe.instructions:
        line = annotate_recipe_instruction(line, recipe.ingredients)
        recipe.instructions_html.append(line)

    return recipe


def parse_recipe(path):
    # print(pyMicrodata().rdf_from_source(path).decode("utf-8"))

    with open(path, "rb") as f:
        root = lxml.html.parse(f).getroot()
        lang = root.attrib.get("lang")
        print(lang)

    # from bs4 import BeautifulSoup
    # from langdetect import detect

    # with open(path, "rb") as f:
    #     soup = BeautifulSoup(f, "lxml")
    #     [s.decompose() for s in soup("script")]  # remove <script> elements
    #     body_text = soup.body.get_text()
    #     print(detect(body_text))

    with open(path, "rb") as f:
        items = microdata.get_items(f)
        for item in items:
            if str(item.itemtype[0]) == "https://schema.org/Recipe":
                recipe = parse_recipe_item(item)
                print(
                    json.dumps(
                        asdict(recipe), sort_keys=True, indent=4, ensure_ascii=False
                    )
                )
                print(recipe.ingredient_map)
                return recipe

    return None
