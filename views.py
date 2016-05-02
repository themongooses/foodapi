from flask import request, jsonify

from app import app, db
from entities import Food, Menu, NutritionalFact, Recipe
from utils import nocache, check_date


################
# FRIDGE ROUTE #
################
@app.route('/fridge/', methods=["GET"])
@nocache
def fridge():
    """
    Gets all food records that have their in_fridge attribute set to true
    :return: A JSON object of {"fridge": [<a list of food records in the form of JSON objects>]}
    """
    return jsonify({"fridge": [food for food in Food(db).all(cols={"in_fridge": ["=", True]})]})


#################
# RECIPE ROUTES #
#################
@app.route('/recipe/', methods=["POST"])
@nocache
def recipe_update_create():
    """
    Take in a JSON object in the form of
    {
        "recipes":
        [
            {
                "rec_id": 1,
                "rec_name": "Chicken and Rice",
                "instructions": "Idk, ask mom",
                "category": <a string value of either entree, appetizer, or dessert>,
                "ingredients": [ <a list of ingredient ids>]
            }, ...
        ]
    }

    Where for each entry in "recipes" if there is a "rec_id" attribute,
    it is assumed that we are updating an existing recipe (because we wouldn't have the id otherwise),
    and the values given will update the record and its ingredients links in the database.

    Otherwise, if there is no "rec_id" for an object, the system will assume the values
    given are for a new record in the database and will create a new record.

    :return: A JSON object of {"recipes":[<list of ids corresponding to recipes updated or created in the system]}
    """
    if not request.json or len(request.json) == 0:
        return jsonify({"error": "No JSON supplied"}), 400
    id_column = Recipe.__keys__[0]
    ret_val = []
    rec = Recipe(db)
    j = request.json
    for recipe in j['recipes']:
        recipe_id = recipe.get(id_column, None)
        # Enforce enums
        if recipe.get("category", None) and recipe['category'] not in Recipe.__columns__['category']:
            return jsonify({
                "error": "Categories must be one of the following: {}".format(Recipe.__columns__['category'])}
            )
        if recipe_id:
            rec.find_by_id(recipe_id)
            rec.update(**recipe)
            rec.flush()
        else:
            rec.create(**recipe)
        if recipe.get('ingredients', None):
            try:
                recipe.ingredients = recipe['ingredients']
            except TypeError:
                return jsonify({
                    "error": "Ingredient entries must be a list of ids referencing food items in the database"
                })
        ret_val.append(rec.id)
    return jsonify({"recipes": ret_val})


@app.route('/recipe/<int:rec_id>/del/', methods=["DELETE"])
@nocache
def recipe_delete(rec_id):
    """
    Given a recipe_id, will attempt to delete the recipe with the id in the database.
    Note, database triggers will remove associated entries in the ingredients and serves tables
    :param rec_id: The Recipe id to delete
    :return: JSON data in the form of {"success":<boolean value whether a record was deleted or not>}
    """
    cursor = db.cursor()
    res = cursor.execute("DELETE FROM {table} WHERE {key}=%s".format(table=Recipe.__table__,
                                                                     key=Recipe.__keys__[0]), (rec_id,))
    db.commit()
    cursor.close()
    return jsonify({"success": res != 0})


@app.route("/recipe/all/", methods=["GET"])
@nocache
def get_all_recipes():
    """
    Fetch all recipes in the database
    :return: JSON data in the form of {"recipes":[<list of JSON objects representing the recipes and their ingredients>]}
    """
    recipes = Recipe(db).all()
    cursor = db.cursor()
    for recipe in recipes:
        id_val = recipe[Recipe.__keys__[0]]
        cursor.execute(
            "SELECT *\n"
            "FROM mongoose.food\n"
            "WHERE food_id IN (SELECT food_id\n"
            "                  FROM mongoose.ingredients\n"
            "                  WHERE recipe_id = %s)",
            (id_val,))
        ingredients = cursor.fetchall()
        recipe['ingredients'] = ingredients
    cursor.close()

    return jsonify({"recipes": recipes})


@app.route("/recipe/<int:rec_id>/", methods=["GET"])
@nocache
def get_recipe_by_id(rec_id):
    """
    Gets a single recipe by its id
    :param rec_id: The numeric id of the recipe to find
    :return: JSON response in the form of {"recipe": <A JSON object representing a recipe and its ingredients}}
    """
    recipe = Recipe(db).find_by_id(rec_id)
    if not recipe:
        return jsonify({"error": "No recipe with id {} found".format(rec_id)}), 404

    id_val = recipe[Recipe.__keys__[0]]
    cursor = db.cursor()
    cursor.execute(
        "SELECT *\n"
        "FROM mongoose.food\n"
        "WHERE food_id IN (SELECT food_id\n"
        "                  FROM mongoose.ingredients\n"
        "                  WHERE recipe_id = %s)",
        (id_val,))
    ingredients = cursor.fetchall()
    recipe['ingredients'] = ingredients
    cursor.close()
    return jsonify(recipe)


@app.route("/recipe/<string:rec_name>/", methods=["GET"])
@nocache
def get_recipe_by_name(rec_name):
    """
    Get all recipes that match a name
    :param rec_name: A string value with a recipe name
    :return: JSON data in the form of {"recipes":[<list of JSON objects representing the recipes and their ingredients>]}
    """
    recipes = Recipe(db).find_by_attribute("rec_name", rec_name, limit=-1)
    if not recipes:
        return jsonify(({"error": "No recipes with name \"{}\" found".format(rec_name)})), 404
    cursor = db.cursor()
    for recipe in recipes:
        id_val = recipe[Recipe.__keys__[0]]
        cursor.execute(
            "SELECT *\n"
            "FROM mongoose.food\n"
            "WHERE food_id IN (SELECT food_id\n"
            "                  FROM mongoose.ingredients\n"
            "                  WHERE recipe_id = %s)",
            (id_val,))
        ingredients = cursor.fetchall()
        recipe['ingredients'] = ingredients
    cursor.close()
    return jsonify({"recipes": recipes})


###############
# FOOD ROUTES #
###############
@app.route("/food/", methods=["POST"])
@nocache
def food_update_create():
    """
    Take in a JSON object in the form of
    {
        "food":
        [
            {
                "food_id": 1,
                "food_name": "Chicken and Rice",
                "in_fridge": <boolean value>,
                "fk_nfact_id": <integer equal to this food's nutritional fact record>,
                "nutrition": <a JSON object with similar structure to the nutritional_fact schema>
            }, ...
        ]
    }

    Where for each entry in "food" if there is a "food_id" attribute,
    it is assumed that we are updating an existing food (because we wouldn't have the id otherwise),
    and the values given will update the record and its ingredients links in the database.

    Otherwise, if there is no "food_id" for an object, the system will assume the values
    given are for a new record in the database and will create a new record.

    :return: A JSON object of {"food":[<list of ids corresponding to food updated or created in the system]}
    """
    if not request.json or len(request.json) == 0:
        return jsonify({"error": "No JSON supplied"}), 400
    id_column = Food.__keys__[0]
    ret_val = []
    f = Food(db)
    j = request.json
    for food in j['food']:
        food_id = food.get(id_column, None)
        if food_id:
            f.find_by_id(food_id)
            f.update(**food)
            f.flush()
        else:
            f.create(**food)
        if j['nutrition']:
            try:
                f.nutrition = j['nutrition']
            except TypeError:
                return jsonify({"error": "Nutrition entries must be objects similar to nutritional_fact schema"})
        ret_val.append(f.id)

    return jsonify({"food": ret_val})


@app.route("/food/<int:id>/del/", methods=["DELETE"])
@nocache
def delete_food_item(id):
    """
    Remove a food item from the database according to its id
    :param id: The id of the food to delete
    :return: A JSON object with a "success" attribute specifying if anything was deleted or now
    """
    id_col = Food.__keys__[0]
    cursor = db.cursor()
    ret = cursor.execute("DELETE FROM mongoose.food WHERE {key}=%s".format(key=id_col), (id,))
    db.commit()
    cursor.close()
    return jsonify({"success": ret != 0})


@app.route("/food/all/", methods=["GET"])
@nocache
def get_all_food():
    """
    Get all food in the database
    :return: A JSON structure in the form of
    {"food":[<list of JSON objects representing food records in the database and their nutrition facts>]}
    """
    all_food = Food(db).all()
    for food in all_food:
        food['nutrition'] = NutritionalFact(db).find_by_id(food['fk_nfact_id']) or dict()

    return jsonify({"food": all_food})


@app.route("/food/<int:id>/", methods=["GET"])
@nocache
def get_food_by_id(id):
    """
    Get a single food record by its id
    :param id: The numeric id of the food record to find
    :return: A JSON object representation of the food record along with its nutritional facts
    """
    food = Food(db).find_by_id(id)
    if not food:
        return jsonify({"error": "No food with id {} found".format(id)}), 404

    food['nutrition'] = NutritionalFact(db).find_by_id(food['fk_nfact_id']) or dict()

    return jsonify(food)


@app.route("/food/<string:food_name>/", methods=["GET"])
@nocache
def get_food_by_name(food_name):
    """
    Get all foods that have the food name
    :param food_name: The food name to search for
    :return: A JSON structure in the form of
    {"food":[<list of JSON objects representing food records in the database and their nutrition facts>]}
    """
    food = Food(db).find_by_attribute("food_name", food_name, limit=-1)
    if not food:
        return jsonify({"error": "No food with name \"{}\" found".format(food_name)}), 404
    for f in food:
        f['nutrition'] = NutritionalFact(db).find_by_id(f['fk_nfact_id']) or dict()
    return jsonify({"food": food})


####################
# NUTRITION ROUTES #
####################
@app.route("/nutrition/", methods=["POST"])
@nocache
def nutrition_post():
    """
    Take in a JSON object in the form of
    {
        "facts":
        [
            {
                "nfact_id": 1,
                "sodium": <decimal with format dddd.ff>,
                "fat": <decimal with format dddd.ff>,
                "calories": <decimal with format dddd.ff>,
                "sugar": <decimal with format dddd.ff>,
                "sodium": <decimal with format dddd.ff>,
                "protein": <decimal with format dddd.ff>,
                "food_group": <one of the following strings: ('grain', 'meat', 'veggies')>,
                "amount": <decimal with format dddd.ff>,
            }, ...
        ]
    }

    Where for each entry in "facts" if there is an "nfact_id" attribute,
    it is assumed that we are updating an existing nutrition (because we wouldn't have the id otherwise).

    Otherwise, if there is no "nfact_id" for an object, the system will assume the values
    given are for a new record in the database and will create a new record.

    :return: A JSON object of
    {"nutritional_facts":[<list of ids corresponding to nutrition updated or created in the system]}
    """
    if not request.json or len(request.json) == 0:
        return jsonify({"error": "No JSON supplied"}), 400
    id_column = NutritionalFact.__keys__[0]
    ret_val = []
    nfact = NutritionalFact(db)
    j = request.json
    for fact in j['facts']:
        fact_id = fact.get(id_column, None)
        if fact_id:
            nfact.find_by_id(fact_id)
            nfact.update(**fact)
            nfact.flush()
        else:
            nfact.create(**fact)
        ret_val.append(nfact.id)
    return jsonify({"nutritional_facts": ret_val})


@app.route("/nutrition/<int:nfact_id>/del/", methods=["DELETE"])
@nocache
def nutrition_delete(nfact_id):
    """
    Given an id, delete the corresponding nutritional fact from the database.
    Note, this will also null the corresponding food's fk_nfact_id value.
    :param nfact_id: The id of the nutritional fact to delete
    :return: A JSON object with a success attribute that signifies if a row
     was removed from the database or not
    """
    id_column = NutritionalFact.__keys__[0]
    cursor = db.cursor()
    res = cursor.execute(
        "DELETE FROM {table} WHERE {id_column}=%s".format(table=NutritionalFact.__table__, id_column=id_column),
        (nfact_id,))
    db.commit()
    cursor.close()
    return jsonify({"success": res != 0})


@app.route("/nutrition/all/", methods=["GET"])
@nocache
def get_all_nutrition():
    """
    Get all nutrition facts in the database
    :return: A JSON object of the following structure
    {"nutritional_facts":[<list of objects with similar structure to nutritional_fact schema>]}
    """
    return jsonify({"nutritional_facts": NutritionalFact(db).all()})


@app.route('/nutrition/<int:nfact_id>/', methods=["GET"])
@nocache
def get_nutrition_by_id(nfact_id):
    """
    Get a nutrtional fact by its id
    :param nfact_id: The id of the nutritional fact
    :return: A JSON object representing the nutritional fact in the database
    """
    nutritional_fact = NutritionalFact(db).find_by_id(nfact_id)
    if not nutritional_fact:
        return jsonify({"error": "No nutritional fact with id {} found".format(nfact_id)}), 404

    return jsonify(nutritional_fact)


###############
# MENU ROUTES #
###############
@app.route("/menu/", methods=["POST"])
@nocache
def menu_post():
    """
    Take in a JSON object in the form of
    {
        "menus":
        [
            {
                "id": 1,
                "time_of_day": <one of ('breakfast', 'lunch', 'dinner')>,
                "date": <date string in the format YYYY-MM-DD>,
                "recipes": [a list of numeric (integer) ids representing the ids of recipes to associate to this menu]
            }, ...
        ]
    }

    Where for each entry in "menu" if there is an "id" attribute,
    it is assumed that we are updating an existing menu (because we wouldn't have the id otherwise),
    and the values given will update the record and its ingredients links in the database.

    Otherwise, if there is no "id" for an object, the system will assume the values
    given are for a new record in the database and will create a new record.

    :return: A JSON object of {"menu":[<list of ids corresponding to menu updated or created in the system]}
    """
    if not request.json or len(request.json) == 0:
        return jsonify({"error": "No JSON supplied"}), 400

    id_col = Menu.__keys__[0]
    menu = Menu(db)
    ret_val = []

    for m in request.json['menus']:
        menu_id = m.get(id_col, None)
        # check for data validity
        # Enforce a datetime format
        if m.get('date', None) and not check_date(m['date']):
            return jsonify({"error": "{} is not a valid date".format(m['date'])})
        # Enforce enums
        if m.get('time_of_day', None):
            if m['time_of_day'] not in Menu.__columns__['time_of_day']:
                return jsonify({"error": "{} is not a valid time of day".format(m['time_of_day'])})

        if menu_id:
            menu.find_by_id(menu_id)
            menu.update(**m)
            menu.flush()
        else:
            menu.create(**m)
        if m.get('recipes', None):
            try:
                menu.recipes = m['recipes']
            except TypeError:
                return jsonify({"error": "Invalid data. The recipes attribute must be a list of numeric recipe ids"})

        ret_val.append(menu.id)

    return jsonify({"menus": ret_val})


@app.route("/menu/all/", methods=["GET"])
@nocache
def get_all_menus():
    """
    Get all menu items in the database
    :return: A JSON format in the form of
    {"menus": [<list of JSON objects representing a menu record that also contains a list of recipe objects for that menu record>]}
    """
    cursor = db.cursor()
    menus = Menu(db).all()

    for menu in menus:
        cursor.execute(
            "SELECT *\n"
            "FROM mongoose.recipes\n"
            "WHERE rec_id IN (SELECT recipe_id\n"
            "                 FROM mongoose.serves\n"
            "                 WHERE menu_id = %s)",
            (menu['id'],))
        menu['recipes'] = cursor.fetchall()
    cursor.close()

    return jsonify({"menus": menus})


@app.route("/menu/<int:id>/", methods=["GET"])
@nocache
def get_menu_by_id(id):
    """
    Get a menu record by its id
    :param id: The id to find the record by
    :return: A JSON object representing a menu record along with its associated list of recipe objects
    """
    menu = Menu(db)
    menu_data = menu.find_by_id(id)

    if not menu_data:
        return jsonify({"error": "No menu with id {} found".format(id)}), 404

    menu_data['recipes'] = menu.recipes

    return jsonify(menu_data)


@app.route("/menu/<int:id>/del/", methods=["DELETE"])
@nocache
def delete_menu(id):
    """
    Delete a menu from the database by its id. Will also remove menu/recipe associations (but
    leave the recipe intact)
    :param id: The id of the menu to delete
    :return: A JSON object with a success attribute representing whether any rows were deleted or not
    """
    id_column = Menu.__keys__[0]
    cursor = db.cursor()
    res = cursor.execute("DELETE FROM {table} WHERE {column}=%s".format(table=Menu.__table__,
                                                                        column=id_column), (id,))
    cursor.close()
    db.commit()

    return jsonify({"success": res != 0})


@app.route("/menu/<string:time_of_day>/", methods=["GET"])
@nocache
def get_menus_by_time_of_day(time_of_day):
    """
    Get all menus for a time of day
    :param time_of_day: A lowercase string of one of the following: ('breakfast', 'lunch', 'dinner')
    :return: A JSON format in the form of
    {"menus": [<list of JSON objects representing a menu record that also contains a list of recipe objects for that menu record>]}
    """
    menus = Menu(db).find_by_attribute("time_of_day", time_of_day, limit=-1)
    if not menus:
        return jsonify({"error": "No menus with the time of day {} found".format(time_of_day)}), 404

    cursor = db.cursor()
    for menu in menus:
        cursor.execute(
            "SELECT *\n"
            "FROM mongoose.recipes\n"
            "WHERE rec_id IN (SELECT recipe_id\n"
            "                 FROM mongoose.serves\n"
            "                 WHERE menu_id = %s)",
            (menu['id'],))
        menu['recipes'] = cursor.fetchall()

    cursor.close()

    return jsonify({"menus": menus})


@app.route("/menu/<string:time_of_day>/<date:date>/", methods=["GET"])
@nocache
def get_menu_by_time_of_day_and_date(time_of_day, date):
    """
    Get a menu given its time of day and date
    :param time_of_day: A lowercase string of one of the following: ('breakfast', 'lunch', 'dinner')
    :param date: A date string in the form of YYYY-MM-DD
    :return: A JSON format in the form of
    {"menu": {<A JSON object representing a menu record that also contains a list of recipe objects for that menu record>}}
    """
    menu = Menu(db).find_by_attribute("date", date, limit=-1)
    menu = filter(lambda x: x['time_of_day'] == time_of_day, menu)
    if not menu:
        return jsonify({"error": "No menu found for the time of day {} at date {}".format(time_of_day, date)})

    return jsonify({"menu": menu})


@app.route("/menu/date/<date:date>/", methods=["GET"])
@nocache
def get_menu_by_date(date):
    """
    Get menus on a specific date
    :param date: A date string in the format YYYY-MM-DD
    :return: A JSON format in the form of
    {"menus": [<list of JSON objects representing a menu record that also contains a list of recipe objects for that menu record>]}
    """
    menus = Menu(db).find_by_attribute("date", date, limit=-1)
    if not menus:
        return jsonify({"error": "No menus for the date {}".format(date)}), 404

    cursor = db.cursor()
    for menu in menus:
        cursor.execute(
            "SELECT *\n"
            "FROM mongoose.recipes\n"
            "WHERE rec_id IN (SELECT recipe_id\n"
            "                 FROM mongoose.serves\n"
            "                 WHERE menu_id = %s)",
            (menu['id'],))
        menu['recipes'] = cursor.fetchall()
    cursor.close()

    return jsonify({"menus": menus})


@app.route("/menu/date/between/<date:begin>/<date:end>/", methods=["GET"])
@nocache
def get_menu_in_date_range(begin, end):
    """
    Get menus in-between two dates (inclusive)
    :param begin: A string in the format of YYYY-MM-DD specifying the start day (inclusive)
    :param end: A string in the format of YYYY-MM-DD specifying the end day (inclusive)
    :return: A JSON format in the form of
    {"menus": [<list of JSON objects representing a menu record that also contains a list of recipe objects for that menu record>]}
    """
    menus = Menu(db).all(cols={"date": ["BETWEEN", [begin, end]]})
    if not menus:
        return jsonify({"error": "No menus between dates {} and {} found".format(begin, end)}), 404

    cursor = db.cursor()
    for menu in menus:
        cursor.execute(
            "SELECT *\n"
            "FROM mongoose.recipes\n"
            "WHERE rec_id IN (SELECT recipe_id\n"
            "                 FROM mongoose.serves\n"
            "                 WHERE menu_id = %s)",
            (menu['id'],))
        menu['recipes'] = cursor.fetchall()
    cursor.close()

    return jsonify({"menus": menus})
