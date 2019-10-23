import re
import unicodedata

from bs4 import BeautifulSoup
import langdetect
import nltk
from nltk.stem import SnowballStemmer

# from rdflib.plugins.parsers.pyMicrodata import pyMicrodata


staple_ingredient_names = {
    "sv": ["olivolja", "salt", "svartpeppar", "vinäger", "socker"],
    "en": ["Salt and freshly ground black pepper"],
}
ingredient_units = {
    "sv": ["burk", "påse", "knippe", "förpackning", "portion"],
    "en": ["tablespoons", "cups"],
}


def slugify(s):
    slug = unicodedata.normalize("NFKD", s)
    slug = slug.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    slug = re.sub(r"[-]+", "-", slug)
    return slug


def annotate_recipe_instruction(text, ingredients, stemmer):
    # Annotate mentions of the name stem
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

    # Annotate time durations
    matches = list(re.finditer(r"(\b(\d+([\-–]\d+)? min\w*)\b)", text))
    offset = 0
    for m in matches:
        start, end = m.span(1)
        begin_tag = f'<span class="instruction-time-duration"><a href="javascript:alert(\'not implemented\')">'
        end_tag = "</a></span>"
        text = (
            text[: start + offset]
            + begin_tag
            + text[start + offset : end + offset]
            + end_tag
            + text[end + offset :]
        )
        offset = offset + len(begin_tag) + len(end_tag)

    return text


def parse_recipe(recipe):
    assert recipe

    # soup = BeautifulSoup(html, "lxml")
    # [s.decompose() for s in soup("script")]  # remove <script> elements
    # body_text = soup.body.get_text()
    # recipe.lang = detect(body_text)
    instructions_text = "\n".join(recipe.instructions_raw)
    recipe.lang = langdetect.detect(instructions_text)

    lang_code_to_name = {"en": "english", "sv": "swedish"}
    lang_name = lang_code_to_name.get(recipe.lang, "english")
    stemmer = SnowballStemmer(lang_name)

    recipe.total_time = recipe.total_time_raw  # TODO
    recipe.recipe_yield = recipe.recipe_yield_raw  # TODO

    ingredient_lines = [re.sub(r"\s+", " ", s).strip() for s in recipe.ingredients_raw]
    recipe.ingredients = []
    for line in ingredient_lines:
        ingredient = {}
        m = re.match(r"(([\d¼½¾⅓⅔\-– ]| to )+) \b(.+)", line)
        if m:
            ingredient["amount"] = m.group(1)
            ingredient["name"] = m.group(3)
        else:
            ingredient["name"] = line

        m = re.match(
            fr"(({'|'.join(ingredient_units[recipe.lang])}) )?(.+)", ingredient["name"]
        )
        if m:
            ingredient["unit"] = m.group(2)
            ingredient["name"] = m.group(3)

        m = re.match(r"(.+) \((.+)\)", ingredient["name"])
        if m:
            ingredient["name"] = m.group(1)
            ingredient["comment"] = m.group(2)

        if ingredient["name"] in staple_ingredient_names[recipe.lang]:
            ingredient["is_staple"] = True

        ingredient["id"] = slugify(ingredient["name"])
        recipe.ingredients.append(ingredient)

    recipe.ingredient_map = {}
    for ingredient in recipe.ingredients:
        recipe.ingredient_map[ingredient["id"]] = ingredient

    text = re.sub(r"\b\d+\.[\xa0 ]\b", "\n\n", "\n".join(recipe.instructions_raw))
    text = re.sub(r"Gör så här:", "\n", text)
    text = re.sub(r"\bServering", "\n", text)
    instructions_cleaned = [line.strip() for line in text.split("\n") if line.strip()]

    recipe.instructions_html = []
    for line in instructions_cleaned:
        line = annotate_recipe_instruction(line, recipe.ingredients, stemmer)
        recipe.instructions_html.append(line)


if __name__ == "__main__":
    from recipe import extract_recipe_from_url, pprint_recipe
    import os
    import sys
    import urllib.parse

    if len(sys.argv) < 2:
        print("usage: parser.py PATH")
        exit(1)

    path = os.path.realpath(sys.argv[1])
    url = urllib.parse.urlunparse(("file", "", path, "", "", ""))

    recipe = extract_recipe_from_url(url)
    assert recipe

    parse_recipe(recipe)
    pprint_recipe(recipe)
