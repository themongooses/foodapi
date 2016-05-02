from collections import OrderedDict
from datetime import date


class DbEntity:
    cursor = None
    db = None
    data = OrderedDict()
    __table__ = None
    __columns__ = dict()
    __keys__ = []
    __foreign_keys__ = dict()

    def __init__(self, db):
        self.db = db
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM {table} LIMIT 1".format(table=self.__table__))
        self.data = OrderedDict(**{i[0]: None for i in cursor.description})
        if not self.__columns__:
            self.__columns__ = self.data.copy()
        cursor.close()
        self.save()

    def find_by_id(self, id):
        cursor = self.db.cursor()
        placeholder, value = self.prep_for_query(id)
        sql = "SELECT * FROM {table} WHERE {key}={placeholder} LIMIT 1".format(table=self.__table__,
                                                                               key=self.__keys__[0],
                                                                               placeholder=placeholder)
        cursor.execute(sql, value)
        ret = cursor.fetchone()

        if ret:
            self.data.update(ret)
        else:
            self.data = OrderedDict(**{i[0]: None for i in cursor.description})
        cursor.close()
        self.save()
        return ret

    def find_by_attribute(self, attribute, value, limit=1):
        if attribute not in self.__columns__:
            raise TypeError("Invalid column name")
        cursor = self.db.cursor()
        placeholder, value = self.prep_for_query(value)
        sql = "SELECT * FROM {table} WHERE {attr}={placeholder}{limit}".format(table=self.__table__,
                                                                               attr=attribute,
                                                                               placeholder=placeholder,
                                                                               limit=" LIMIT {}".format(
                                                                                   limit) if limit > 0 else "")

        cursor.execute(sql, value)
        ret = cursor.fetchall()
        cursor.close()

        if limit == 1 and ret:
            self.data.update(ret[0])

        self.save()

        return ret

    def update(self, **values):
        self.data.update(values)

    def all(self, combinator="AND", cols=None):
        if cols is None:
            cols = dict()
        cursor = self.db.cursor()
        values = []
        where_string = ""
        if cols:
            where_string = " {} ".format(combinator.strip())
            conditions = []
            for key, value in cols.iteritems():
                if value[0].upper() == "BETWEEN":
                    values.append(self.prep_for_query(value[1][0])[1])
                    values.append(self.prep_for_query(value[1][1])[1])
                    conditions.append("{} {} %s AND %s".format(key, value[0]))
                else:
                    values.append(self.prep_for_query(value[1])[1])
                    conditions.append("{}{}%s".format(key, value[0]))

            where_string = "WHERE {}".format(where_string.join(conditions))
        sql = "SELECT * FROM {table} {where_string}".format(table=self.__table__,
                                                            where_string=where_string)
        cursor.execute(sql, tuple(values))
        ret = cursor.fetchall()
        cursor.close()
        self.save()

        return ret

    def create(self, **columns):
        self.data.update(columns)
        columns = [column for column in self.__columns__ if
                   column not in self.__keys__ and self.data[column] is not None]
        values = [self.prep_for_query(value)[1] for key, value in self.data.iteritems() if
                  key in columns and value is not None]
        placeholders = ", ".join(["%s" for _ in range(len(values))])

        sql = "INSERT INTO {table} ({columns}) VALUES ({placeholders})".format(table=self.__table__,
                                                                               columns=", ".join(columns),
                                                                               placeholders=placeholders)
        cursor = self.db.cursor()
        cursor.execute(sql, tuple(values))
        self.save()
        cursor.execute("SELECT MAX({key}) AS id FROM {table} LIMIT 1".format(key=self.__keys__[0],
                                                                             table=self.__table__))
        self.data[self.__keys__[0]] = cursor.fetchone()['id']
        cursor.close()
        self.save()

    def __getitem__(self, item):
        return self.data.get(item, None)

    def __setitem__(self, key, value):
        self.data[key] = value

    @property
    def id(self):
        return self.data.get(self.__keys__[0], None)

    def prep_for_query(self, value):
        """
        Given a value, returns a placeholder and the proper
        value for insertion into a query string
        :param value:
        :return:
        """
        if isinstance(value, date):
            value = value.strftime('%Y-%m-%d')
        return '%s', value

    def save(self):
        """
        Flushes changes done by the cursor to the database
        :return:
        """
        self.db.commit()

    def flush(self):
        columns = [column for column in self.__columns__ if column not in self.__keys__ and self.data[column] is not None]
        values = [self.prep_for_query(value)[1] for key, value in self.data.iteritems() if
                  key in columns and value is not None]
        placeholders = ", ".join("{}=%s".format(column) for column in columns)
        key = self.__keys__[0]
        key_value = self.prep_for_query(self.data[key])[1]
        sql = "UPDATE {table} SET {placeholders} WHERE {key}={key_value}".format(table=self.__table__,
                                                                                 placeholders=placeholders,
                                                                                 key=key,
                                                                                 key_value=key_value)
        cursor = self.db.cursor()
        cursor.execute(sql, tuple(values))
        cursor.close()
        self.save()


class Food(DbEntity):
    __table__ = "food"
    __columns__ = {
        "food_id": int,
        "in_fridge": bool,
        "food_name": str,
        "fk_nfact_id": int
    }
    __keys__ = ["food_id"]
    __foreign_keys__ = {
        "fk_nfact_id": "nutritional_fact.nfact_id"
    }

    def __init__(self, db):
        DbEntity.__init__(self, db)

    @property
    def nutrition(self):
        if not self.data.get('fk_nfact_id', None):
            self.data['nutrition'] = {}
        else:
            self.data['nutrition'] = NutritionalFact(self.db).find_by_id(self.data['fk_nfact_id'])

        return self.data['nutrition']

    @nutrition.setter
    def nutrition(self, nutrition_facts):
        if not isinstance(nutrition_facts, dict):
            raise TypeError("Attempting to set Food.nutrition with a non-dict object")
        if len(nutrition_facts) == 0 and self.data.get('fk_nfact_id', None):
            cursor = self.db.cursor()
            cursor.execute("DELETE FROM mongoose.nutritional_fact WHERE nfact_id=%s", (self.data['fk_nfact_id']))
            self.data['nutrition'] = {}
            self.save()
            cursor.close()
        else:
            nfact = NutritionalFact(self.db)
            nfact.find_by_id(self.data['fk_nfact_id'])
            nfact.update(**nutrition_facts)
            self.data['nutrition'] = nfact.data


class NutritionalFact(DbEntity):
    __table__ = "nutritional_fact"
    __columns__ = {
        "nfact_id": int,
        "sodium": float,
        "fat": float,
        "calories": float,
        "sugar": float,
        "protein": float,
        "food_group": ('grain', 'meat', 'veggies'),
        "amount": float
    }
    __keys__ = ["nfact_id"]

    def __init__(self, db):
        DbEntity.__init__(self, db)


class Recipe(DbEntity):
    __table__ = "recipes"
    __columns__ = {
        "rec_id": int,
        "rec_name": str,
        "instructions": str,
        "category": ('entree', 'appetizer', 'dessert')
    }
    __keys__ = ["rec_id"]

    def __init__(self, db):
        DbEntity.__init__(self, db)

    @property
    def ingredients(self):
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT * FROM mongoose.food WHERE food_id IN (SELECT food_id FROM mongoose.ingredients WHERE recipe_id=%s)",
            (self.id,))
        self.data['ingredients'] = cursor.fetchall()
        return self.data['ingredients']

    @ingredients.setter
    def ingredients(self, ingredient_ids):
        if not isinstance(ingredient_ids, list):
            raise TypeError("Attempting to set Recipe.ingredients property with a non-list object")
        if len(ingredient_ids) > 0 and not all(type(x) == int for x in ingredient_ids):
            raise TypeError("Non-integers being passed to Recipe.ingredients")
        cursor = self.db.cursor()
        # clear out the cached recipe objects ids
        if self.data.get('ingredients', None):
            del self.data['ingredients']
        # Delete the recipe-to-menu records
        cursor.execute("DELETE FROM mongoose.ingredients WHERE recipe_id=%s", (self.id,))
        self.save()
        # insert the new associations if they are there
        if len(ingredient_ids) > 0:
            cursor.executemany("INSERT INTO mongoose.ingredients(recipe_id, food_id) VALUES (%s, %s)",
                               [(self.id, food_id) for food_id in ingredient_ids])
            self.save()
        # rebuild the cache
        cursor.execute(
            "SELECT * FROM mongoose.food WHERE food_id IN ({placeholders})".format(
                placeholders=", ".join(["%s" for _ in range(len(ingredient_ids))])),
            tuple(ingredient_ids))
        self.data['ingredients'] = cursor.fetchall()
        cursor.close()
        self.save()


class Menu(DbEntity):
    __table__ = "menu"
    __columns__ = {
        "id": int,
        "time_of_day": ('breakfast', 'lunch', 'dinner'),
        "date": date
    }
    __keys__ = ["id"]

    def __init__(self, db):
        DbEntity.__init__(self, db)

    @property
    def recipes(self):
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT * FROM mongoose.recipes WHERE rec_id IN (SELECT recipe_id FROM mongoose.serves WHERE menu_id=%s)",
            (self.id,))
        self.data['recipes'] = cursor.fetchall()
        cursor.close()
        self.save()
        return self.data['recipes']

    @recipes.setter
    def recipes(self, recipe_ids):
        if not isinstance(recipe_ids, list):
            raise TypeError("Attempting to set Menu.recipes property with a non-list object")
        if not all(type(x) == int for x in recipe_ids):
            raise TypeError("Non-integers being passed to Menu.recipes")
        cursor = self.db.cursor()
        # clear out the cached recipe objects ids
        if self.data.get('recipes', None):
            del self.data['recipes']
        # Delete the recipe-to-menu records
        cursor.execute("DELETE FROM mongoose.serves WHERE menu_id=%s", (self.id,))
        self.save()
        # insert the new associations
        cursor.executemany("INSERT INTO mongoose.serves(menu_id, recipe_id) VALUES (%s, %s)",
                           [(self.id, recipe_id) for recipe_id in recipe_ids])
        self.save()
        # rebuild the cache
        cursor.execute(
            "SELECT * FROM mongoose.recipes WHERE rec_id IN ({placeholders})".format(
                placeholders=", ".join(["%s" for _ in range(len(recipe_ids))])),
            tuple(recipe_ids))

        self.data['recipes'] = cursor.fetchall()
        cursor.close()
        self.save()
