# Pic a Dish — checked demo photos

Tested against https://www.picadish.photo/api/detect on 2026-10-18. These are selected demo cases, not an accuracy benchmark. No model weights or confidence thresholds were changed. Nine photos return multiple ingredient types; only the first six avoid obvious incorrect ingredient labels. Not every visible ingredient is detected. Files 02 and 06 are lower-resolution backups.

Start with 04 for a meal, or 01 for vegetables. Upload the original photo; review suggestions, remove errors, and add missing ingredients before generating recipes. This verifies detection only, not Backboard configuration.

Photos retain their source attribution below. Ownership remains with original photographers/publishers; redistribution rights have not been verified.

## Files

### 01-vegetable-table.jpg
- Live output (highest confidence per label): tomato 71%, cucumber 69%, pepper 64%.
- Review: Good demo: tomato, cucumber and pepper boxes match. Misses carrot, lettuce and radishes.
- Source: [https://cn.best-wallpaper.net/Tomato-cucumber-carrot-chili-lettuce-vegetables_wallpapers.html](https://cn.best-wallpaper.net/Tomato-cucumber-carrot-chili-lettuce-vegetables_wallpapers.html)
- Original: [image](https://s2.best-wallpaper.net/wallpaper/1920x1440/2105/Tomato-cucumber-carrot-chili-lettuce-vegetables_1920x1440.jpg)

### 02-apple-banana-rustic.jpg
- Live output (highest confidence per label): apple 91%, banana 79%.
- Review: Good demo: apples and bananas detected. Lower-resolution original (600 × 400), included because detection is strong.
- Source: [https://tt.jxnews.com.cn/news/2474875](https://tt.jxnews.com.cn/news/2474875)
- Original: [image](https://pic.tt.jxnews.com.cn/upload/news/2474875/sources/6b60732f-4027-4b9e-8fe4-4375b600b2b3.jpg)

### 03-fruit-trio.jpg
- Live output (highest confidence per label): apple 76%, banana 66%.
- Review: Good demo: apple and banana detected; lemon is missed.
- Source: [https://m.economictimes.com/magazines/panache/apple-vs-lemon-vs-banana-who-wins-the-healthiest-fruit-trophy-science-has-the-answer/amp_articleshow/122926096.cms](https://m.economictimes.com/magazines/panache/apple-vs-lemon-vs-banana-who-wins-the-healthiest-fruit-trophy-science-has-the-answer/amp_articleshow/122926096.cms)
- Original: [image](https://m.economictimes.com/thumb/msid-122926263%2Cwidth-1600%2Cheight-900%2Cresizemode-4%2Cimgsize-24526/lemon-tops-nutritional-chart-in-study-by-william-paterson-university.jpg)

### 04-chicken-potatoes.jpg
- Live output (highest confidence per label): carrot 70%, chicken 59%, potato 43%.
- Review: Best meal demo: chicken, carrot and potato detected. Misses broccoli, garlic, eggplant, milk and oil.
- Source: [https://www.lsm.lv/raksts/dzive--stils/virtuve/27.03.2025-viena-vesela-vista-cetri-dazadi-edieni-budzeta-receptes-gardam-maltitem.a593064/](https://www.lsm.lv/raksts/dzive--stils/virtuve/27.03.2025-viena-vesela-vista-cetri-dazadi-edieni-budzeta-receptes-gardam-maltitem.a593064/)
- Original: [image](https://static.lsm.lv/media/2025/03/large/1/q1su.jpg)

### 05-baking-light.jpg
- Live output (highest confidence per label): egg 69%, milk 58%.
- Review: Good demo: eggs and milk detected. Misses butter and flour; one egg box covers an eggshell.
- Source: [https://www.diredonna.it/8-trucchi-per-fare-dolci-light-3090959.html](https://www.diredonna.it/8-trucchi-per-fare-dolci-light-3090959.html)
- Original: [image](https://cdn.diredonna.it/app/uploads/2016/04/shutterstock_321535031.jpg)

### 06-mac-cheese.jpg
- Live output (highest confidence per label): butter 74%, milk 59%.
- Review: Backup: butter and milk detected. Misses eggs, cheese, flour and garlic. Small original (386 × 576); do not present as high resolution.
- Source: [https://userealbutter.com/2013/04/03/mac-and-cheese-recipe/](https://userealbutter.com/2013/04/03/mac-and-cheese-recipe/)
- Original: [image](https://userealbutter.com/recipe_photos/mac-and-cheese14.jpg)

### 07-root-vegetables.jpg
- Live output (highest confidence per label): potato 92%, carrot 74%.
- Review: Correction demo only: real potatoes and carrots detected, but some onions are wrongly boxed as potatoes. Cabbage and beet are missed.
- Source: [https://vidomosti-ua.com/health/129280](https://vidomosti-ua.com/health/129280)
- Original: [image](https://vidomosti-ua.com/photo/original-1508761734.JPG)

### 08-potato-garlic-basket.jpg
- Live output (highest confidence per label): garlic 76%, potato 62%.
- Review: Correction demo only: potatoes and some garlic detected; onions are also incorrectly labeled garlic. Highest garlic score is an onion, not a correct garlic detection.
- Source: [https://www.onmanorama.com/lifestyle/health/2026/01/16/potatoes-onions-storing-together-toxic.html](https://www.onmanorama.com/lifestyle/health/2026/01/16/potatoes-onions-storing-together-toxic.html)
- Original: [image](https://img.onmanorama.com/content/dam/mm/en/archive/lifestyle/health/images/2026/1/16/onion-potato.jpg)

### 09-chicken-board.jpg
- Live output (highest confidence per label): chicken 66%, pepper 57%, broccoli 51%, mushroom 47%.
- Review: Correction demo only: chicken, broccoli and mushroom detected; pepper is a false label on a tomato. Misses garlic, onion and lemon.
- Source: [https://www.lacucinaitaliana.it/ricetta/secondi/fuso-di-pollo-alla-senape/](https://www.lacucinaitaliana.it/ricetta/secondi/fuso-di-pollo-alla-senape/)
- Original: [image](https://media-assets.lacucinaitaliana.it/photos/620b61e3b758df3090bd39f6/1%3A1/pass/undefined)

### 10-bakery-table.jpg
- Live output (highest confidence per label): egg 89%.
- Review: Manual-entry fallback only: detects two eggs, but misses milk, butter and flour. Does not pass the multiple-ingredient detection requirement.
- Source: [https://holeygrailbakery.ca/](https://holeygrailbakery.ca/)
- Original: [image](https://img1.wsimg.com/isteam/stock/104680)
