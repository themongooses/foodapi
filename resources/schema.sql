/*
 BEGIN ENTITY TABLES
 */
CREATE TABLE menu (
  id          INTEGER PRIMARY KEY,
  time_of_day NVARCHAR2(10) NOT NULL CHECK (time_of_day IN ('breakfast', 'lunch', 'dinner')),
  "date"      DATE          NOT NULL -- Are we gonna enforce date format here?
);
-- Auto-increment ID because Oracle is stupid
CREATE SEQUENCE menu_id_sequence START WITH 1 INCREMENT BY 1;
CREATE OR REPLACE TRIGGER menu_id_insert
BEFORE INSERT ON menu
FOR EACH ROW
  BEGIN
    SELECT menu_id_sequence.nextval
    INTO :NEW.ID
    FROM dual;
  END;
/

CREATE TABLE recipes (
  rec_id       INT PRIMARY KEY,
  rec_name     NVARCHAR2(50) NOT NULL,
  instructions CLOB, -- character blob
  -- not sure on these enums
  category     NVARCHAR2(10) DEFAULT 'entree' CHECK (category IN ('entree', 'appetizer', 'dessert'))
);

-- Auto-increment ID because Oracle is stupid
CREATE SEQUENCE recipe_id_sequence START WITH 1 INCREMENT BY 1;
CREATE OR REPLACE TRIGGER recipe_id_insert
BEFORE INSERT ON recipes
FOR EACH ROW
  BEGIN
    SELECT recipe_id_sequence.nextval
    INTO :NEW.rec_id
    FROM dual;
  END;
/

CREATE TABLE food (
  food_id     INT PRIMARY KEY,
  in_fridge   CHAR CHECK (in_fridge IN (0, 1)), -- not sure what this means
  food_name   NVARCHAR2(50) NOT NULL,
  fk_nfact_id INT REFERENCES nutritional_fact (nfact_id)
);

CREATE TABLE nutritional_fact (
  nfact_id   INT PRIMARY KEY,
  -- Assuming that we'll need precision in terms of 123.45
  sodium     NUMBER(6, 2) DEFAULT 0.00,
  fat        NUMBER(6, 2) DEFAULT 0.00,
  calories   NUMBER(6, 2) DEFAULT 0.00,
  sugar      NUMBER(6, 2) DEFAULT 0.00,
  protein    NUMBER(6, 2) DEFAULT 0.00,
  food_group NVARCHAR2(15) CHECK (food_group IN ('grain', 'meat', 'veggies')), -- Not sure what enums you need
  amount     NUMBER(6, 2) DEFAULT 0.00
);

-- Auto-increment ID because Oracle is stupid
CREATE SEQUENCE nutritional_fact_id_sequence START WITH 1 INCREMENT BY 1;
CREATE OR REPLACE TRIGGER nutritional_fact_id_insert
BEFORE INSERT ON nutritional_fact
FOR EACH ROW
  BEGIN
    SELECT nutritional_fact_id_sequence.nextval
    INTO :NEW.nfact_id
    FROM dual;
  END;
/

-- Auto-increment ID because Oracle is stupid
CREATE SEQUENCE food_id_sequence START WITH 1 INCREMENT BY 1;
CREATE OR REPLACE TRIGGER food_id_insert
BEFORE INSERT ON food
FOR EACH ROW
  BEGIN
    SELECT food_id_sequence.nextval
    INTO :NEW.food_id
    FROM dual;
  END;
/

/*
 * BEGIN PIVOT TABLES FOR MANY TO MANY RELATIONS
 */

CREATE TABLE serves (
  menu_id REFERENCES menu (id),
  recipe_id INT REFERENCES recipes (rec_id)
);

CREATE TABLE ingredients (
  recipe_id INT REFERENCES recipes (rec_id),
  food_id   INT REFERENCES food (food_id)
);