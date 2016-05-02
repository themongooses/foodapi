CREATE TABLE menu (
  id          INTEGER PRIMARY KEY AUTO_INCREMENT,
  time_of_day ENUM ('breakfast', 'lunch', 'dinner'),
  `date`      DATE NOT NULL -- Are we gonna enforce date format here?
);

CREATE TABLE recipes (
  rec_id       INT PRIMARY KEY                         AUTO_INCREMENT,
  rec_name     VARCHAR(50) NOT NULL,
  instructions TEXT, -- character blob
  -- not sure on these enums
  category     ENUM ('entree', 'appetizer', 'dessert') DEFAULT 'entree'
);

CREATE TABLE nutritional_fact (
  nfact_id   INT PRIMARY KEY AUTO_INCREMENT,
  -- Assuming that we'll need precision in terms of 123.45
  sodium     DECIMAL(6,2)         DEFAULT 0.00,
  fat        DECIMAL(6,2)         DEFAULT 0.00,
  calories   DECIMAL(6,2)         DEFAULT 0.00,
  sugar      DECIMAL(6,2)         DEFAULT 0.00,
  protein    DECIMAL(6,2)         DEFAULT 0.00,
  food_group ENUM ('grain', 'meat', 'veggies') NOT NULL, -- Not sure what enums you need
  amount     DECIMAL(6,2)         DEFAULT 0.00
);

CREATE TABLE food (
  food_id     INT PRIMARY KEY AUTO_INCREMENT,
  in_fridge   BOOLEAN         DEFAULT TRUE,
  food_name   VARCHAR(50) NOT NULL,
  fk_nfact_id INT REFERENCES nutritional_fact (nfact_id)
);

CREATE TABLE serves (
  menu_id   INT REFERENCES menu (id),
  recipe_id INT REFERENCES recipes (rec_id)
);

CREATE TABLE ingredients (
  recipe_id INT REFERENCES recipes (rec_id),
  food_id   INT REFERENCES food (food_id)
);

DELIMITER $$
CREATE TRIGGER on_food_delete
BEFORE DELETE ON food
FOR EACH ROW
  BEGIN
    -- When a food is deleted, its nutritional fact should also be deleted
    DELETE FROM nutritional_fact
    WHERE nfact_id = OLD.fk_nfact_id;
    -- And its entry binding it to a recipe should also be deleted
    DELETE FROM ingredients
    WHERE food_id = OLD.food_id;
  END $$;
DELIMITER ;

DELIMITER $$
CREATE TRIGGER on_recipe_delete
BEFORE DELETE ON recipes
FOR EACH ROW
  BEGIN
    -- When a recipe is deleted, its entry in the ingredients table should also be deleted
    DELETE FROM ingredients
    WHERE recipe_id = OLD.rec_id;
    -- And its entry binding it to a menu should also be deleted
    DELETE FROM serves
    WHERE recipe_id = OLD.rec_id;
  END $$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER on_menu_delete
BEFORE DELETE ON menu
FOR EACH ROW
  BEGIN
    -- When a menu item is deleted, its entry in the serves table should be deleted
    DELETE FROM serves
    WHERE menu_id = OLD.id;
  END $$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER on_nutritional_fact_delete
BEFORE DELETE ON nutritional_fact
  FOR EACH ROW
  BEGIN
    -- When a nutritional fact is deleted, its id on the food entry should be set to null
    UPDATE food SET fk_nfact_id=NULL WHERE fk_nfact_id=OLD.nfact_id;
  END $$
DELIMITER ;