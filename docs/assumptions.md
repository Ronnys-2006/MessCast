# Assumptions table (dataset is SYNTHETIC)

`data/mess_synthetic_data.csv` is simulated from documented assumptions with a fixed random seed (42).
Results validate our pipeline; they are **not** evidence about a real mess.

> NOTE for Rohan: the original `generate_mess_data.py` was not part of this build. The "Value" column below was measured
> from the CSV itself. Replace it with the real numbers from your generator, add the "Why / source" (mess manager or
> hostel residents), and drop `generate_mess_data.py` into `src/`.

| Assumption | Value (observed in the CSV) | Why / source |
|---|---|---|
| Period / size | 150 days (2025-08-04 to 2025-12-31) x 3 meals = 450 rows, 17 columns | Project brief |
| Hostel strength | 1000 students, constant | Common-sense estimate |
| Plates cooked today (fixed) | Breakfast 650, Lunch 850, Dinner 900 | Mess cooks a fixed amount (brief) |
| Share of hostel eating, average | Breakfast ~51%, Lunch ~78%, Dinner ~82% | TO CONFIRM with mess manager |
| Weekend effect | about 10% lower than weekdays (Sat/Sun lowest) | TO CONFIRM |
| Holiday effect | about -16% | TO CONFIRM (students go home) |
| Vacation effect | about -45% (18-26 Oct 2025) | TO CONFIRM |
| Exam-period effect | about +7% (22 Sep-3 Oct, 1-13 Dec) | TO CONFIRM (students stay in) |
| Event effect | about +8% (3 days) | TO CONFIRM |
| Special dish effect | about +6% overall; Paneer Special, Chicken Curry, Veg Biryani flagged special | TO CONFIRM |
| Rain effect | slightly positive (corr 0.08; >5 mm days about +5%) | Students eat in mess when it rains |
| Leftover weight | 0.35 kg per plate | Common-sense estimate |
| Missing values | 9 of 450 plates_served (2%), blank on purpose, with leftover/shortage columns blank too | Practise cleaning |
| Random seed | 42 | Reproducibility |

Menus: Breakfast = Poha, Upma, Sandwich, Idli, Aloo Paratha; Lunch = Paneer Special, Dal Rice, Chole Bhature,
Regular Veg Thali, Veg Biryani; Dinner = Chicken Curry, Dal Rice, Paneer Special, Egg Curry, Regular Veg Thali.
