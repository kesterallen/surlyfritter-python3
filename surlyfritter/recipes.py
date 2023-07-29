""" Clunky nickname-to-html-file handler """

from flask import render_template, abort

from . import app

@app.route('/recipes')
@app.route('/recipes/<name>')
def recipes(name=None):
    """ Clunky nickname-to-html-file handler """
    if name is None:
        name = "recipes"
    names = {
        'spinach-artichoke-mac-and-cheese': 'spinach_mac_and_cheese.html',
        'recipes': 'recipes.html',
        'spin': 'green_chile.html',
        'green-chile': 'green_chile.html',
        'matzo_lasagne': 'matzo_lasagne.html',
        'matzoh_lasagne': 'matzo_lasagne.html',
        'eggs': 'instant_pot_hard_boiled_eggs.html',
        'softeggs': 'instant_pot_soft_boiled_eggs.html',
        'pepitas-salsa': 'pepitas_salsa.html',
        'pancakes': 'buttermilk_pancakes.html',
        'gail_lambson_ihop_pancakes': 'gail_lambson_ihop_pancakes.html',
        'gail': 'gail_lambson_ihop_pancakes.html',
        'ihop': 'gail_lambson_ihop_pancakes.html',
        'crisp': 'fruit_crisp.html',
        'fruit-crisp': 'fruit_crisp.html',
        'rice': 'instant_pot_mexican_rice.html',
        'mexican-rice': 'instant_pot_mexican_rice.html',
        'gnocchi': 'gnocchi_with_chard.html',
        'gnocchi-with-chard': 'gnocchi_with_chard.html',
        'cranberry_pecan_pie': 'cranberry_pecan_pie.html',
        'keylimepie': 'key_lime_pie.html',
        'key-lime-pie': 'key_lime_pie.html',
        'mujadara': 'mujadara.html',
        'paneer': 'mutar_paneer.html',
        'mutar-paneer': 'mutar_paneer.html',
        'sourdough-pancakes': 'sourdough_pancakes.html',
        'waffles': 'yogurt_waffles.html',
        'oatmeal': 'instant_pot_steel_cut_oatmeal.html',
        'pretzelpie': 'strawberry_pretzel_pie.html',
        'pretzel-pie': 'strawberry_pretzel_pie.html',
        'libbys': 'pumpkin_pie.html',
        'pumpkinpie': 'pumpkin_pie.html',
        'pie': 'pumpkin_pie.html',
        'pumpkin-pie': 'pumpkin_pie.html',
        'crust': 'pie_dough.html',
        'pie-dough': 'pie_dough.html',
        'piedough': 'pie_dough.html',
        'dutch-baby': 'dutch_baby.html',
        'dutchbaby': 'dutch_baby.html',
        'cookies': 'chocolate_chip_cookies.html',
        'orange-cake': 'orange_cake.html',
        'coffee-cake': 'sour_cream_coffee_cake.html',
        'rolls': 'parker_house_rolls.html',
        'shortbread': 'shortbread.html',
        'andes-mint-cookies': 'andes_mint_cookies.html',
        'black-dots-chocolate-aunt-cake': 'black_dots_chocolate_aunt_cake.html',
        'silver-palates-decadent-chocolate-frosting': 'silver_palates_decadent_chocolate_frosting.html',
    }
    if name not in names:
        abort(404, f"404: recipe {name} not found")

    filename = f"recipes/{names[name]}"
    html = render_template(filename)
    return html

@app.route('/pancakes')
def pancakes():
    """Special route for nature's most perfect food"""
    return recipes("pancakes")

@app.route('/crust')
def crust():
    """Special route for pie crust"""
    return recipes("crust")
