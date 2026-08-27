# Sanskrit–Ukrainian Ontology Sources — дослідження

**Статус:** DRAFT (дослідницькі нотатки власника, не ратифіковано; не
`empirically confirmed` — джерела процитовані, самі claims про них не
перевірені незалежно цією сесією).
**Контекст:** виникло з питання "чи можем ми взяти онтологію з
санскрито-українського словника, або десь в інтернеті" під час роботи
над `TAGGING-V2-DESIGN-2026-08-28.md` (якими анкорами розширити 270
концептів онтології для vault-тегування). Дослідження провів власник.

**Домен:** це дослідження стосується Paninian ontology / Sanskrit
lexicon загалом, не лише vault-тегування — авторитет над цим доменом
за федеративною моделлю екосистеми належить `my-lisp-panini`/
`shiva-sutras` (`paninian-ontology`, `shiva-canon`), не
`vault-semantic-mcp`. Збережено тут, бо тут виникло питання; вартує
поділитися з тими репозиторіями, якщо рішення справді впливає на їхню
онтологію.

---

## Висновок пошуку: словника немає, і це, можливо, краще

**Повноцінного сучасного академічного санскритсько-українського
словника загальної лексики не знайдено.** Є Glosbe (Sanskrit↔Ukrainian)
— агрегована translation-memory система з різних джерел, не той тип
джерела, що годиться як authority для онтології. Є «Санскритсько-
український тлумачний словник езотеричних термінів» (7promeniv.com.ua,
3000+ термінів), але джерельна база включає Шівананду, Ауробіндо,
Блаватську, Бейлі — цікаво для історії рецепції термінів, **не як
лексикографічний авторитет**.

Український проєкт «Санскрит в Україні» у власному списку
рекомендованих словників не має окремого Sanskrit→Ukrainian словника
— рекомендує Monier-Williams/Кельн, Кочергіну, Sanskrit Dictionary,
граматичний словник Abhyankar.

Але для онтології потрібен не плоский `dharma = дгарма`, а щось
значно багатше:

```text
Sanskrit lemma
   ↓
morphology / root / derivation
   ↓
historically attested senses
   ↓
relations to other Sanskrit concepts
   ↓
source passages
   ↓
school / period / genre
   ↓
possible Ukrainian renderings
   ↓
translation evidence
```

Для цього вже існує сильний набір джерел.

---

## Онтологію варто будувати шарами

### 1. Внутрішньосанскритський семантичний шар — найважливіший

**Amarakośa** — не перекладний словник, а класичний санскритський
тезаурус синонімів. Cologne Digital Sanskrit Lexicon має цифрову
версію Sanskrit→Sanskrit. Групує санскритські поняття між собою, а не
"яке англійське слово відповідає цьому слову" — золото для ontology.

Поруч: **Śabdakalpadruma**, **Vācaspatyam** — великі традиційні
Sanskrit→Sanskrit лексикони (Cologne виділяє їх як джерела
внутрішньосанскритських визначень).

Архітектурний принцип:

```text
не:  Sanskrit → English → Ukrainian → concept
а:   Sanskrit → Sanskrit semantic graph → Ukrainian
```

Українська стає **інтерфейсом до поняття**, не джерелом самого поняття.

### 2. Історична семантика та етимологія

- **Monier-Williams** — широкий загальний словник, compounds,
  етимології, посилання на літературні джерела. Стандартний general
  reference для classical Sanskrit (за Cologne).
- **Apte** — класичне вживання, нумерація значень, ідіоми.
- **Böhtlingk–Roth / Petersburg Wörterbuch** — глибший
  історико-філологічний контроль, багаті цитати.
- **Grassmann** — окремо для Ṛgveda (ведійське значення не можна
  автоматично прирівнювати до пізнішого класичного).

Cologne має **43 словники**, дані доступні і як вебсторінки, і у
завантажуваних цифрових форматах (XML/SLP1 для багатьох) — важливо
для машинного pipeline.

### 3. Nirukta Яски

Яска цікавить не просто як словникар — `Nirukta` пояснює значення
слів через їхню структуру, походження та вживання; класифікує слова
(`nāman`, `ākhyāta`, `upasarga`, `nipāta`). Текст доступний на GRETIL.

Пропонована пара для `my-lisp-panini`:

```text
Pāṇini = generative morphology / grammar
Yāska  = lexical-semantic interpretation
Amara  = conceptual neighbourhood / synonymy
```

Три різні підсистеми майбутньої ontology.

### 4. Sanskrit WordNet — пряме попадання в задачу

- **IIT Bombay Sanskrit WordNet** — "Lexical Database for Sanskrit"
  через synsets; станом на 2026 понад 66 тис. унікальних слів, понад
  46 тис. linked synsets. Використовував традиційну індійську
  ontology на кшталт Amarakośa.
- **Sanskrit WordNet (University of Pavia / Exeter)** — мета:
  comprehensive lexico-semantic database Sanskrit,
  machine-interpretable and machine-actionable. Модель даних: lemma /
  synset / relation / semantic field; relations можуть бути semantic
  або lexical.

Рекомендація власника: **обов'язково дослідити перед тим, як
винаходити власну schema** — не копіювати, а не повторювати вже
вирішені задачі.

### 5. Sanskrit Heritage (Gérard Huet) — морфологічний шар

Не лише словник — морфологічний generator/analyzer, sandhi, reader,
compound recognition, linguistic databases. Huet (2004) окремо описав
архітектуру lexical database for Sanskrit — методологічна праця про
машинне представлення санскритського лексикону.

Повний ланцюжок:

```text
surface form
↓ Heritage / morphology
lemma
↓
Pāṇinian derivation
↓
lexical senses
↓ MW / Apte / traditional kośa
↓
synset / semantic relations
↓ Sanskrit WordNet
↓
Ukrainian lexicalization
```

---

## Український бік

**Дмитро Бурба** — «Практична транскрипція санскритських власних назв
та термінів в українській мові» (рецензована публікація у «Східному
світі», з DOI) — потрібна для шару `Sanskrit canonical form ↔ IAST ↔
Ukrainian representation`.

Переклади Бурби (**«Бгаґавадґіта. Ґіта-артха-санґрага Ямуни»**,
`Caraka-saṃhitā`, серія триває навіть у 2026) містять переклад із
санскриту, граматичний розбір і коментарі — майже ідеальний parallel
corpus.

**Гнатовська** — свіжа робота про `sat`/`asat` у Nasadiya-sukta та
Bṛhadāraṇyaka-upaniṣad: сама постановка проблеми показує, що одне
Sanskrit lemma не отримує автоматично один український label:

```text
sat ≠ просто "буття"
sat → sense₁ in text A
    → sense₂ in text B
    → philosophical interpretation C
    → Ukrainian rendering X/Y depending on context
```

**Павло Ріттер** — один із засновників української індології,
викладав санскрит у Харківському університеті, переклади безпосередньо
із санскриту («Голоси Стародавньої Індії»: Ṛgveda, Atharvaveda,
Mahābhārata, Rāmāyaṇa, Kālidāsa, Bhartṛhari). Його санскритська
граматика — українське видання 2022 р. за редакцією й з примітками
Бурби.

```text
Sanskrit concept
↓ Ritter Ukrainian rendering ~1920s
↓ modern Burba rendering
↓ possible semantic drift in Ukrainian terminology
```

---

## Що НЕ вважати authority

Праці типу «Праукраїна і санскрит», «Українські говірки і санскрит»,
«Українсько-санскритські спорідненості» — присутні в бібліографіях, але
**не використовувати як доказ спорідненості/етимології без незалежного
історико-лінгвістичного підтвердження**. Зберігати як:

```text
claim-source
status: requires-independent-validation
```

не як `etymology: confirmed`. Пряме застосування evidence discipline
цієї екосистеми (§3 кореневого CLAUDE.md) до зовнішніх джерел.

## Уточнення (2026-08-28): не відкидати fringe-джерела, а розкладати

Власник уточнив попередню рекомендацію ("не authority" ≠ "викинути").
Слабка або навіть фантазійна теорія може містити **один сильний факт**,
який автор просто неправильно пояснив — рідкісне діалектне слово,
форма до стандартизації, точний паралель, забуте посилання,
неперевірене спостереження. Правильна модель — не "джерело сумнівне →
відкинути все" і не "джерело цікаве → повірити всьому", а:

```text
джерело
↓
розібрати на атомарні твердження
↓
відділити СПОСТЕРЕЖЕННЯ від ІНТЕРПРЕТАЦІЇ
↓
кожне спостереження перевірити незалежно
```

Приклад декомпозиції твердження "українське X походить від
санскритського Y":

```text
CLAIM A: українське слово X існує
CLAIM B: форма X історично засвідчена
CLAIM C: санскритське Y існує
CLAIM D: Y має значення Z
CLAIM E: X і Y фонетично подібні
CLAIM F: між X і Y є історична етимологічна спорідненість
```

Може виявитись: A-E confirmed/observed, F unsupported — головна теза
автора падає, але A-E лишаються цінними даними. Це і є "діамант".

Пропонований статус-словник для окремих атомарних тверджень (ширший
за просто `requires-independent-validation` вище): `OBSERVED`,
`SUPPORTED`, `PARTIAL`, `DISPUTED`, `UNVERIFIED`, `FALSIFIED`. З таким
розрізненням fringe-джерела не "отруюють базу" — вони лише додають
кандидатів на перевірку:

```text
┌─────────────────────────────┐
│ Fringe / speculative source │
└──────────────┬──────────────┘
               │ extract
               ▼
        atomic observations
               │
               ▼
      independent validation
        /       |        \
 confirmed   unknown    false
    │
    ▼
ontology proper
```

Принцип: **погане пояснення не робить саме спостереження поганим.**
Найцінніше тут не обов'язково пряме запозичення — може бути тонший
сигнал: дві індоєвропейські мови зберегли схожу семантичну структуру
(корінь → значення руху → значення життєвої сили → абстрактне
значення), не пряме слово-в-слово запозичення. Для онтології мислення
це може бути цікавіше за звичайну етимологію.

Перегляд попередньої рекомендації: не "ці праці не використовувати", а
**"використовувати їх як шахту, але не як метрологічний еталон"** —
автор показує, де копати; чи це золото, визначають незалежні
словники, корпуси, історична фонетика, датовані тексти, первинні
джерела. Ці українсько-санскритські роботи варто включити в майбутній
`my-lisp-panini` pipeline саме як **hypothesis generators**, не як
джерела істини.

**Історична паралель (додано цією сесією, не частина оригінального
дослідження власника):** цей патерн — задокументований в історії
науки, не лише метафора. Алхіміки лишили реальну процедурну хімічну
базу (дистиляція, кристалізація, точні пропорції) попри хибну теорію
трансмутації/флогістону. Тіхо Браге зібрав найточніші на свій час
спостереження руху планет у межах геоцентричної моделі — ці ж дані
Кеплер потім використав, щоб цю модель спростувати. В обох випадках
спостереження пережили теорію, яка їх породила.

**Зв'язок з іншою роботою цієї ж сесії:** той самий рух "не заборонити
чи змішати, а розділити й підписати", що вже застосований сьогодні до
негігієнічних макросів (інструмент дозволений, лише позначений, що
захоплює) і до `advise` в `lib/knowledge.my` (negation-as-failure
тримається окремо від явного факту `(not goal)`, не одним типом nil).

**Наступний найдешевший крок (не виконано, запропоновано):** взяти
ОДНЕ конкретне твердження з "Українсько-санскритських спорідненостей"
(не всю працю) і реально прогнати через A-F декомпозицію — перевірити,
чи справді щось із A-E виживає, коли F падає.

---

## Пропонована форма онтології

Не файл `sanskrit_ukrainian_dictionary`, а лексико-семантична система
з provenance:

```text
                  ┌─ Pāṇini (morphology / derivation)
                  │
Sanskrit lemma ───┼─ Yāska (semantic/etymological analysis)
                  │
                  ├─ Amarakośa (synonym/concept groups)
                  │
                  ├─ MW / Apte / PWG (historical senses + attestations)
                  │
                  ├─ Sanskrit WordNet (synsets + semantic relations)
                  │
                  └─ corpus passages
                           │
                           ▼
                     SENSE NODE
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       Ukrainian label           Ukrainian gloss
       Бурба / Ріттер            commentary
              │
              ▼
       Ukrainian ontology
```

Пропонована одиниця даних (my-lisp-стиль):

```lisp
(concept sat-1
  (lemma sat)
  (root as)
  (pos adjective)
  (sense existence-real-being)
  (source ...)
  (period vedic)
  (relations
    (opposite asat)
    ...)
  (uk
    (label "сущий")
    (alternatives "буття" "дійсний"))
  (evidence
    (monier-williams ...)
    (yaska ...)
    (burba ...)
    ...)
  (status partial))
```

Тобто не "слово дорівнює слову", а: форма → лема → значення → концепт
→ відношення → контекст → українські способи вираження → джерела.

## Рекомендація власника

**Не починати зі створення санскритсько-українського словника.**
Почати зі створення маленького **Sanskrit–Ukrainian Concept Graph**
(50-100 фундаментальних понять), кожен вузол максимально доказовий.

Джерельний пріоритет:

```text
Primary Sanskrit text
      ↓
Pāṇini / Yāska / traditional kośa
      ↓
MW + Apte + specialist lexicon
      ↓
Sanskrit WordNet / Heritage
      ↓
academic Ukrainian translation/commentary
      ↓
Ukrainian lexical label
```

## Джерела (посилання з оригінального дослідження)

- Glosbe Sanskrit↔Ukrainian: https://glosbe.com/sa/uk
- «Санскритсько-український тлумачний словник езотеричних термінів»: https://7promeniv.com.ua/zamovyty-knyhu/sanskrytsko-ukrainskyi-slovnyk-ezoterychnykh-terminiv
- «Санскрит в Україні»: https://sanskrit.com.ua/for-students/
- Amarakośa (Cologne): https://sanskrit-lexicon.github.io/AMAR/
- Dictionaries Overview (Cologne): https://sanskrit-lexicon.github.io/csl-guides/dictionaries/overview
- Monier-Williams (Cologne): https://sanskrit-lexicon.github.io/csl-guides/dictionaries/mw
- Cologne Sanskrit Lexicon (43 dictionaries): https://www.sanskrit-lexicon.uni-koeln.de/index.html
- Nirukta (GRETIL): https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/sa_yAska-nirukta.htm
- IIT Bombay Sanskrit WordNet: https://rnd.iitb.ac.in/node/1148
- Sanskrit WordNet (Pavia): https://sanskritwordnet.unipv.it/
- Sanskrit WordNet API: https://sanskritwordnet.unipv.it/api
- Sanskrit Heritage Site (Huet): https://sanskrit.uohyd.ac.in/SKT/
- Huet, "Design of a Lexical Database for Sanskrit" (ACL Anthology): https://aclanthology.org/W04-2102/
- Бурба, "Orthographic Transcription of Sanskrit Names..." (ОУЦІ/DOI): https://ouci.dntb.gov.ua/en/works/4YKP1PR9/
- Переклади (indology.ho.ua): https://indology.ho.ua/translations.html
- Чарака-самгіта, пер. Бурби (Східний світ): https://oriental-world.org.ua/journal/article/view/826
- Гнатовська, "Сат і асат..." (Східний світ): https://oriental-world.org.ua/index.php/journal/article/view/820
- Ріттер П.Г. (Енциклопедія Сучасної України): https://esu.com.ua/article-884546
- «Голоси Стародавньої Індії» (ТДСФ): https://www.tdsf.kiev.ua/ritter_year.php
- Бібліографія "Ukrainian and Sanskrit" (Grafiati): https://www.grafiati.com/en/literature-selections/ukrainian-and-sanskrit/

**Примітка:** усі посилання — з дослідження власника, не перевірені
цією сесією напряму (не завантажені, не звірені живцем). Статус
кожного твердження — `predicted`/цитата з чужого пошуку, не
`source-confirmed` цим агентом.
