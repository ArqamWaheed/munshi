# Teacher-label spot check (30 random rows of data/train.jsonl, seed 7)

Mark each row [x] if every field is right under the conventions in data/seed_templates.md; otherwise
write what is wrong. The error rate is the honest label-noise number for the post.

1. [ ] TODAY 2026-11-14: `Bhai suite ka kya rate hai? family ke liye, 4 log`  
   -> {"guests": 4, "rooms": 2, "room_type": "family", "language": "roman_urdu", "needs_clarification": true}
2. [ ] TODAY 2026-10-20: `advance kitni deni hogi? 4 log hain hum`  
   -> {"guests": 4, "rooms": 2, "language": "roman_urdu", "needs_clarification": true}
3. [ ] TODAY 2026-10-16: `is coming friday 4 people, 2 nights, budget 8k per night max`  
   -> {"check_in": "2026-10-23", "nights": 2, "guests": 4, "rooms": 2, "budget_pkr": 8000, "language": "english", "needs_clarification": false}
4. [ ] TODAY 2026-10-17: `assalam o alikum, agle hafte jumma ko aayenge 6 log, 2 kamray, 2 din. naashta shamil hai?`  
   -> {"check_in": "2026-10-23", "nights": 2, "guests": 6, "rooms": 2, "language": "roman_urdu", "needs_clarification": false}
5. [ ] TODAY 2026-10-20: `is there any discount for 4 nights? 2 people, Islamabad stay`  
   -> {"nights": 4, "guests": 2, "rooms": 1, "language": "english", "needs_clarification": true}
6. [ ] TODAY 2026-10-28: `Assalam o alaikum, 4 log hain family, 2 kids bhi hain, day after tomorrow se 3 nights ke liye family room chahiye. Rates bhej dein.`  
   -> {"check_in": "2026-10-30", "nights": 3, "guests": 4, "rooms": 1, "room_type": "family", "language": "roman_urdu", "needs_clarification": false}
7. [ ] TODAY 2026-10-26: `Hi, need a room for 2 adults from Friday for 2 nights, what's the price? Islamabad area`  
   -> {"check_in": "2026-10-30", "nights": 2, "guests": 2, "rooms": 1, "language": "english", "needs_clarification": false}
8. [ ] TODAY 2026-10-29: `Islamabad mein 1 room chahiye, 3 nights, budget 8k per night`  
   -> {"nights": 3, "rooms": 1, "budget_pkr": 8000, "language": "roman_urdu", "needs_clarification": true}
9. [ ] TODAY 2026-10-21: `2 log hain hum, parso aana hai, advance kitni deni hogi?`  
   -> {"check_in": "2026-10-23", "guests": 2, "rooms": 1, "language": "roman_urdu", "needs_clarification": true}
10. [ ] TODAY 2026-11-07: `is weekend Swat ke liye 12 log hain, 3 rooms chahiye, advance kitni deni hogi?`  
   -> {"check_in": "2026-11-07", "guests": 12, "rooms": 3, "language": "roman_urdu", "needs_clarification": true}
11. [ ] TODAY 2026-11-06: `Salam, Murree mein room chahiye 2 nights k liye, budget 8k approx hai total. available?`  
   -> {"nights": 2, "rooms": 1, "budget_pkr": 4000, "language": "roman_urdu", "needs_clarification": true}
12. [ ] TODAY 2026-10-01: `any availability for 15th? 4 adults, need 2 rooms`  
   -> {"check_in": "2026-10-15", "guests": 4, "rooms": 2, "language": "english", "needs_clarification": true}
13. [ ] TODAY 2026-11-22: `naran ke liye 12 log hain, 2 kamray mil jayenge kya?`  
   -> {"guests": 12, "rooms": 2, "language": "roman_urdu", "needs_clarification": true}
14. [ ] TODAY 2026-10-30: `Assalam o alaikum, Murree ke liye room chahiye kal se, 4 log hain hum, budget 8k tak hai`  
   -> {"check_in": "2026-10-31", "guests": 4, "rooms": 2, "budget_pkr": 8000, "language": "roman_urdu", "needs_clarification": true}
15. [ ] TODAY 2026-10-16: `کل تین لوگوں کے لیے ایک کمرہ چاہیے، ایک رات`  
   -> {"check_in": "2026-10-17", "nights": 1, "guests": 3, "rooms": 1, "language": "roman_urdu", "needs_clarification": false}
16. [ ] TODAY 2026-11-17: `we are coming to Swat, 5 nights, 12 log, group booking rates bta dein`  
   -> {"nights": 5, "guests": 12, "rooms": 4, "language": "english", "needs_clarification": true}
17. [ ] TODAY 2026-10-11: `Murree mein koi room hai kal ke liye? 2 log, budget 5k tak hai`  
   -> {"check_in": "2026-10-12", "guests": 2, "rooms": 1, "budget_pkr": 5000, "language": "roman_urdu", "needs_clarification": true}
18. [ ] TODAY 2026-11-01: `Assalam o alaikum, 1 room chahiye 3 nights ke liye, budget 10k hai total`  
   -> {"nights": 3, "rooms": 1, "budget_pkr": 3333, "language": "roman_urdu", "needs_clarification": true}
19. [ ] TODAY 2026-11-16: `bhai advance kitni deni hogi room confirm karnay k liye? 2 log hain aur 1 raat rukhna hai`  
   -> {"nights": 1, "guests": 2, "rooms": 1, "language": "roman_urdu", "needs_clarification": true}
20. [ ] TODAY 2026-11-05: `bhai 2 rooms chahiye Islamabad mein, parso k liye, advance kitni lenge?`  
   -> {"check_in": "2026-11-07", "rooms": 2, "language": "roman_urdu", "needs_clarification": true}
21. [ ] TODAY 2026-10-15: `hello, check in 20 ko hai, kitna advance dena hoga?`  
   -> {"check_in": "2026-10-20", "rooms": 1, "language": "mixed", "needs_clarification": true}
22. [ ] TODAY 2026-11-05: `hello, need booking for 4 people, 3 nights, 15 Nov to 18 Nov. kitna advance dena hoga?`  
   -> {"check_in": "2026-11-15", "nights": 3, "guests": 4, "rooms": 2, "language": "mixed", "needs_clarification": false}
23. [ ] TODAY 2026-11-29: `Murree mein single room kitnay ka hai? 1 night ke liye`  
   -> {"nights": 1, "rooms": 1, "room_type": "single", "language": "roman_urdu", "needs_clarification": true}
24. [ ] TODAY 2026-10-14: `sir 5 nights ke liye suite chahiye, budget 40 hazar tak hai, can u manage?`  
   -> {"nights": 5, "rooms": 1, "room_type": "suite", "budget_pkr": 8000, "language": "mixed", "needs_clarification": true}
25. [ ] TODAY 2026-11-07: `Naran mein 12 ko check in 15 ko check out, 2 rooms chahiye, family of 6, kitna advance dena hoga?`  
   -> {"check_in": "2026-11-12", "nights": 3, "guests": 6, "rooms": 2, "room_type": "family", "language": "roman_urdu", "needs_clarification": false}
26. [ ] TODAY 2026-10-08: `5 log hain hum, 2 rooms chahiye 3 din ke liye, advance kitni deni hogi?`  
   -> {"nights": 3, "guests": 5, "rooms": 2, "language": "roman_urdu", "needs_clarification": true}
27. [ ] TODAY 2026-11-18: `Swat mein room available hai? 4 log, 2 days, parso aana hai`  
   -> {"check_in": "2026-11-20", "nights": 2, "guests": 4, "rooms": 2, "language": "roman_urdu", "needs_clarification": false}
28. [ ] TODAY 2026-11-06: `Naran weather kaisa hai abhi? Need a big room for 5 people for 2 days`  
   -> {"nights": 2, "guests": 5, "rooms": 2, "room_type": "family", "language": "mixed", "needs_clarification": true}
29. [ ] TODAY 2026-11-06: `hello, is there availability for 2 nights? budget 5k per night max`  
   -> {"nights": 2, "rooms": 1, "budget_pkr": 5000, "language": "english", "needs_clarification": true}
30. [ ] TODAY 2026-10-25: `AoA, 10 log hain hum, kitne rooms chahiye honge aur per night kya rate hai?`  
   -> {"guests": 10, "rooms": 4, "language": "roman_urdu", "needs_clarification": true}
