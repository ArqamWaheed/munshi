# Seed inquiries for the Gemma teacher (synthetic: NO real guest data)

Write these yourself; `gen_synthetic.py` reads every line starting with `- ` below and asks Gemma for
paraphrases that keep the same booking facts, plus new variants. Keep the typos: real WhatsApp has them.
Label conventions (the full list is SPEC_PROMPT in munshi/parser.py; data/eval.jsonl follows the same rules):
kal = tomorrow, parso = day after tomorrow, "is weekend" = coming Saturday, "agle hafte" = next Monday,
weekday names = next date after today, "X din" = X nights, nights = null when no stay length is given,
budget is per night, rooms default 1 (or ceil(guests/3) if guests > 4); "a"/"ek" + room states one room.
language (eval convention, not in SPEC_PROMPT): roman_urdu when the only English is hotel loanwords
(room and room types, budget, booking, advance, rate, check in/out, available); mixed once English phrases
appear ("2 adults", "we are", "per night", "need"). Because the teacher never saw this rule, eval_parser
also reports booking-field exact match (every parsed field except language).
Seeds must not copy rows of data/eval.jsonl (the eval set has to stay unseen).

## Roman Urdu
- AoA, kal 2 log ke liye 1 room chahiye 2 raat ke liye. rate kya hai?
- parso family aa rahi hai 5 bande, family room available hai? advance kitni deni hogi
- bhai is weekend 2 room chahiye, 4 log, budget 8 hazar per night tak
- 25 tareekh se 3 nights double room, kitne ka padega?
- kal raat ke liye koi room khali hai? sirf ek banda hun
- agle hafte jumma ko aayenge 6 log, 2 kamray, 2 din. naashta shamil hai?
- room ka rate bata dein, hum log aa rahe hain (no date, no count -> needs_clarification)
- sir 14 ko check in 16 ko check out, couple, double bed chahiye
- hum 3 bhai aur unki families, total 9 log, peer se jumeraat tak, 3 kamray
- shadi pe aa rahe hain, 8 log, 2 raat, sab se kam rate kya lagayen ge?
- mjhe kl k liye 1 kmra chahye 2 bndon k liye (heavy typos)
- 2 raat ka total 18 hazar budget hai, parso aayenge 2 log (total budget -> per night 9000)

## English / mixed
- Hi, need a room for 2 adults from Friday for 2 nights, what's the price?
- salam, do you have a twin room tomorow? 2 ppl 1 night. budget around 6k
- Family of 4 + 2 kids coming day after tomorrow, need family room 3 nights pls share rates
- is there any room avalable for tonight, 3 friends, cheapest option
- booking for 10 people, 4 rooms, 28 Oct to 30 Oct, corporate group, total budget 1 lakh
- Can u hold a room for us? will send advance through jazzcash (no date -> needs_clarification)
- Sir hum 2 couples hain, 2 double rooms chahiye this weekend, 1 night
- Need suite for honeymoon couple, 5 nights starting 12th

## Urdu script
- کل تین لوگوں کے لیے ایک کمرہ چاہیے، ایک رات
- اگلے ہفتے فیملی آ رہی ہے، چھ افراد، دو راتیں، ریٹ بتا دیں

## Typos / edge cases to cover
- "2 log" vs "2 bande" vs "do log" (Roman words for numbers: ek, do, teen, char, paanch, chhe)
- "kal" said late at night (still = tomorrow relative to TODAY)
- check-out given instead of nights; total budget instead of per-night
- urdu script message (language = urdu_script)
- WhatsApp export lines "[dd/mm/yyyy, hh:mm] Name: text" (redact() strips the header before any model)
