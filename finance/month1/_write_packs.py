#!/usr/bin/env python3
"""Generate F26-ready metadata packs for month 1. Run from month1/."""
from pathlib import Path

DISCL = (
    "This video is for education and entertainment only. It is not financial, tax, or "
    "investment advice. Nothing here is a recommendation to buy or sell any security. "
    "Past patterns are not future results. All investing involves risk, including loss "
    "of principal. Numbers are sourced below and rounded for speech. Consult a licensed "
    "advisor for your situation."
)
PIN = "Education only — not financial advice. Which number are you actually tracking? Tell me below."

def pack(title, desc, tags, hashtags, thumb, chapters, sources, pinned=PIN, extra=""):
    h = " ".join(hashtags)
    return f"""## TITLE
**{title}**

## THUMBNAIL
{thumb}

## DESCRIPTION
{desc}

{chapters}

Sources:
{sources}

{DISCL}

If this was useful, the next video continues the same rule — shown, not sold.

{h}

## TAGS
{tags}

## PINNED COMMENT
{pinned}

## HASHTAGS (3-5, also in description)
{h}
{extra}
"""

LONG = [
dict(
dir="v01", kw="20,000",
title="Why Everything Changes After $20,000",
thumb="2 lines: THE FIRST / THRESHOLD. Hero: gold $20,000 stat card on navy. Title must NOT repeat the thumbnail.",
tags="20,000, why everything changes after 20000, net worth 20000, first net worth threshold, personal finance, money rules, emergency fund, investable surplus, financial milestone, threshold finance",
hashtags=["#personalfinance", "#networth", "#threshold"],
desc=(
"Why everything changes after $20,000 is not a flex and it is not a promise that you are rich. "
"Twenty thousand dollars is the first common threshold where money stops being only survival cash "
"and starts becoming a tool: a buffer, then an investable surplus. This video shows that rule as a "
"chart, not as a pep talk. We walk the ladder from zero to five thousand to twenty thousand to one "
"hundred thousand and mark what actually changes at each step — the ability to absorb a shock, the "
"ability to say no, and the first time a year's return can rival a month of saving. "
"You will see why people who hit twenty thousand and immediately buy a depreciating object reset the "
"clock, and why the number is about optionality rather than status. This is education, not a target "
"you must copy. Households differ. Costs differ. The mechanism does not: until a buffer exists, every "
"dollar is one accident away from zero. After a real buffer, the same dollar can be left alone long "
"enough for time to matter. We source US median figures from the Federal Reserve Survey of Consumer "
"Finances so the picture is not invented. If you are under the line, the video is a map. If you are "
"over it, the video is a warning not to spend the threshold away. Comment the number you are actually "
"defending this year."
),
chapters="0:00 The $20,000 rule\n0:15 Education, not advice\n1:10 Survival money vs tool money\n3:00 The ladder on a chart\n6:00 The car that resets you to zero\n8:30 What to protect, not buy\n10:20 Which number are you defending?",
sources="- Board of Governors of the Federal Reserve System, Survey of Consumer Finances (latest release): median net worth and transaction accounts by age.\n- U.S. Bureau of Labor Statistics, Consumer Price Index: why idle cash loses purchasing power.\n- Illustrative thresholds ($5k / $20k / $100k) are teaching marks, not advice.",
),
dict(
dir="v02", kw="compound interest",
title="Compound Interest Doesn't Make Most People Rich",
thumb="2 lines: THE LIE / OF 8%. Hero: two-line chart, gold vs alert, 8% of $0 stays $0.",
tags="compound interest, compound interest doesn't make people rich, savings rate vs return, personal finance, money rules, investing basics, why compound interest fails, threshold finance",
hashtags=["#personalfinance", "#investing", "#threshold"],
desc=(
"Compound interest doesn't make most people rich, and the posters that say otherwise skip the only "
"number that matters at the start: how much you actually add. Eight percent of almost nothing is still "
"almost nothing. This video puts two charts on screen — a pretty return with no contributions, and a "
"plain savings rate with no magic — and lets the lines argue. The mechanism is simple and rarely taught: "
"at low balances, contribution dwarfs yield. Brochures reverse that, because yield is easier to sell "
"than behavior. We are not anti-investing. We are anti-mythology. You will see when the slope of returns "
"finally starts to rival new savings (a later video, one hundred thousand, is that chapter) and why "
"chasing a higher rate before a higher savings rate is a category error. Figures are illustrations of "
"the mechanism, labeled as such, not projections of your account. Education, not financial advice. "
"If a talking head promised you that time alone would rescue a zero contribution plan, this is the "
"correction. Tell me which number you are protecting this year: the rate you hope for, or the amount "
"you can actually move."
),
chapters="0:00 The pretty lie\n0:15 Not financial advice\n1:20 8% of zero\n3:40 Savings rate vs return, on one chart\n6:10 When slope finally matters\n8:50 What to measure instead\n10:10 Rate or contribution?",
sources="- Illustrative compound vs contribution charts (labeled illustration, not a forecast).\n- Concept: wealth accumulation identity — ending balance depends on contributions, time, and rate. No security is recommended.\n- Later milestone context: see V08 ($100k slope).",
),
dict(
dir="v03", kw="net worth",
title="3 Net Worth Numbers That Matter Before 40",
thumb="2 lines: NOT YOUR / SALARY. Hero: three gold gauges, salary crossed out.",
tags="net worth, net worth numbers before 40, net worth vs salary, personal finance, money rules, solvency, emergency fund, optionality, threshold finance",
hashtags=["#personalfinance", "#networth", "#threshold"],
desc=(
"Net worth is the scoreboard. Salary is a flow that can vanish. This video shows three net worth numbers "
"that matter before 40, drawn as gauges, not as shame. First: above zero — solvency. If assets minus debts "
"is negative, a raise is not a plan; the hole is. Second: a buffer measured in months of essential costs, "
"commonly taught as about three months, which we treat as a teaching mark, not a law. Third: optionality — "
"a net worth that can buy time, often discussed as about one year of gross salary, again a mark, not a "
"prescription. We use the Federal Reserve Survey of Consumer Finances so you can see where US medians sit "
"by age, and we say out loud that medians are not goals. The point of the graphic is the difference between "
"a flow and a stock. People optimize the flow because it shows up every two weeks. The stock is what lets "
"you survive a gap in the flow. Education, not financial advice. Your cost of living is not the example "
"on screen. Comment which of the three gauges you can actually fill in without guessing."
),
chapters="0:00 Salary is the wrong chart\n0:15 Not financial advice\n1:30 Gauge 1 — solvency\n3:20 Gauge 2 — buffer\n5:40 Gauge 3 — optionality\n8:00 US medians, not goals\n10:00 Which gauge are you tracking?",
sources="- Federal Reserve SCF: median US net worth by age (latest).\n- Buffer '3 months' and '1× salary' are widely used teaching marks (CFP Board / consumer-finance curricula), not advice for you.\n- BLS CPI for the cost of standing still.",
),
dict(
dir="v04", kw="two incomes",
title="Why Two Incomes Made Families Poorer",
thumb="2 lines: THE SECOND / PAYCHECK. Hero: stacked-cost bars eating the second bar.",
tags="two incomes, two income trap, why two incomes made families poorer, household costs, personal finance, housing costs, childcare, money rules, threshold finance",
hashtags=["#personalfinance", "#moneyrules", "#threshold"],
desc=(
"Two incomes made many families poorer in freedom even when the spreadsheet got bigger. This video "
"shows the two-income trap as stacked bars: housing, childcare, transport, and status costs that were "
"bid up because two paychecks showed up to the auction. The second income did not land in savings. It "
"landed in a higher fixed-cost floor. That floor is brittle — two jobs, two commute, two careers that "
"cannot both break without the house wobbling. We draw a then-versus-now cost stack using historical "
"household data and the argument popularized in Elizabeth Warren and Amelia Warren Tyagi's work on "
"the two-income trap, labeled as research not scripture. This is not an argument that a partner should "
"quit. It is an argument that a second paycheck spent entirely on newly mandatory costs is not wealth. "
"Wealth is what remains when one bar disappears. Education, not financial advice. Look at the chart, "
"then look at your own fixed costs. Which of them exist only because the second income exists?"
),
chapters="0:00 Two paychecks, less slack\n0:15 Not financial advice\n1:40 The auction for housing and care\n4:00 Then vs now, stacked\n6:20 Brittleness — one job gone\n8:50 What remaining actually means\n10:20 Which costs are optional?",
sources="- Warren & Tyagi, The Two-Income Trap (mechanism; we show the logic, not a political program).\n- U.S. Census / BLS consumer expenditure and housing cost series for the stacks (cited with years in sources.md at script time).\n- Illustrative bars labeled as teaching graphics.",
),
dict(
dir="v05", kw="started from $0",
title="If I Started From $0 in 2026, I'd Do This",
thumb="2 lines: SKIP THE / TIPS. Hero: three-step flowchart, no logos, no tickers.",
tags="started from $0, if I started from 0 in 2026, order of operations money, personal finance, beginner investing framework, emergency fund first, money rules, threshold finance",
hashtags=["#personalfinance", "#moneyrules", "#threshold"],
desc=(
"If I started from $0 in 2026 I would not start with a ticker. I would start with an order of operations "
"you can draw in three boxes: a buffer for shocks, a stop on high-cost debt, then broad low-cost funds "
"as a concept — not a shopping list. This video is a flowchart. Every box is a rule, none is a product. "
"We will not name a broker, a fund, or a coin. The internet is already a catalog. What it is not, is a "
"sequence. Sequence is the whole game when you have nothing, because the wrong first move (a car, a "
"hot stock, a course) puts you back at zero with interest. Education, not financial advice. Your debts, "
"your country, your tax wrapper are not the boxes on screen. The boxes are: don't die from a shock, "
"don't feed a high-rate hole, don't skip time in the market with money you cannot leave alone. Comment "
"which box you would be tempted to skip, and why."
),
chapters="0:00 Starting at zero\n0:15 Not financial advice\n1:20 Box 1 — buffer\n3:30 Box 2 — high-cost debt\n5:40 Box 3 — broad funds as a concept\n8:00 What I would refuse to buy first\n10:00 Which box would you skip?",
sources="- Order-of-operations is a teaching framework used across CFP/consumer-finance education (buffer, costly debt, then investing). Not a personal plan.\n- No securities, tickers, or products are named as recommendations.\n- 2026 in the title is a year-stamp for search, not a market call.",
),
dict(
dir="v06", kw="cash in the bank",
title="Why Too Much Cash in the Bank Is a Trap",
thumb="2 lines: CASH IS / A FEE. Hero: a shrinking real-value line on $10k.",
tags="cash in the bank, too much cash, inflation cash trap, emergency fund vs excess cash, personal finance, purchasing power, money rules, threshold finance",
hashtags=["#personalfinance", "#inflation", "#threshold"],
desc=(
"Too much cash in the bank is a trap because inflation is a fee you do not see on the statement. A "
"buffer is not the trap. The trap is the pile above the buffer, sitting still while prices walk away. "
"This video draws ten thousand dollars of extra cash against the Consumer Price Index and watches the "
"real value fall. We are not telling you to empty your account. We are showing why 'I don't trust "
"markets so I keep it all in cash' is also a market position — a short on your future grocery list. "
"The teaching mark we use is months of essential expenses, not a universal dollar amount. Above that "
"mark, cash is no longer safety; it is a decaying inventory. Education, not financial advice. Your "
"buffer size depends on how jumpy your income is. A contractor is not a salaried employee. Watch the "
"line, then count your months. How many months are safety, and how many months are a fee?"
),
chapters="0:00 The fee you don't see\n0:15 Not financial advice\n1:30 Buffer vs pile\n3:20 $10k vs CPI, on a chart\n6:00 Cash is also a bet\n8:20 How many months is safety?\n10:00 Count your months",
sources="- U.S. Bureau of Labor Statistics, Consumer Price Index (CPI-U), historical series.\n- Buffer measured in months of expenses is a teaching mark, not a prescription.\n- Chart of $10k real value is an illustration using CPI, not a forecast.",
),
dict(
dir="v07", kw="secretly wealthy",
title="7 Signs Someone Is Secretly Wealthy",
thumb="2 lines: QUIET / MATH. Hero: 2×2 'looks rich / is rich'.",
tags="secretly wealthy, 7 signs secretly wealthy, quiet wealth, looks rich vs is rich, personal finance, net worth, money rules, consumption vs balance sheet, threshold finance",
hashtags=["#personalfinance", "#networth", "#threshold"],
desc=(
"Secretly wealthy people are easy to miss because we were trained to read consumption as the scoreboard. "
"This video puts seven signs on a 2×2: looks rich versus is rich. The mechanism is the balance sheet, "
"not the Instagram. Time that is not sold, a house that is not performing, a car that is boring, a "
"calendar that is empty of status errands, a refusal to talk about picks, a buffer that is boring, a "
"slope they do not need to photograph. None of these is a costume you should copy this week. They are "
"downstream of a number. We will not pretend a cheap watch equals a funded future. We will show why "
"the camera lies and the chart does not. Education, not financial advice. If you want a sign to chase, "
"chase the gauge from video three, not the outfit. Which sign have you been using as a proxy for wealth, "
"and which one do you actually want?"
),
chapters="0:00 The camera lies\n0:15 Not financial advice\n1:20 Looks rich vs is rich\n3:00 Seven signs, one mechanism\n7:30 What not to costume\n9:40 Which proxy have you been using?",
sources="- Mechanism: consumption vs net worth (SCF: high-income low-NW households exist). No individual's wealth is claimed.\n- Signs are behavioral illustrations, not a diagnostic test.\n- Cross-ref V03 gauges and V08 $100k slope.",
),
dict(
dir="v08", kw="100k",
title="Once You Hit $100K, Net Worth Starts Compounding",
thumb="2 lines: THE SLOPE / CHANGES. Hero: line that steepens at $100k.",
tags="100k, once you hit 100k, net worth 100000, compounding net worth, personal finance, critical mass investing, money rules, threshold finance",
hashtags=["#personalfinance", "#networth", "#threshold"],
desc=(
"Once you hit $100K, net worth starts compounding in a way you can finally feel, because a single-digit "
"year on one hundred thousand begins to rival a year of new savings for a lot of households. That is "
"the slope change. Before that number, your deposits are the story. After it, time is invited to the "
"meeting. This is not magic and it is not a guarantee. Markets fall. Jobs end. We draw an illustrative "
"seven percent year on one hundred thousand — seven thousand — next to a typical savings year, and we "
"label it an illustration, not a forecast of your account. The Federal Reserve SCF still shows that "
"many households never sit at this line, which is why the line matters as a map, not as a taunt. "
"Education, not financial advice. If you are far from it, video one and video two are the path, not a "
"hot pick. If you are near it, the job is to not spend the slope. What would have to be true for your "
"slope to change this year?"
),
chapters="0:00 The slope change\n0:15 Not financial advice\n1:40 Why $100k is a different chart\n4:00 $7k vs a year of saving\n6:30 Who never gets here, per SCF\n8:40 Do not spend the slope\n10:20 What would have to be true?",
sources="- Illustrative 7% on $100k = $7k (a teaching rate, NOT a projected return).\n- Federal Reserve SCF for the share of households around this net-worth region (cite year in sources.md).\n- No security recommended.",
),
]

SHORTS = [
dict(dir="s01", parent="V01", kind="hook",
title="Everything Changes After $20,000",
kw="20,000",
thumb="Big $20,000 on navy. One word under: THRESHOLD.",
desc="Everything changes after $20,000 — not because you are rich, because the math finally has something to work on. Education, not financial advice. Full video on this channel. #Shorts #personalfinance #networth",
tags="20,000, everything changes after 20000, net worth short, personal finance shorts"),
dict(dir="s02", parent="V01", kind="payoff",
title="Why $20,000 Is the First Real Threshold",
kw="20,000",
thumb="THE BUFFER as 2 words. Gold bar filling.",
desc="Why $20,000 is the first real threshold: it is the first buffer that can take a hit without sending you back to zero. Education, not financial advice. Full video on this channel. #Shorts #personalfinance #networth",
tags="20,000, first net worth threshold, emergency buffer, personal finance shorts"),
dict(dir="s03", parent="V02", kind="hook",
title="Compound Interest Is a Lie (For You)",
kw="compound interest",
thumb="8% in gold, $0 under it in alert red.",
desc="Compound interest is a lie for you if the balance is near zero — eight percent of nothing is nothing. Education, not financial advice. Full video on this channel. #Shorts #personalfinance #investing",
tags="compound interest, compound interest lie, savings rate, personal finance shorts"),
dict(dir="s04", parent="V02", kind="payoff",
title="The Number That Actually Makes You Rich",
kw="savings rate",
thumb="SAVINGS RATE as two words, bar growing.",
desc="The number that actually makes you rich at the start is the savings rate, not the return on a poster. Education, not financial advice. Full video on this channel. #Shorts #personalfinance #investing",
tags="savings rate, compound interest, personal finance shorts, money rules"),
dict(dir="s05", parent="V03", kind="hook",
title="Your Salary Is the Wrong Scoreboard",
kw="net worth",
thumb="SALARY crossed out, NET WORTH in gold.",
desc="Your salary is the wrong scoreboard. Net worth is the stock. Salary is a flow that can stop. Education, not financial advice. Full video on this channel. #Shorts #personalfinance #networth",
tags="net worth, salary vs net worth, personal finance shorts"),
dict(dir="s06", parent="V04", kind="hook",
title="Two Incomes, Less Freedom",
kw="two incomes",
thumb="TWO PAYCHECKS, second bar eaten.",
desc="Two incomes, less freedom — when the second paycheck is already spent on a higher floor of costs. Education, not financial advice. Full video on this channel. #Shorts #personalfinance #moneyrules",
tags="two incomes, two income trap, personal finance shorts"),
dict(dir="s07", parent="V04", kind="payoff",
title="The Costs That Ate the Second Income",
kw="two incomes",
thumb="FIXED COSTS in alert, eating gold.",
desc="The costs that ate the second income are the ones that only exist because the second income exists. Education, not financial advice. Full video on this channel. #Shorts #personalfinance #moneyrules",
tags="two incomes, fixed costs, two income trap, personal finance shorts"),
dict(dir="s08", parent="V05", kind="hook",
title="If I Started at $0 in 2026",
kw="started at $0",
thumb="$0 then three boxes. SKIP THE TIPS.",
desc="If I started at $0 in 2026 I would not start with a ticker. Three boxes, no shopping list. Education, not financial advice. Full video on this channel. #Shorts #personalfinance #moneyrules",
tags="started at $0, started from zero 2026, personal finance shorts"),
dict(dir="s09", parent="V06", kind="hook",
title="Your Bank Account Is Charging You",
kw="cash",
thumb="SILENT FEE, shrinking pile.",
desc="Your bank account is charging you if the pile above your buffer sits still while prices walk away. Education, not financial advice. Full video on this channel. #Shorts #personalfinance #inflation",
tags="cash in the bank, inflation, silent fee, personal finance shorts"),
dict(dir="s10", parent="V07", kind="hook",
title="7 Signs of Quiet Wealth",
kw="quiet wealth",
thumb="QUIET MATH. 2×2 grid still.",
desc="7 signs of quiet wealth — the camera lies, the balance sheet does not. Education, not financial advice. Full video on this channel. #Shorts #personalfinance #networth",
tags="quiet wealth, secretly wealthy, personal finance shorts"),
dict(dir="s11", parent="V08", kind="hook",
title="Why $100K Is When Money Gets Easier",
kw="100k",
thumb="$100K, slope steepens.",
desc="Why $100K is when money gets easier: a normal year on that pile starts to rival a year of new savings. Education, not financial advice. Full video on this channel. #Shorts #personalfinance #networth",
tags="100k, net worth 100000, compounding, personal finance shorts"),
dict(dir="s12", parent="V08", kind="payoff",
title="The Slope After $100K",
kw="100k",
thumb="THE SLOPE in gold on a steep line.",
desc="The slope after $100K is time joining the meeting. Do not spend the slope. Education, not financial advice. Full video on this channel. #Shorts #personalfinance #networth",
tags="100k, net worth slope, compounding, personal finance shorts"),
]

ROOT = Path(__file__).resolve().parent

def write_long(v):
    d = ROOT / v["dir"]
    d.mkdir(exist_ok=True)
    extra = f"\n## PRIMARY KEYWORD\n{v['kw']}\n"
    (d / "metadata.md").write_text(pack(
        v["title"], v["desc"], v["tags"], v["hashtags"], v["thumb"],
        v["chapters"], v["sources"], extra=extra), encoding="utf-8")
    print("wrote", d / "metadata.md", "title chars", len(v["title"]))

def write_short(s):
    d = ROOT / s["dir"]
    d.mkdir(exist_ok=True)
    title = s["title"]
    if len(title) > 50:
        print("WARN short title", len(title), title)
    body = f"""## TITLE
**{title}**

## THUMBNAIL
{s['thumb']}

## DESCRIPTION
{s['desc']}

## TAGS
{s['tags']}

## PINNED COMMENT
Education only — not financial advice. Full video on this channel.

## PARENT
{s['parent']} {s['kind']}

## PRIMARY KEYWORD
{s['kw']}
"""
    (d / "metadata.md").write_text(body, encoding="utf-8")
    print("wrote", d / "metadata.md", "title chars", len(title))

if __name__ == "__main__":
    for v in LONG: write_long(v)
    for s in SHORTS: write_short(s)
