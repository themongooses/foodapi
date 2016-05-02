# INSERT INTO menu(TIME_OF_DAY, "date") VALUES('breakfast', TO_DATE('2016/05/01', 'yyyy/mm/dd'));
# INSERT INTO menu(TIME_OF_DAY, "date") VALUES('lunch', TO_DATE('2016/05/01', 'yyyy/mm/dd'));
# INSERT INTO mongoose.menu (time_of_day, date) VALUES ('breakfast', CURRENT_DATE());
# INSERT INTO mongoose.menu (time_of_day, date) VALUES ('lunch', CURRENT_DATE());
# INSERT INTO mongoose.menu (time_of_day, date) VALUES ('dinner', CURRENT_DATE());
INSERT INTO mongoose.food (in_fridge, food_name, fk_nfact_id) VALUES (1, 'Pizza', 1);
INSERT INTO mongoose.food (in_fridge, food_name, fk_nfact_id) VALUES (0, 'Beer', 2);
INSERT INTO mongoose.food (in_fridge, food_name, fk_nfact_id) VALUES (1, 'Salmon', 3);

INSERT INTO mongoose.recipes(rec_name, instructions, category) VALUES('foo', 'Marshmellow salad has to have a diced, small watermelon component.', 'entree');
INSERT INTO mongoose.recipes(rec_name, instructions, category) VALUES('bar', 'Cut watermelon carefully minced, then mix with rice vinegar and serve immediately in basin.', 'dessert');

INSERT INTO mongoose.ingredients(recipe_id, food_id) VALUES(1,1);
INSERT INTO mongoose.ingredients(recipe_id, food_id) VALUES(1,2);

INSERT INTO nutritional_fact(sodium, fat, calories, sugar, protein, food_group, amount) VALUES(12.343, 11.11, 5.3, 0, 10.01, 'grain', 11.2);