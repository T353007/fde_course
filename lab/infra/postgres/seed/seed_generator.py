#!/usr/bin/env python3
"""
Northstar lab seed generator.

Builds 1,200 applications with the mess a real lender accumulates over eleven
years. Standard library only, fixed random seed, so every learner gets byte for
byte identical data.

The important part is not the row count. It is that the discovery numbers in
CANON.md fall out of this data when you query it correctly:

    median cycle time ................ 9.4 days
    median hands-on time ............. 41 minutes
    median document wait ............. 5.1 days
    at least one rework loop ......... 63%
    median cost of a rework loop ..... 2.8 days
    application rate ................. about 1,840 per month

Those are not hardcoded into a summary table. They come out of
application_events, which is the only place the truth lives. The generator
calibrates its own distributions until the measured medians match, then prints
what it measured. Run with --check to fail if any target drifts.

Usage:
    python3 seed_generator.py            write CSVs into ./data
    python3 seed_generator.py --check    write and assert every canon number
    python3 seed_generator.py --report   print the measured numbers only
"""

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
import random
import statistics
import sys

# --------------------------------------------------------------------------
# Fixed inputs. Change any of these and the canon numbers move, so do not.
# --------------------------------------------------------------------------

RANDOM_SEED = 20260202

TOTAL_APPLICATIONS = 1200
DRAFT_APPLICATIONS = 24                      # created, never submitted
SUBMITTED_APPLICATIONS = TOTAL_APPLICATIONS - DRAFT_APPLICATIONS   # 1176

STALLED_APPLICATIONS = 94                    # still open at extract time
WITHDRAWN_APPLICATIONS = 78                   # pulled by the applicant
DECISIONED_APPLICATIONS = (
    SUBMITTED_APPLICATIONS - STALLED_APPLICATIONS - WITHDRAWN_APPLICATIONS
)                                             # 1004

REWORK_APPLICATIONS = 741                     # 741 / 1176 = 63.01%

# Volume window. February 2026 is the last full month before discovery starts.
# The span is picked so the submitted event rate is 1,840 a month.
WINDOW_START = dt.datetime(2026, 2, 2, 7, 30, 0)
DAYS_PER_MONTH = 30.4375
TARGET_MONTHLY_RATE = 1840
WINDOW_SPAN_DAYS = SUBMITTED_APPLICATIONS / TARGET_MONTHLY_RATE * DAYS_PER_MONTH

# The date the extract was taken. Everything open on this date is stalled.
EXTRACT_NOW = dt.datetime(2026, 4, 10, 9, 0, 0)

TARGET_CYCLE_DAYS = 9.4
TARGET_HANDS_ON_MINUTES = 41.0
TARGET_DOC_WAIT_DAYS = 5.1
TARGET_REWORK_DAYS = 2.8
TARGET_REWORK_SHARE = 63.0

TENANT_MIX = [("NSC_DIRECT", 852), ("BAYLINE", 200), ("CASCADE", 148)]

PRODUCTS = [
    ("TERM_LOAN", 0.44),
    ("LOC", 0.26),
    ("EQUIPMENT", 0.18),
    ("SBA_7A", 0.12),
]

# Applicant ids reserved for the Corner Rise Bakery duplicate cluster.
# Scattered on purpose. A cluster at the top of the table would be a giveaway.
CORNER_RISE_APPLICANT_IDS = [137, 402, 688, 991]

# The application that carries the bank statement from CANON.md section 4.
CANON_STATEMENT_APPLICATION_ID = 1044

FASTCAPITAL_SHARE = 0.08

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "data")

ET = dt.timezone(dt.timedelta(hours=-5))      # America/New_York in February

# --------------------------------------------------------------------------
# Name material. Boring on purpose. Real small business names are boring.
# --------------------------------------------------------------------------

BIZ_FIRST = [
    "Harbor", "Cedar", "Granite", "Maple", "Pinehurst", "Kestrel", "Lantern",
    "Ironwood", "Blue Ridge", "Catawba", "Piedmont", "Sunbelt", "Rowan",
    "Uwharrie", "Tryon", "Ballantyne", "Elizabeth", "Dilworth", "Belmont",
    "Salisbury", "Concord", "Matthews", "Waxhaw", "Mint Hill", "Davidson",
    "Cornelius", "Huntersville", "Gastonia", "Kannapolis", "Monroe",
    "Steele Creek", "Mallard", "Providence", "Sardis", "Idlewild", "Sharon",
    "Randolph", "Freedom", "Tuckaseegee", "Beatties Ford", "Statesville",
    "Mooresville", "Hickory", "Shelby", "Lincolnton", "Newton", "Cherryville",
]

BIZ_SECOND = [
    "Coffee", "Dental", "Auto", "HVAC", "Roofing", "Landscape", "Bakery",
    "Print", "Fitness", "Logistics", "Freight", "Machine", "Metal", "Electric",
    "Plumbing", "Grocery", "Pharmacy", "Veterinary", "Childcare", "Catering",
    "Brewing", "Textile", "Cabinet", "Flooring", "Paving", "Welding",
    "Staffing", "Janitorial", "Security", "Medical Billing", "Optical",
    "Physical Therapy", "Tax", "Insurance", "Realty", "Salon", "Barber",
    "Tire", "Body Shop", "Towing", "Nursery", "Irrigation", "Pest Control",
]

BIZ_SUFFIX = [
    "LLC", "LLC", "LLC", "Inc", "Inc", "LLC", "Co", "Group LLC",
    "Holdings LLC", "Partners LLC", "Services LLC", "Solutions Inc",
]

BIZ_KIND = [
    "Roasters", "Works", "Supply", "Company", "Services", "Group", "Partners",
    "Brothers", "and Sons", "Associates", "Enterprises", "Contractors",
]

FIRST_NAMES = [
    "James", "Maria", "Robert", "Linda", "Michael", "Patricia", "David",
    "Jennifer", "William", "Elizabeth", "Richard", "Barbara", "Joseph",
    "Susan", "Thomas", "Jessica", "Charles", "Sarah", "Christopher", "Karen",
    "Daniel", "Nancy", "Matthew", "Lisa", "Anthony", "Betty", "Mark",
    "Margaret", "Donald", "Sandra", "Steven", "Ashley", "Andrew", "Kimberly",
    "Kenneth", "Emily", "Joshua", "Donna", "Kevin", "Michelle", "Brian",
    "Carol", "George", "Amanda", "Edward", "Melissa", "Ronald", "Deborah",
    "Timothy", "Stephanie", "Jason", "Dorothy", "Jeffrey", "Rebecca",
    "Ryan", "Sharon", "Jacob", "Laura", "Gary", "Cynthia", "Nicholas",
    "Amy", "Eric", "Kathleen", "Jonathan", "Angela", "Stephen", "Shirley",
    "Larry", "Emma", "Justin", "Brenda", "Scott", "Pamela", "Brandon",
    "Nicole", "Benjamin", "Anna", "Samuel", "Katherine", "Gregory", "Samantha",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Patel", "Okafor", "Cheng", "Vasquez", "Boyd",
    "Whitfield", "Mabry", "Pridgen", "Suggs", "Blalock", "Yarborough",
]

UNDERWRITERS = [
    "renee.blackwell", "d.pham", "m.okonkwo", "t.rivas", "j.beaumont",
    "a.castellanos", "s.whitfield", "l.nakamura", "c.obrien", "p.deshmukh",
    "k.abernathy",
]

CITY_STATE = [
    ("Charlotte", "NC", "28202"), ("Charlotte", "NC", "28204"),
    ("Charlotte", "NC", "28211"), ("Concord", "NC", "28025"),
    ("Gastonia", "NC", "28054"), ("Rock Hill", "SC", "29730"),
    ("Greenville", "SC", "29601"), ("Columbia", "SC", "29201"),
    ("Raleigh", "NC", "27601"), ("Durham", "NC", "27701"),
    ("Winston-Salem", "NC", "27101"), ("Asheville", "NC", "28801"),
    ("Fresno", "CA", "93701"), ("Sacramento", "CA", "95814"),
    ("Bakersfield", "CA", "93301"), ("Riverside", "CA", "92501"),
    ("Atlanta", "GA", "30303"), ("Savannah", "GA", "31401"),
    ("Nashville", "TN", "37201"), ("Knoxville", "TN", "37902"),
    ("Richmond", "VA", "23219"), ("Norfolk", "VA", "23510"),
]


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def lognorm(rng, median, sigma):
    """Lognormal draw with the median you asked for."""
    return median * math.exp(rng.gauss(0.0, sigma))


def median_of(values):
    return statistics.median(values) if values else 0.0


def et(stamp):
    """Stamp the naive datetime with Eastern time so Postgres stores an offset."""
    return stamp.replace(tzinfo=ET).isoformat(sep=" ")


def money(value):
    return "%.2f" % round(value, 2)


def pick_weighted(rng, pairs):
    roll = rng.random()
    running = 0.0
    for value, weight in pairs:
        running += weight
        if roll <= running:
            return value
    return pairs[-1][0]


# --------------------------------------------------------------------------
# Step 1: applicants
# --------------------------------------------------------------------------

class Applicant:
    __slots__ = ("applicant_id", "legal_name", "dba_name", "ein",
                 "owner_ssn_last4", "email", "phone", "tenant_id",
                 "created_at", "mailing_state", "mailing_zip", "mailing_city")


def build_applicants(rng, tenant_by_application):
    """One applicant per application, minus repeat borrowers and the dupes."""
    applicants = []
    used_names = set()

    for applicant_id in range(1, TOTAL_APPLICATIONS + 1):
        a = Applicant()
        a.applicant_id = applicant_id
        a.tenant_id = tenant_by_application[applicant_id - 1]

        for _ in range(40):
            style = rng.random()
            if style < 0.55:
                name = "%s %s %s" % (rng.choice(BIZ_FIRST),
                                     rng.choice(BIZ_SECOND),
                                     rng.choice(BIZ_SUFFIX))
            elif style < 0.85:
                name = "%s %s %s" % (rng.choice(BIZ_FIRST),
                                     rng.choice(BIZ_KIND),
                                     rng.choice(BIZ_SUFFIX))
            else:
                name = "%s %s %s" % (rng.choice(LAST_NAMES),
                                     rng.choice(BIZ_SECOND),
                                     rng.choice(BIZ_SUFFIX))
            if name not in used_names:
                used_names.add(name)
                break
        a.legal_name = name

        a.dba_name = None
        if rng.random() < 0.22:
            base = name
            for suffix in (" LLC", " Inc", " Co", " Group LLC",
                           " Holdings LLC", " Partners LLC",
                           " Services LLC", " Solutions Inc"):
                if base.endswith(suffix):
                    base = base[: -len(suffix)]
                    break
            a.dba_name = base.strip()

        # EIN. Nullable and often wrong. Four formats in the same column.
        if rng.random() < 0.09:
            a.ein = None
        else:
            digits = "%02d%07d" % (rng.randint(20, 99), rng.randint(0, 9999999))
            roll = rng.random()
            if roll < 0.62:
                a.ein = digits[:2] + "-" + digits[2:]
            elif roll < 0.88:
                a.ein = digits
            elif roll < 0.95:
                a.ein = digits[:2] + " " + digits[2:]
            else:
                a.ein = "EIN " + digits[:2] + "-" + digits[2:]

        a.owner_ssn_last4 = ("%04d" % rng.randint(0, 9999)) if rng.random() < 0.86 else None

        first = rng.choice(FIRST_NAMES).lower()
        last = rng.choice(LAST_NAMES).lower()
        domain_word = name.split()[0].lower().replace("-", "")
        a.email = "%s.%s@%s%s.com" % (first, last, domain_word,
                                      rng.choice(["", "co", "biz", "inc"]))
        a.phone = "%d%d%d-%d%d%d-%04d" % (
            rng.randint(2, 9), rng.randint(0, 9), rng.randint(0, 9),
            rng.randint(2, 9), rng.randint(0, 9), rng.randint(0, 9),
            rng.randint(0, 9999))
        if rng.random() < 0.14:
            a.phone = a.phone.replace("-", "")
        if rng.random() < 0.07:
            a.phone = "(" + a.phone[:3] + ") " + a.phone[4:]

        city, state, zipcode = rng.choice(CITY_STATE)
        if a.tenant_id == "CASCADE" and rng.random() < 0.78:
            city, state, zipcode = rng.choice(
                [c for c in CITY_STATE if c[1] == "CA"])
        a.mailing_city, a.mailing_state, a.mailing_zip = city, state, zipcode

        a.created_at = WINDOW_START - dt.timedelta(
            days=rng.uniform(1, 2600), seconds=rng.uniform(0, 86400))
        applicants.append(a)

    apply_corner_rise_cluster(applicants)
    apply_canon_statement_applicant(applicants)
    return applicants


def apply_corner_rise_cluster(applicants):
    """
    Mission 10. One bakery, four applicant rows, no unique constraint on ein.

    Row 1 is the original 2023 term loan that is still funded.
    Row 2 came from an email intake in 2024. Someone retyped the EIN with no
    dash and the match on legal_name missed because of the comma.
    Row 3 is a typo. Two digits transposed in the EIN and the name run together.
    Row 4 came in through Bayline, using the DBA name, with the parent LLC as
    the legal name. Nothing in the code compares across tenants.
    """
    by_id = {a.applicant_id: a for a in applicants}

    row = by_id[CORNER_RISE_APPLICANT_IDS[0]]
    row.legal_name = "Corner Rise Bakery LLC"
    row.dba_name = None
    row.ein = "84-3921776"
    row.owner_ssn_last4 = "4417"
    row.email = "owner@cornerrisebakery.com"
    row.phone = "704-555-0182"
    row.tenant_id = "NSC_DIRECT"
    row.mailing_city, row.mailing_state, row.mailing_zip = ("Charlotte", "NC", "28205")
    row.created_at = dt.datetime(2023, 5, 18, 10, 41, 0)

    row = by_id[CORNER_RISE_APPLICANT_IDS[1]]
    row.legal_name = "Corner Rise Bakery, LLC"
    row.dba_name = None
    row.ein = "843921776"
    row.owner_ssn_last4 = "4417"
    row.email = "owner@cornerrisebakery.com"
    row.phone = "7045550182"
    row.tenant_id = "NSC_DIRECT"
    row.mailing_city, row.mailing_state, row.mailing_zip = ("Charlotte", "NC", "28205")
    row.created_at = dt.datetime(2024, 9, 3, 16, 22, 0)

    row = by_id[CORNER_RISE_APPLICANT_IDS[2]]
    row.legal_name = "Cornerrise Bakery LLC"
    row.dba_name = None
    row.ein = "84-3921767"
    row.owner_ssn_last4 = "4417"
    row.email = "accounting@cornerrisebakery.com"
    row.phone = "(704) 555-0182"
    row.tenant_id = "NSC_DIRECT"
    row.mailing_city, row.mailing_state, row.mailing_zip = ("Charlotte", "NC", "28205")
    row.created_at = dt.datetime(2025, 6, 27, 9, 5, 0)

    row = by_id[CORNER_RISE_APPLICANT_IDS[3]]
    row.legal_name = "CRB Holdings LLC"
    row.dba_name = "Corner Rise Bakery"
    row.ein = "84-3921776"
    row.owner_ssn_last4 = "4417"
    row.email = "j.mabry@cornerrisebakery.com"
    row.phone = "704-555-0182"
    row.tenant_id = "BAYLINE"
    row.mailing_city, row.mailing_state, row.mailing_zip = ("Charlotte", "NC", "28205")
    row.created_at = dt.datetime(2025, 11, 14, 14, 9, 0)


def apply_canon_statement_applicant(applicants):
    by_id = {a.applicant_id: a for a in applicants}
    row = by_id[CANON_STATEMENT_APPLICATION_ID]
    row.legal_name = "Harbor and Vine Provisions LLC"
    row.dba_name = "Harbor & Vine"
    row.ein = "56-2288104"
    row.tenant_id = "NSC_DIRECT"
    row.email = "ap@harborandvine.com"
    row.mailing_city, row.mailing_state, row.mailing_zip = ("Charlotte", "NC", "28203")


# --------------------------------------------------------------------------
# Step 2: application shells and the timeline model
# --------------------------------------------------------------------------

class App:
    pass


def build_apps(rng):
    """Assign every application a path, a product, and its raw time components."""
    tenants = []
    for tenant, count in TENANT_MIX:
        tenants.extend([tenant] * count)
    assert len(tenants) == TOTAL_APPLICATIONS
    rng.shuffle(tenants)

    # Submission times. Weekdays carry the volume. Weekends do not.
    span = dt.timedelta(days=WINDOW_SPAN_DAYS)
    window_end = WINDOW_START + span
    candidates = []
    while len(candidates) < SUBMITTED_APPLICATIONS * 3:
        offset = rng.random() * WINDOW_SPAN_DAYS
        moment = WINDOW_START + dt.timedelta(days=offset)
        day_weight = {5: 0.18, 6: 0.10}.get(moment.weekday(), 1.0)
        hour_weight = 0.15 + 0.85 * math.exp(
            -((moment.hour - 12.5) ** 2) / 26.0)
        if rng.random() <= day_weight * hour_weight:
            candidates.append(moment)
    candidates.sort()
    step = len(candidates) / float(SUBMITTED_APPLICATIONS)
    submit_times = [candidates[int(i * step)] for i in range(SUBMITTED_APPLICATIONS)]
    submit_times.sort()
    # Pin the ends. The rate query reads the first and last submitted event.
    submit_times[0] = WINDOW_START
    submit_times[-1] = window_end

    paths = (["DECISIONED"] * DECISIONED_APPLICATIONS
             + ["WITHDRAWN"] * WITHDRAWN_APPLICATIONS
             + ["STALLED"] * STALLED_APPLICATIONS)
    rng.shuffle(paths)

    apps = []
    for i in range(TOTAL_APPLICATIONS):
        app = App()
        app.application_id = i + 1
        app.applicant_id = i + 1
        app.tenant_id = tenants[i]
        app.product = pick_weighted(rng, PRODUCTS)
        apps.append(app)

    # Draft applications never reach the pipeline. Pick them off the middle of
    # the window so the volume shape is not dented at one end.
    draft_ids = sorted(rng.sample(range(2, TOTAL_APPLICATIONS), DRAFT_APPLICATIONS))
    draft_set = set(draft_ids)

    submitted_apps = [a for a in apps if a.application_id not in draft_set]
    assert len(submitted_apps) == SUBMITTED_APPLICATIONS

    for app in apps:
        app.is_draft = app.application_id in draft_set

    for app, moment, path in zip(submitted_apps, submit_times, paths):
        app.submit_ts = moment
        app.path = path

    for app in apps:
        if app.is_draft:
            app.path = "DRAFT"
            app.submit_ts = None

    # Where a stalled application is stuck has to be settled before rework,
    # because an application still waiting on its first upload has never been
    # in front of an underwriter and cannot have looped.
    for app in submitted_apps:
        app.stall_point = None
        if app.path == "STALLED":
            app.stall_point = (
                "PENDING_INFO" if rng.random() < 0.60 else "DOCS_REQUESTED")

    assign_rework(rng, submitted_apps)
    sample_components(rng, apps)
    assign_amounts(rng, apps)
    return apps


def assign_rework(rng, submitted_apps):
    """
    63 percent of applications go around at least once. Stalled and withdrawn
    applications are much more likely to have looped, because the loop is what
    killed them.
    """
    forced = []
    excluded = []
    pool = []
    for app in submitted_apps:
        if app.path == "STALLED" and app.stall_point == "DOCS_REQUESTED":
            excluded.append(app)          # never reached an underwriter
        elif app.path == "STALLED" and app.stall_point == "PENDING_INFO":
            forced.append(app)            # stuck in the loop right now
        else:
            pool.append(app)

    for app in excluded:
        app.reworked = False
    for app in forced:
        app.reworked = True

    remaining = REWORK_APPLICATIONS - len(forced)
    weights = {"WITHDRAWN": 0.79, "DECISIONED": 1.0}
    scored = [(rng.random() * (2.0 - weights[app.path]), app) for app in pool]
    scored.sort(key=lambda pair: pair[0])
    for index, (_, app) in enumerate(scored):
        app.reworked = index < remaining

    for app in submitted_apps:
        if not app.reworked:
            app.loops = 0
        else:
            roll = rng.random()
            app.loops = 1 if roll < 0.68 else (2 if roll < 0.92 else 3)


def sample_components(rng, apps):
    """Raw time components in days. Calibration scales them later."""
    for app in apps:
        if app.is_draft:
            app.draft_lead = rng.uniform(0.2, 9.0)
            continue

        app.draft_lead = lognorm(rng, 0.9, 1.1)
        app.t_ack = lognorm(rng, 0.055, 0.9)            # about 80 minutes
        app.doc_wait = lognorm(rng, 5.0, 0.86)
        app.queue = lognorm(rng, 1.05, 0.72)
        app.passes = [lognorm(rng, 0.52, 0.85) for _ in range(app.loops + 1)]
        app.rework_docs = [lognorm(rng, 2.6, 0.92) for _ in range(app.loops)]
        app.rework_queue = [lognorm(rng, 0.10, 0.80) for _ in range(app.loops)]

        # Hands-on sessions. One to three per review pass, 6 to 40 minutes each.
        app.sessions = []
        for _ in range(app.loops + 1):
            count = 1 if rng.random() < 0.58 else (2 if rng.random() < 0.8 else 3)
            app.sessions.append(
                [lognorm(rng, 14.0, 0.55) for _ in range(count)])

        # About 6 percent of review sessions never get a close event. The
        # reviewer closed the tab. Defect D-24.
        app.session_closed = [
            [rng.random() > 0.06 for _ in row] for row in app.sessions]

        app.withdraw_point = "PENDING_INFO" if (
            app.reworked and rng.random() < 0.72) else "IN_REVIEW"
        app.stall_days = lognorm(rng, 34.0, 0.5)
        app.underwriter = rng.choice(UNDERWRITERS)
        app.decline = None


def assign_amounts(rng, apps):
    ranges = {
        "TERM_LOAN": (35000, 750000),
        "LOC": (25000, 400000),
        "EQUIPMENT": (40000, 900000),
        "SBA_7A": (150000, 2500000),
    }
    for app in apps:
        low, high = ranges[app.product]
        raw = math.exp(rng.uniform(math.log(low), math.log(high)))
        step = 5000 if raw > 100000 else 1000
        app.amount_requested = float(int(raw / step) * step)
        if app.application_id == CANON_STATEMENT_APPLICATION_ID:
            app.product = "SBA_7A"
            app.amount_requested = 1200000.0


# --------------------------------------------------------------------------
# Step 3: calibration
# --------------------------------------------------------------------------

def scale_to_target(values, target):
    current = median_of(values)
    if current <= 0:
        return 1.0
    return target / current


def calibrate(apps):
    """
    Scale each component so the measured median equals the canon number.

    Order matters. The document wait, the rework cost, and the hands-on time
    are independent of each other, so they get scaled directly. Cycle time is
    the sum of everything, so it gets a bisection on the two components nobody
    quotes a target for: the queue wait and the review pass.
    """
    submitted = [a for a in apps if not a.is_draft]

    # Document wait. Population is every application that got to DOCS_RECEIVED.
    doc_pop = [a for a in submitted if has_docs_received(a)]
    factor = scale_to_target([a.doc_wait for a in doc_pop], TARGET_DOC_WAIT_DAYS)
    for app in submitted:
        app.doc_wait *= factor

    # Rework cost. One value per completed loop, measured from the PENDING_INFO
    # event to the next IN_REVIEW event.
    loop_values = []
    for app in submitted:
        for index in range(completed_loops(app)):
            loop_values.append(app.rework_docs[index] + app.rework_queue[index])
    factor = scale_to_target(loop_values, TARGET_REWORK_DAYS)
    for app in submitted:
        app.rework_docs = [v * factor for v in app.rework_docs]
        app.rework_queue = [v * factor for v in app.rework_queue]

    # Hands-on time. Only closed sessions count, same as the SQL.
    per_app = []
    for app in submitted:
        total = paired_session_minutes(app)
        if total is not None:
            per_app.append(total)
    factor = scale_to_target(per_app, TARGET_HANDS_ON_MINUTES)
    scale_sessions(apps, factor)
    return calibrate_cycle(apps)


def scale_sessions(apps, factor):
    for app in apps:
        if app.is_draft:
            continue
        app.sessions = [[v * factor for v in row] for row in app.sessions]


def scale_doc_wait(apps, factor):
    for app in apps:
        if not app.is_draft:
            app.doc_wait *= factor


def scale_rework(apps, factor):
    for app in apps:
        if app.is_draft:
            continue
        app.rework_docs = [v * factor for v in app.rework_docs]
        app.rework_queue = [v * factor for v in app.rework_queue]


def calibrate_cycle(apps):
    """Bisect the queue and review pass scale until the median cycle is 9.4."""
    submitted = [a for a in apps if not a.is_draft]
    base_queue = {a.application_id: a.queue for a in submitted}
    base_passes = {a.application_id: list(a.passes) for a in submitted}

    def cycle_median(k):
        for app in submitted:
            app.queue = base_queue[app.application_id] * k
            app.passes = [v * k for v in base_passes[app.application_id]]
        return median_of([cycle_days(a) for a in submitted
                          if a.path == "DECISIONED"])

    low, high = 0.01, 40.0
    for _ in range(200):
        mid = (low + high) / 2.0
        if cycle_median(mid) < TARGET_CYCLE_DAYS:
            low = mid
        else:
            high = mid
    cycle_median((low + high) / 2.0)
    return (low + high) / 2.0


def has_docs_received(app):
    """A stalled application waiting on its first upload never gets there."""
    if app.path == "STALLED" and app.stall_point == "DOCS_REQUESTED":
        return False
    return True


def completed_loops(app):
    """
    A stalled application is sitting in PENDING_INFO, so its last loop never
    closed. A withdrawn application that quit from PENDING_INFO is the same.
    """
    if app.loops == 0:
        return 0
    if app.path == "STALLED" and app.stall_point == "PENDING_INFO":
        return app.loops - 1
    if app.path == "WITHDRAWN" and app.withdraw_point == "PENDING_INFO":
        return app.loops - 1
    return app.loops


SESSION_TAIL_MINUTES = 25.0


def pass_days(app, index):
    """
    A review pass cannot be shorter than the work done inside it. When the
    sampled pass is too short, the sessions set the floor.
    """
    needed = (sum(app.sessions[index]) + SESSION_TAIL_MINUTES) / 1440.0
    return max(app.passes[index], needed)


def cycle_days(app):
    total = app.t_ack + app.doc_wait + app.queue
    for index in range(app.loops + 1):
        total += pass_days(app, index)
        if index < app.loops:
            total += app.rework_docs[index] + app.rework_queue[index]
    return total


def emitted_passes(app):
    """
    How many review passes actually happen. An application that stalled or was
    withdrawn stops partway, so its later passes never exist.
    """
    if app.path == "STALLED" and app.stall_point == "DOCS_REQUESTED":
        return 0
    if app.path == "STALLED" and app.stall_point == "PENDING_INFO":
        return app.loops
    if app.path == "WITHDRAWN" and app.withdraw_point == "PENDING_INFO" and app.loops:
        return app.loops
    return app.loops + 1


def paired_session_minutes(app):
    total = 0.0
    found = False
    limit = emitted_passes(app)
    for row, closed_row in zip(app.sessions[:limit], app.session_closed[:limit]):
        for value, closed in zip(row, closed_row):
            if closed:
                total += value
                found = True
    return total if found else None


# --------------------------------------------------------------------------
# Step 4: events
# --------------------------------------------------------------------------

class Event:
    __slots__ = ("application_id", "event_type", "from_status", "to_status",
                 "actor_type", "actor_id", "occurred_at", "recorded_at",
                 "detail")


def make_event(app_id, event_type, from_status, to_status, actor_type,
               actor_id, occurred_at, recorded_at=None, detail=None):
    e = Event()
    e.application_id = app_id
    e.event_type = event_type
    e.from_status = from_status
    e.to_status = to_status
    e.actor_type = actor_type
    e.actor_id = actor_id
    e.occurred_at = occurred_at
    e.recorded_at = recorded_at or occurred_at + dt.timedelta(
        milliseconds=40 + (app_id % 700))
    e.detail = detail
    return e


PENDING_INFO_REASONS = [
    "Missing month 3 bank statement",
    "Bank statement unreadable, requested a clean copy",
    "Need signed 4506-C",
    "Need most recent business tax return",
    "Voided check missing",
    "Requested AR aging as of month end",
    "Statement is for the wrong account",
    "Need proof of ownership for second member",
    "Debt schedule incomplete",
    "Requested explanation of large deposit",
]

DECLINE_CODES = [
    "DSCR_BELOW_MIN", "REVENUE_BELOW_MIN", "TIME_IN_BUSINESS",
    "CREDIT_SCORE", "EXISTING_DEBT", "INDUSTRY_RESTRICTED",
    "NSF_ACTIVITY", "UNVERIFIED_REVENUE", "COLLATERAL_SHORTFALL",
    "STACKED_DEBT",
]

APPROVE_CODES = [
    "DSCR_OK", "REVENUE_VERIFIED", "TIB_OK", "CREDIT_OK", "COLLATERAL_OK",
    "MANUAL_OVERRIDE_RB", "POLICY_EXCEPTION_APPROVED",
]


def build_events(rng, apps):
    events = []
    for app in apps:
        if app.is_draft:
            app.created_at = WINDOW_START + dt.timedelta(
                days=rng.uniform(0.5, WINDOW_SPAN_DAYS - 0.5))
            app.status = "DRAFT"
            app.decided_event_at = None
            app.decided_at = None
            app.submitted_at = None
            assign_customer_id(rng, app)
            events.append(make_event(
                app.application_id, "CREATED", None, "DRAFT", "APPLICANT",
                "portal", app.created_at))
            app.updated_at = app.created_at
            continue

        created = app.submit_ts - dt.timedelta(days=app.draft_lead)
        app.created_at = created
        events.append(make_event(
            app.application_id, "CREATED", None, "DRAFT", "APPLICANT",
            "portal", created))

        events.append(make_event(
            app.application_id, "SUBMITTED", "DRAFT", "SUBMITTED", "APPLICANT",
            "portal", app.submit_ts))
        cursor = app.submit_ts
        status = "SUBMITTED"

        cursor = cursor + dt.timedelta(days=app.t_ack)
        events.append(make_event(
            app.application_id, "DOCS_REQUESTED", status, "DOCS_REQUESTED",
            "SYSTEM", "intake-worker", cursor,
            detail="Standard package for " + app.product))
        status = "DOCS_REQUESTED"
        app.docs_requested_at = cursor

        if app.path == "STALLED" and app.stall_point == "DOCS_REQUESTED":
            app.status = "DOCS_REQUESTED"
            app.decided_event_at = None
            app.updated_at = cursor
            finish_application_fields(rng, app, events)
            continue

        cursor = cursor + dt.timedelta(days=app.doc_wait)
        events.append(make_event(
            app.application_id, "DOCS_RECEIVED", status, "DOCS_RECEIVED",
            "APPLICANT", "portal", cursor))
        status = "DOCS_RECEIVED"
        app.docs_received_at = cursor

        cursor = cursor + dt.timedelta(days=app.queue)

        terminal = None
        for index in range(app.loops + 1):
            events.append(make_event(
                app.application_id, "IN_REVIEW", status, "IN_REVIEW",
                "UNDERWRITER", app.underwriter, cursor))
            status = "IN_REVIEW"
            pass_start = cursor
            pass_end = cursor + dt.timedelta(days=pass_days(app, index))

            emit_sessions(app, index, pass_start, pass_end, events, rng)
            cursor = pass_end

            last_pass = index == app.loops
            if app.path == "WITHDRAWN" and app.withdraw_point == "IN_REVIEW" and last_pass:
                terminal = ("WITHDRAWN", cursor)
                break

            if not last_pass:
                events.append(make_event(
                    app.application_id, "PENDING_INFO", status,
                    "PENDING_INFO", "UNDERWRITER", app.underwriter, cursor,
                    detail=rng.choice(PENDING_INFO_REASONS)))
                status = "PENDING_INFO"
                stop_here = (
                    (app.path == "STALLED" and app.stall_point == "PENDING_INFO"
                     and index == app.loops - 1)
                    or (app.path == "WITHDRAWN"
                        and app.withdraw_point == "PENDING_INFO"
                        and index == app.loops - 1))
                if stop_here:
                    if app.path == "WITHDRAWN":
                        cursor = cursor + dt.timedelta(
                            days=min(app.stall_days, 21.0))
                        terminal = ("WITHDRAWN", cursor)
                    else:
                        terminal = ("STALL", cursor)
                    break
                cursor = cursor + dt.timedelta(days=app.rework_docs[index])
                events.append(make_event(
                    app.application_id, "DOCS_RECEIVED", status,
                    "DOCS_RECEIVED", "APPLICANT", "portal", cursor))
                status = "DOCS_RECEIVED"
                cursor = cursor + dt.timedelta(days=app.rework_queue[index])
            else:
                terminal = ("DECISIONED", cursor)

        if terminal is None:
            terminal = ("DECISIONED", cursor)

        kind, when = terminal
        if kind == "STALL":
            app.status = "PENDING_INFO"
            app.decided_event_at = None
            app.updated_at = when
        elif kind == "WITHDRAWN":
            events.append(make_event(
                app.application_id, "WITHDRAWN", status, "WITHDRAWN",
                "APPLICANT", "portal", when,
                detail="Applicant withdrew"))
            app.status = "WITHDRAWN"
            app.decided_event_at = None
            app.updated_at = when
        else:
            events.append(make_event(
                app.application_id, "DECISIONED", status, "DECISIONED",
                "UNDERWRITER", app.underwriter, when))
            app.decided_event_at = when
            approve = rng.random() < 0.62
            app.decline = not approve
            after = when + dt.timedelta(minutes=rng.uniform(1, 55))
            if approve:
                events.append(make_event(
                    app.application_id, "APPROVED", "DECISIONED", "APPROVED",
                    "SYSTEM", "underwriting-service", after))
                app.status = "APPROVED"
                app.updated_at = after
                if rng.random() < 0.81:
                    funded = after + dt.timedelta(days=lognorm(rng, 4.0, 0.6))
                    if funded < EXTRACT_NOW:
                        events.append(make_event(
                            app.application_id, "FUNDED", "APPROVED", "FUNDED",
                            "SYSTEM", "loancore-sync", funded))
                        app.status = "FUNDED"
                        app.updated_at = funded
            else:
                events.append(make_event(
                    app.application_id, "DECLINED", "DECISIONED", "DECLINED",
                    "SYSTEM", "underwriting-service", after))
                app.status = "DECLINED"
                app.updated_at = after

        finish_application_fields(rng, app, events)
    return events


def emit_sessions(app, index, pass_start, pass_end, events, rng):
    """
    Lay the review sessions inside the pass. The underwriter opens the file,
    works it, closes it, and comes back later. Six percent of the time the
    close event never lands.
    """
    durations = app.sessions[index]
    closed_flags = app.session_closed[index]
    span = (pass_end - pass_start).total_seconds() - SESSION_TAIL_MINUTES * 60.0
    work = sum(durations) * 60.0
    slack = max(0.0, span - work)

    # Split the idle time into the gaps before each session. The file sits in
    # the queue, the underwriter picks it up, puts it down, picks it up again.
    weights = [rng.random() + 0.05 for _ in range(len(durations) + 1)]
    total_weight = sum(weights)
    cursor = 0.0
    for slot, (minutes, closed) in enumerate(zip(durations, closed_flags)):
        cursor += slack * weights[slot] / total_weight
        opened = pass_start + dt.timedelta(seconds=cursor)
        events.append(make_event(
            app.application_id, "REVIEW_OPENED", None, None, "UNDERWRITER",
            app.underwriter, opened))
        if closed:
            events.append(make_event(
                app.application_id, "REVIEW_CLOSED", None, None, "UNDERWRITER",
                app.underwriter, opened + dt.timedelta(minutes=minutes)))
        cursor += minutes * 60.0


TARGET_STAMP_GAP_MINUTES = 40.0


def assign_submitted_at_offsets(rng, apps):
    """
    applications.submitted_at is written by the portal on the client, so it is
    never the same as the SUBMITTED event the backend recorded. Four ways it
    goes wrong, and the normal case is calibrated to a median gap of exactly
    40 minutes. This is defect D-11.
    """
    submitted = [a for a in apps if not a.is_draft]
    for app in submitted:
        roll = rng.random()
        if roll < 0.021:
            app.stamp_kind = "NULL"          # the portal write failed outright
        elif roll < 0.061:
            app.stamp_kind = "BACKFILL"      # nightly job filled it in at 02:10
        elif roll < 0.076:
            app.stamp_kind = "TZ"            # old build sent local time, no offset
        elif roll < 0.093:
            app.stamp_kind = "DOUBLE"        # applicant clicked submit twice, days apart
        else:
            app.stamp_kind = "NORMAL"

    for app in submitted:
        if app.stamp_kind == "NORMAL":
            app.stamp_gap = lognorm(rng, TARGET_STAMP_GAP_MINUTES, 0.7)
        elif app.stamp_kind == "DOUBLE":
            app.stamp_gap = lognorm(rng, 1.6, 0.7) * 1440.0
        elif app.stamp_kind == "TZ":
            app.stamp_gap = 300.0
        elif app.stamp_kind == "BACKFILL":
            next_day = (app.submit_ts + dt.timedelta(days=1)).replace(
                hour=2, minute=10, second=0)
            app.stamp_gap = (next_day - app.submit_ts).total_seconds() / 60.0
        else:
            app.stamp_gap = None

    base = {a.application_id: a.stamp_gap for a in submitted
            if a.stamp_kind == "NORMAL"}

    def overall_median(scale):
        values = []
        for app in submitted:
            if app.stamp_gap is None:
                continue
            if app.stamp_kind == "NORMAL":
                values.append(base[app.application_id] * scale)
            else:
                values.append(app.stamp_gap)
        return median_of(values)

    low, high = 0.01, 100.0
    for _ in range(120):
        mid = (low + high) / 2.0
        if overall_median(mid) < TARGET_STAMP_GAP_MINUTES:
            low = mid
        else:
            high = mid
    scale = (low + high) / 2.0
    for app in submitted:
        if app.stamp_kind == "NORMAL":
            app.stamp_gap = base[app.application_id] * scale


def assign_customer_id(rng, app):
    """
    customer_id. Bayline onboarding in 2020 needed a partner code and nobody
    wanted to touch the applicants table, so a second tenant convention landed
    here. Three formats and a lot of nulls. Defect D-07.
    """
    app.customer_id = None
    if app.tenant_id == "NSC_DIRECT":
        roll = rng.random()
        if roll < 0.68:
            app.customer_id = None
        elif roll < 0.86:
            app.customer_id = "NSC-DIRECT"
        elif roll < 0.97:
            app.customer_id = "1"
        else:
            app.customer_id = "NSC_DIRECT"
    elif app.tenant_id == "BAYLINE":
        roll = rng.random()
        if roll < 0.44:
            app.customer_id = "BAY"
        elif roll < 0.72:
            app.customer_id = "bayline"
        elif roll < 0.88:
            app.customer_id = "2"
        else:
            app.customer_id = None
    else:
        roll = rng.random()
        if roll < 0.51:
            app.customer_id = "CASCADE-FUNDING"
        elif roll < 0.77:
            app.customer_id = "CSC"
        elif roll < 0.9:
            app.customer_id = "3"
        else:
            app.customer_id = None


def finish_application_fields(rng, app, events):
    """applications.submitted_at and applications.decided_at, both written
    outside the event stream and both wrong in their own way."""
    assign_customer_id(rng, app)
    if app.is_draft:
        app.submitted_at = None
        app.decided_at = None
        return

    if app.stamp_kind == "NULL":
        app.submitted_at = None
    elif app.stamp_kind in ("BACKFILL", "TZ"):
        app.submitted_at = app.submit_ts + dt.timedelta(minutes=app.stamp_gap)
    else:
        app.submitted_at = app.submit_ts - dt.timedelta(minutes=app.stamp_gap)

    app.decided_at = None
    if app.decided_event_at is not None:
        if rng.random() < 0.14:
            app.decided_at = None                     # CRM sync never ran
        else:
            nightly = (app.decided_event_at + dt.timedelta(days=1)).replace(
                hour=2, minute=int(rng.uniform(5, 50)))
            app.decided_at = (
                nightly if rng.random() < 0.55
                else app.decided_event_at + dt.timedelta(
                    minutes=rng.uniform(1, 240)))


def plant_tenant_mismatches(rng, apps):
    """
    Eleven applications where customer_id points at a different brand than
    applicants.tenant_id. This is the row set Mission 24 needs.
    """
    pool = [a for a in apps if not a.is_draft and a.tenant_id == "NSC_DIRECT"]
    chosen = rng.sample(pool, 11)
    for index, app in enumerate(chosen):
        app.customer_id = "BAY" if index % 2 == 0 else "CASCADE-FUNDING"
    return [a.application_id for a in chosen]


# --------------------------------------------------------------------------
# Step 5: documents, extractions, transactions, decisions, fraud
# --------------------------------------------------------------------------

DOC_TYPES = [
    ("BANK_STATEMENT", 0.42),
    ("TAX_RETURN", 0.16),
    ("DRIVERS_LICENSE", 0.11),
    ("VOIDED_CHECK", 0.10),
    ("AR_AGING", 0.08),
    ("DEBT_SCHEDULE", 0.07),
    ("OTHER", 0.06),
]

DOC_SOURCES = [
    ("PORTAL_UPLOAD", 0.52),
    ("EMAIL", 0.24),
    ("FAX", 0.09),
    ("LEDGERLINK", 0.11),
    ("BRANCH_SCAN", 0.04),
]

MIME_BY_TYPE = {
    "BANK_STATEMENT": "application/pdf",
    "TAX_RETURN": "application/pdf",
    "DRIVERS_LICENSE": "image/jpeg",
    "VOIDED_CHECK": "image/jpeg",
    "AR_AGING": "application/vnd.ms-excel",
    "DEBT_SCHEDULE": "application/vnd.ms-excel",
    "OTHER": "application/pdf",
}


class Document:
    pass


def build_documents(rng, apps, applicants_by_id):
    documents = []
    doc_id = 0
    for app in apps:
        if app.is_draft:
            # Most drafts have nothing attached. A few have one stray upload.
            count = 1 if rng.random() < 0.3 else 0
        else:
            count = (2 if rng.random() < 0.2 else (
                3 if rng.random() < 0.5 else (
                    4 if rng.random() < 0.75 else rng.randint(5, 8))))
            if app.path == "STALLED" and app.stall_point == "DOCS_REQUESTED":
                count = min(count, 1)

        for index in range(count):
            doc_id += 1
            d = Document()
            d.document_id = doc_id
            d.application_id = app.application_id
            if index == 0:
                d.doc_type = "BANK_STATEMENT"
            else:
                d.doc_type = pick_weighted(rng, DOC_TYPES)
            d.source = pick_weighted(rng, DOC_SOURCES)
            d.mime_type = MIME_BY_TYPE[d.doc_type]
            if d.source == "FAX":
                d.mime_type = "application/pdf"
            d.page_count = (
                rng.randint(3, 14) if d.doc_type == "BANK_STATEMENT"
                else rng.randint(1, 30))
            d.size_bytes = d.page_count * rng.randint(48000, 320000)

            base = app.created_at if app.is_draft else getattr(
                app, "docs_received_at", app.docs_requested_at)
            d.uploaded_at = base + dt.timedelta(
                minutes=rng.uniform(-90, 5000) if not app.is_draft else 30)
            if d.uploaded_at > EXTRACT_NOW:
                d.uploaded_at = EXTRACT_NOW - dt.timedelta(days=1)

            applicant = applicants_by_id[app.applicant_id]
            slug = applicant.legal_name.lower().replace(" ", "-")
            slug = "".join(c for c in slug if c.isalnum() or c == "-")
            d.file_name = "%s-%s-%s.%s" % (
                slug[:28], d.doc_type.lower(),
                d.uploaded_at.strftime("%Y%m"),
                "pdf" if "pdf" in d.mime_type else (
                    "jpg" if "jpeg" in d.mime_type else "xls"))
            if d.source == "FAX":
                d.file_name = "fax-%s-%04d.pdf" % (
                    d.uploaded_at.strftime("%Y%m%d"), doc_id % 10000)
            if d.source == "EMAIL" and rng.random() < 0.4:
                d.file_name = rng.choice(
                    ["scan0012.pdf", "IMG_4471.pdf", "document (2).pdf",
                     "statement final.pdf", "Untitled.pdf",
                     "bank stuff.pdf", "SCAN_20260214_0001.pdf"])

            d.storage_key = "northstar-documents/%s/%d/%d/%s" % (
                app.tenant_id.lower(), app.application_id, d.document_id,
                d.file_name)
            d.uploaded_by = (
                applicant.email if d.source == "PORTAL_UPLOAD"
                else ("intake@northstarcapital.com" if d.source == "EMAIL"
                      else "system"))
            d.status = "PARSED" if rng.random() < 0.88 else rng.choice(
                ["RECEIVED", "PARSE_FAILED", "QUARANTINED"])

            # sha256 arrived in V9 for the portal path only. Everything that
            # comes in by email, fax, or vendor pull still has none. D-09.
            if d.source == "PORTAL_UPLOAD" and rng.random() < 0.93:
                d.sha256 = hashlib.sha256(
                    ("%s|%d" % (d.file_name, d.document_id)).encode()).hexdigest()
            else:
                d.sha256 = None

            # OCR quality drives everything downstream.
            if d.source in ("FAX", "BRANCH_SCAN"):
                d.ocr_quality = "poor" if rng.random() < 0.72 else "fair"
            elif d.source == "EMAIL":
                d.ocr_quality = pick_weighted(
                    rng, [("good", 0.5), ("fair", 0.33), ("poor", 0.17)])
            else:
                d.ocr_quality = pick_weighted(
                    rng, [("good", 0.84), ("fair", 0.13), ("poor", 0.03)])

            documents.append(d)

    # The canonical statement document gets pinned so Mission 20 can quote it.
    canon_docs = [d for d in documents
                  if d.application_id == CANON_STATEMENT_APPLICATION_ID
                  and d.doc_type == "BANK_STATEMENT"]
    canon_doc = canon_docs[0]
    canon_doc.file_name = "harbor-and-vine-2025-05-statement.pdf"
    canon_doc.source = "PORTAL_UPLOAD"
    canon_doc.mime_type = "application/pdf"
    canon_doc.ocr_quality = "good"
    canon_doc.page_count = 6
    canon_doc.status = "PARSED"
    canon_doc.sha256 = hashlib.sha256(b"harbor-and-vine-2025-05").hexdigest()
    canon_doc.storage_key = "northstar-documents/nsc_direct/%d/%d/%s" % (
        CANON_STATEMENT_APPLICATION_ID, canon_doc.document_id,
        canon_doc.file_name)

    # Two identical statements uploaded twice through different paths. One has
    # a sha256, the other does not, so the dedupe check cannot see the pair.
    duplicates = []
    portal_docs = [d for d in documents
                   if d.doc_type == "BANK_STATEMENT" and d.sha256]
    for source_doc in rng.sample(portal_docs, 34):
        doc_id += 1
        clone = Document()
        for slot in vars(source_doc):
            setattr(clone, slot, getattr(source_doc, slot))
        clone.document_id = doc_id
        clone.source = "EMAIL"
        clone.sha256 = None
        clone.file_name = "RE FW " + source_doc.file_name
        clone.uploaded_at = source_doc.uploaded_at + dt.timedelta(
            days=rng.uniform(0.2, 4.0))
        clone.uploaded_by = "intake@northstarcapital.com"
        clone.storage_key = source_doc.storage_key.replace(
            "/%d/" % source_doc.document_id, "/%d/" % doc_id)
        duplicates.append(clone)
    documents.extend(duplicates)
    return documents, canon_doc


EXTRACT_FIELDS = [
    "business_name", "ein", "account_number", "statement_period_start",
    "statement_period_end", "ending_balance", "total_deposits",
    "total_withdrawals", "nsf_count",
]

EXTRACTORS = [
    ("OPTISCAN_V2", "2.14.3", 0.61),
    ("OPTISCAN_V3", "3.1.0", 0.27),
    ("MANUAL", "n/a", 0.08),
    ("AI_SERVICE", "0.4.1", 0.04),
]


class Extraction:
    pass


def build_extractions(rng, documents, applicants_by_id, apps_by_id):
    """
    OptiScan reports a confidence on every field. Nobody ever checked whether
    it lines up with being right. It does not. On poor scans the confidence is
    slightly higher, because the engine is scoring its own character match on
    garbage. Defect D-05.
    """
    rows = []
    extraction_id = 0
    correct_rate = {"good": 0.96, "fair": 0.82, "poor": 0.45}
    for doc in documents:
        if doc.doc_type not in ("BANK_STATEMENT", "TAX_RETURN"):
            continue
        if doc.status in ("RECEIVED", "QUARANTINED"):
            continue
        extractor = pick_weighted(
            rng, [(n, w) for n, v, w in EXTRACTORS])
        version = {n: v for n, v, _ in EXTRACTORS}[extractor]
        fields = EXTRACT_FIELDS if doc.doc_type == "BANK_STATEMENT" else [
            "business_name", "ein", "gross_receipts", "net_income", "tax_year"]
        app = apps_by_id[doc.application_id]
        applicant = applicants_by_id[app.applicant_id]

        for field in fields:
            extraction_id += 1
            e = Extraction()
            e.extraction_id = extraction_id
            e.document_id = doc.document_id
            e.extractor = extractor
            e.extractor_version = version
            e.field_name = field
            e.extracted_at = doc.uploaded_at + dt.timedelta(
                seconds=rng.uniform(20, 900))

            is_right = rng.random() < correct_rate[doc.ocr_quality]
            e.field_value = extraction_value(
                rng, field, applicant, app, doc, is_right)

            # Confidence. Same shape everywhere, a touch higher on bad scans.
            bump = {"good": 0.0, "fair": 0.012, "poor": 0.028}[doc.ocr_quality]
            if extractor == "MANUAL":
                e.confidence = 1.0
                is_right = rng.random() < 0.985
            else:
                value = 0.955 + bump + rng.gauss(0, 0.031)
                e.confidence = round(min(0.9999, max(0.5, value)), 4)

            # QA only ever sampled about a quarter of extractions. That sample
            # is the only place correctness is recorded.
            e.is_correct = is_right if rng.random() < 0.26 else None
            e.raw_response = json.dumps({
                "field": field,
                "value": e.field_value,
                "confidence": e.confidence,
                "engine": extractor.lower(),
                "page": rng.randint(1, max(1, doc.page_count)),
                "bbox": [rng.randint(20, 400), rng.randint(20, 700),
                         rng.randint(60, 500), rng.randint(30, 720)],
            }, separators=(",", ":"))
            rows.append(e)
    return rows


def extraction_value(rng, field, applicant, app, doc, is_right):
    if field == "business_name":
        if is_right:
            return applicant.legal_name
        return garble(rng, applicant.legal_name)
    if field == "ein":
        if is_right:
            return applicant.ein or ""
        if applicant.ein is None:
            return "%02d-%07d" % (rng.randint(20, 99), rng.randint(0, 9999999))
        return garble_digits(rng, applicant.ein)
    if field == "account_number":
        return "****%04d" % rng.randint(0, 9999)
    if field == "statement_period_start":
        return (doc.uploaded_at - dt.timedelta(days=rng.randint(35, 60))
                ).strftime("%Y-%m-01")
    if field == "statement_period_end":
        return (doc.uploaded_at - dt.timedelta(days=rng.randint(5, 34))
                ).strftime("%Y-%m-28")
    if field == "ending_balance":
        base = rng.uniform(1500, 240000)
        return money(base if is_right else base * rng.choice([10, 0.1, 1.09]))
    if field == "total_deposits":
        base = rng.uniform(18000, 420000)
        return money(base if is_right else base * rng.choice([10, 0.1, 1.4]))
    if field == "total_withdrawals":
        return money(rng.uniform(12000, 380000))
    if field == "nsf_count":
        return str(rng.randint(0, 6) if is_right else rng.randint(0, 1))
    if field == "gross_receipts":
        return money(rng.uniform(120000, 4200000))
    if field == "net_income":
        return money(rng.uniform(-40000, 620000))
    if field == "tax_year":
        return str(rng.choice([2023, 2024, 2025]))
    return ""


GARBLE_MAP = {"O": "0", "0": "O", "I": "1", "1": "I", "S": "5", "5": "S",
              "B": "8", "8": "B", "l": "1", "rn": "m", "m": "rn"}


def garble(rng, text):
    chars = list(text)
    for _ in range(max(1, len(chars) // 7)):
        index = rng.randrange(len(chars))
        chars[index] = GARBLE_MAP.get(chars[index], chars[index])
    out = "".join(chars)
    if rng.random() < 0.3:
        out = out.replace(" ", "")
    return out


def garble_digits(rng, ein):
    digits = [c for c in ein if c.isdigit()]
    if len(digits) < 3:
        return ein
    index = rng.randrange(len(digits) - 1)
    digits[index], digits[index + 1] = digits[index + 1], digits[index]
    joined = "".join(digits)
    return joined[:2] + "-" + joined[2:]


CREDIT_DESCRIPTIONS = [
    ("STRIPE PAYOUT", "CARD_SETTLEMENT", 0.24),
    ("SQUARE INC          DEPOSIT", "CARD_SETTLEMENT", 0.14),
    ("TOAST POS SETTLEMENT", "CARD_SETTLEMENT", 0.07),
    ("MERCHANT BANKCD DEP", "CARD_SETTLEMENT", 0.09),
    ("ACH CREDIT CUSTOMER PMT", "ACH_CREDIT", 0.17),
    ("REMOTE DEPOSIT CAPTURE", "CHECK_DEPOSIT", 0.11),
    ("WIRE IN REF 8841", "WIRE_IN", 0.05),
    ("SHOPIFY PAYMENTS PAYOUT", "CARD_SETTLEMENT", 0.06),
    ("AMEX SETTLEMENT", "CARD_SETTLEMENT", 0.07),
]

DEBIT_DESCRIPTIONS = [
    ("GUSTO PAYROLL", "PAYROLL", 0.16),
    ("ADP PAYROLL FEES", "PAYROLL", 0.05),
    ("COMMERCIAL RENT ACH", "RENT", 0.09),
    ("DUKE ENERGY BILLPAY", "UTILITIES", 0.08),
    ("SYSCO FOOD SERVICE", "SUPPLIER", 0.10),
    ("US FOODS ACH DEBIT", "SUPPLIER", 0.07),
    ("HOME DEPOT PRO", "SUPPLIER", 0.06),
    ("SBA LOAN PAYMENT", "DEBT_SERVICE", 0.05),
    ("CARD PAYMENT THANK YOU", "OTHER", 0.07),
    ("INSURANCE PREMIUM ACH", "INSURANCE", 0.05),
    ("STATE TAX PAYMENT", "TAX", 0.05),
    ("NSF FEE", "FEE", 0.04),
    ("OVERDRAFT ITEM FEE", "FEE", 0.03),
    ("ATM WITHDRAWAL", "OTHER", 0.04),
    ("VENDOR CHECK 1042", "SUPPLIER", 0.06),
]

TRANSFER_DESCRIPTIONS = [
    "TRANSFER FROM SAVINGS ****1221",
    "ONLINE TRANSFER FROM SAV 8842",
    "INTERNAL XFER FROM MMKT",
    "TRANSFER FROM BUS SAVINGS",
]

COMPETITOR_DESCRIPTIONS = [
    "FASTCAPITAL LOAN",
    "FASTCAPITAL FUNDING LLC ACH",
    "FASTCAP ADVANCE DEPOSIT",
    "FASTCAPITAL LOAN PROCEEDS",
]

CANON_STATEMENT = [
    ("05-04", "STRIPE PAYOUT", 48230.00, "CARD_SETTLEMENT"),
    ("05-06", "TRANSFER FROM SAVINGS", 30000.00, "INTERNAL_TRANSFER"),
    ("05-11", "STRIPE PAYOUT", 51340.00, "CARD_SETTLEMENT"),
    ("05-18", "FASTCAPITAL LOAN", 75000.00, "LOAN_PROCEEDS"),
    ("05-22", "STRIPE PAYOUT", 47830.00, "CARD_SETTLEMENT"),
]


class Transaction:
    pass


def build_transactions(rng, documents, apps_by_id, canon_doc):
    """
    One statement month per bank statement document, sometimes three. Credits
    include internal transfers and competitor loan proceeds, which is exactly
    why counting every credit gives the wrong revenue.
    """
    rows = []
    txn_id = 0
    statements = [d for d in documents if d.doc_type == "BANK_STATEMENT"
                  and d.status == "PARSED"]

    for doc in statements:
        if doc.document_id == canon_doc.document_id:
            continue
        app = apps_by_id[doc.application_id]
        months = 3 if app.amount_requested > 400000 and rng.random() < 0.6 else 1
        account = "%04d" % rng.randint(0, 9999)
        balance = rng.uniform(4000, 180000)
        scale = max(0.35, min(6.0, app.amount_requested / 180000.0))
        has_competitor = rng.random() < FASTCAPITAL_SHARE

        period_end = doc.uploaded_at.date() - dt.timedelta(
            days=rng.randint(6, 30))
        for month_index in range(months):
            month_end = period_end - dt.timedelta(days=30 * month_index)
            month_start = month_end - dt.timedelta(days=29)
            credits = rng.randint(4, 11)
            debits = rng.randint(9, 22)

            entries = []
            for _ in range(credits):
                description, category, _ = pick_weighted(
                    rng, [(triple, triple[2]) for triple in CREDIT_DESCRIPTIONS])
                amount = round(rng.uniform(2200, 62000) * scale, 2)
                entries.append((description, category, amount))
            if rng.random() < 0.31:
                entries.append((rng.choice(TRANSFER_DESCRIPTIONS),
                                "INTERNAL_TRANSFER",
                                round(rng.uniform(5000, 60000), 2)))
            if has_competitor and month_index == 0:
                entries.append((rng.choice(COMPETITOR_DESCRIPTIONS),
                                "LOAN_PROCEEDS",
                                round(rng.uniform(25000, 180000) / 500) * 500.0))
            for _ in range(debits):
                description, category, _ = pick_weighted(
                    rng, [(triple, triple[2]) for triple in DEBIT_DESCRIPTIONS])
                amount = -round(rng.uniform(180, 34000) * scale, 2)
                if category == "FEE":
                    amount = -round(rng.choice([29.0, 35.0, 36.0, 15.0]), 2)
                entries.append((description, category, amount))

            rng.shuffle(entries)
            days = sorted(rng.sample(range(0, 30), min(len(entries), 30)))
            while len(days) < len(entries):
                days.append(rng.randint(0, 29))
            days.sort()

            for (description, category, amount), day_offset in zip(entries, days):
                txn_id += 1
                t = Transaction()
                t.transaction_id = txn_id
                t.application_id = doc.application_id
                t.document_id = doc.document_id
                t.account_last4 = account
                t.posted_date = month_start + dt.timedelta(days=day_offset)
                t.description = decorate_description(rng, description)
                t.amount = amount
                balance += amount
                t.running_balance = round(balance, 2)
                t.category, t.category_source = assign_category(rng, category)
                t.created_at = doc.uploaded_at + dt.timedelta(
                    seconds=rng.uniform(60, 1200))
                rows.append(t)

    # The canonical statement, exactly as CANON.md prints it.
    canon_balance = 61204.55
    for day, description, amount, true_category in CANON_STATEMENT:
        txn_id += 1
        t = Transaction()
        t.transaction_id = txn_id
        t.application_id = canon_doc.application_id
        t.document_id = canon_doc.document_id
        t.account_last4 = "1221"
        month, day_number = day.split("-")
        t.posted_date = dt.date(2025, int(month), int(day_number))
        t.description = description
        t.amount = amount
        canon_balance += amount
        t.running_balance = round(canon_balance, 2)
        # The rules engine labelled all three of these as plain deposits. That
        # is the whole problem in Mission 20.
        t.category = {
            "CARD_SETTLEMENT": "CARD_SETTLEMENT",
            "INTERNAL_TRANSFER": "ACH_CREDIT",
            "LOAN_PROCEEDS": "ACH_CREDIT",
        }[true_category]
        t.category_source = "OPTISCAN_RULES"
        t.created_at = canon_doc.uploaded_at + dt.timedelta(minutes=4)
        rows.append(t)
    return rows


def decorate_description(rng, description):
    roll = rng.random()
    if roll < 0.22:
        return "%s %s" % (description, "%08d" % rng.randint(0, 99999999))
    if roll < 0.32:
        return "%s ****%04d" % (description, rng.randint(0, 9999))
    if roll < 0.38:
        return description.lower()
    if roll < 0.44:
        return description + "   "
    return description


def assign_category(rng, true_category):
    """
    category is nullable and category_source arrived in V12. The rules engine
    labels internal transfers and loan proceeds as ordinary credits most of the
    time, which is why nobody noticed the revenue function was wrong.
    """
    if rng.random() < 0.38:
        return None, None
    source = pick_weighted(rng, [("OPTISCAN_RULES", 0.72), ("MANUAL", 0.16),
                                 ("AI_SERVICE", 0.12)])
    if source == "MANUAL":
        return true_category, source
    if true_category == "INTERNAL_TRANSFER" and rng.random() < 0.79:
        return "ACH_CREDIT", source
    if true_category == "LOAN_PROCEEDS" and rng.random() < 0.84:
        return "ACH_CREDIT", source
    return true_category, source


class Decision:
    pass


def build_decisions(rng, apps, transactions_by_app):
    rows = []
    decision_id = 0
    for app in apps:
        if app.decided_event_at is None:
            continue
        decision_id += 1
        d = Decision()
        d.decision_id = decision_id
        d.application_id = app.application_id
        d.outcome = "DECLINED" if app.decline else (
            "COUNTER_OFFER" if rng.random() < 0.11 else "APPROVED")
        if d.outcome == "DECLINED":
            d.approved_amount = None
            codes = rng.sample(DECLINE_CODES, rng.randint(1, 4))
        else:
            factor = rng.choice([1.0, 1.0, 0.85, 0.7, 0.5])
            d.approved_amount = round(app.amount_requested * factor, 2)
            codes = rng.sample(APPROVE_CODES, rng.randint(1, 3))

        # reason_codes is a comma separated string. Sometimes with spaces,
        # sometimes not, sometimes with a trailing comma. Defect D-04.
        joiner = rng.choice([",", ", ", ",", ","])
        d.reason_codes = joiner.join(codes)
        if rng.random() < 0.06:
            d.reason_codes += ","
        if rng.random() < 0.03:
            d.reason_codes = None

        d.rate_apr = round(rng.uniform(7.25, 28.9), 3) if d.approved_amount else None
        d.term_months = rng.choice([12, 24, 36, 48, 60, 84]) if d.approved_amount else None
        d.decided_by = app.underwriter
        d.policy_version = rng.choice(
            ["credit-policy-2025", "credit-policy-2025", "credit-policy-2024",
             "credit-policy-FINAL2", "credit-policy-2025"])

        # The revenue number the decision was made on. It is the naive sum of
        # every credit divided by the month count, so on any statement with a
        # transfer or a competitor loan in it, this is too high.
        credits = [t.amount for t in transactions_by_app.get(app.application_id, [])
                   if t.amount > 0]
        months = 3 if len(credits) > 14 else 1
        d.monthly_revenue_used = (
            round(sum(credits) / months, 2) if credits else
            round(rng.uniform(9000, 210000), 2))
        d.dscr = round(rng.uniform(0.7, 3.4), 3)
        d.decided_at = app.decided_event_at
        d.created_at = app.decided_event_at + dt.timedelta(
            seconds=rng.uniform(1, 30))
        rows.append(d)
    return rows


SENTINEL_REASONS = [
    "IDENTITY_MISMATCH", "DEVICE_REPUTATION", "VELOCITY_APPLICANT",
    "BANK_ACCOUNT_AGE", "SYNTHETIC_ID_PATTERN", "ADDRESS_MISMATCH",
    "PHONE_CARRIER_RISK", "EMAIL_AGE_LOW", "IP_PROXY",
]


class FraudSignal:
    pass


def build_fraud_signals(rng, apps):
    rows = []
    signal_id = 0
    for app in apps:
        if app.is_draft or rng.random() > 0.78:
            continue
        signal_id += 1
        s = FraudSignal()
        s.signal_id = signal_id
        s.application_id = app.application_id
        s.vendor = "SENTINEL"
        s.score = int(min(999, max(1, rng.gauss(320, 190))))
        s.band = "LOW" if s.score < 350 else ("MEDIUM" if s.score < 650 else "HIGH")
        # Sentinel drops reason codes on about 9 percent of responses. The
        # fraud service stores what it got. Defect D-17.
        if rng.random() < 0.09:
            s.reason_codes = None
        else:
            s.reason_codes = ",".join(
                rng.sample(SENTINEL_REASONS, rng.randint(1, 4)))
        s.vendor_latency_ms = int(lognorm(rng, 480, 1.1))
        s.received_at = app.submit_ts + dt.timedelta(minutes=rng.uniform(2, 300))
        s.raw_response = json.dumps({
            "requestId": "sen-%08x" % (app.application_id * 2654435761 % 0xFFFFFFFF),
            "score": s.score,
            "band": s.band,
            "reasonCodes": (s.reason_codes.split(",") if s.reason_codes else None),
            "modelVersion": rng.choice(["sr-4.2", "sr-4.2", "sr-4.1"]),
        }, separators=(",", ":"))
        rows.append(s)
    return rows


# --------------------------------------------------------------------------
# Step 6: measurement. This mirrors seed/verify.sql line for line.
# --------------------------------------------------------------------------

def measure(apps, events):
    by_app = {}
    for e in events:
        by_app.setdefault(e.application_id, []).append(e)
    for rows in by_app.values():
        rows.sort(key=lambda e: e.occurred_at)

    submitted_events = [e for e in events if e.event_type == "SUBMITTED"]
    first = min(e.occurred_at for e in submitted_events)
    last = max(e.occurred_at for e in submitted_events)
    span_days = (last - first).total_seconds() / 86400.0
    monthly_rate = len(submitted_events) / span_days * DAYS_PER_MONTH

    cycles = []
    for app_id, rows in by_app.items():
        submitted = next((e for e in rows if e.event_type == "SUBMITTED"), None)
        decided = next((e for e in rows if e.event_type == "DECISIONED"), None)
        if submitted and decided:
            cycles.append(
                (decided.occurred_at - submitted.occurred_at).total_seconds() / 86400.0)

    doc_waits = []
    for rows in by_app.values():
        requested = next((e for e in rows if e.event_type == "DOCS_REQUESTED"), None)
        received = next((e for e in rows if e.event_type == "DOCS_RECEIVED"), None)
        if requested and received:
            doc_waits.append(
                (received.occurred_at - requested.occurred_at).total_seconds() / 86400.0)

    hands_on = []
    for rows in by_app.values():
        total = 0.0
        found = False
        for index, e in enumerate(rows):
            if e.event_type != "REVIEW_OPENED":
                continue
            following = rows[index + 1] if index + 1 < len(rows) else None
            if following is not None and following.event_type == "REVIEW_CLOSED":
                total += (following.occurred_at - e.occurred_at).total_seconds() / 60.0
                found = True
        if found:
            hands_on.append(total)

    rework_apps = len({e.application_id for e in events
                       if e.event_type == "PENDING_INFO"})
    submitted_apps = len({e.application_id for e in submitted_events})

    rework_costs = []
    for rows in by_app.values():
        for index, e in enumerate(rows):
            if e.event_type != "PENDING_INFO":
                continue
            following = next((f for f in rows[index + 1:]
                              if f.event_type == "IN_REVIEW"), None)
            if following is not None:
                rework_costs.append(
                    (following.occurred_at - e.occurred_at).total_seconds() / 86400.0)

    underwriting_only = []
    for rows in by_app.values():
        review = next((e for e in rows if e.event_type == "IN_REVIEW"), None)
        decided = next((e for e in rows if e.event_type == "DECISIONED"), None)
        if review and decided:
            underwriting_only.append(
                (decided.occurred_at - review.occurred_at).total_seconds() / 86400.0)

    naive = []
    for app in apps:
        if app.is_draft or app.submitted_at is None or app.decided_at is None:
            continue
        naive.append((app.decided_at - app.submitted_at).total_seconds() / 86400.0)

    gaps = []
    for app in apps:
        if app.is_draft or app.submitted_at is None:
            continue
        gaps.append(abs((app.submit_ts - app.submitted_at).total_seconds() / 60.0))

    return {
        "applications": len(apps),
        "submitted": submitted_apps,
        "events": len(events),
        "monthly_rate": monthly_rate,
        "window_span_days": span_days,
        "median_cycle_days": median_of(cycles),
        "decisioned": len(cycles),
        "median_hands_on_minutes": median_of(hands_on),
        "median_doc_wait_days": median_of(doc_waits),
        "rework_share_pct": 100.0 * rework_apps / submitted_apps,
        "median_rework_days": median_of(rework_costs),
        "rework_loops": len(rework_costs),
        "median_underwriting_only_days": median_of(underwriting_only),
        "median_naive_cycle_days": median_of(naive),
        "naive_rows": len(naive),
        "median_submitted_at_gap_minutes": median_of(gaps),
    }


CHECKS = [
    ("median_cycle_days", TARGET_CYCLE_DAYS, 0.05),
    ("median_hands_on_minutes", TARGET_HANDS_ON_MINUTES, 0.05),
    ("median_doc_wait_days", TARGET_DOC_WAIT_DAYS, 0.05),
    ("median_rework_days", TARGET_REWORK_DAYS, 0.05),
    ("rework_share_pct", TARGET_REWORK_SHARE, 0.05),
    ("monthly_rate", float(TARGET_MONTHLY_RATE), 2.0),
]


def print_report(numbers):
    print("")
    print("Northstar seed, measured from application_events")
    print("-" * 62)
    rows = [
        ("applications", "%d" % numbers["applications"], "1200"),
        ("submitted applications", "%d" % numbers["submitted"], "1176"),
        ("events", "%d" % numbers["events"], ""),
        ("window span, days", "%.3f" % numbers["window_span_days"], ""),
        ("applications per month", "%.1f" % numbers["monthly_rate"], "1840"),
        ("median cycle time, days", "%.2f" % numbers["median_cycle_days"], "9.4"),
        ("  decisioned applications", "%d" % numbers["decisioned"], ""),
        ("median hands-on, minutes", "%.2f" % numbers["median_hands_on_minutes"], "41"),
        ("median document wait, days", "%.2f" % numbers["median_doc_wait_days"], "5.1"),
        ("rework share, percent", "%.2f" % numbers["rework_share_pct"], "63"),
        ("median rework cost, days", "%.2f" % numbers["median_rework_days"], "2.8"),
        ("  rework loops measured", "%d" % numbers["rework_loops"], ""),
    ]
    for label, value, target in rows:
        print("  %-30s %12s   %s" % (label, value, target))
    print("")
    print("  Numbers the wrong query produces")
    print("  %-30s %12.2f" % ("time in underwriting, days",
                              numbers["median_underwriting_only_days"]))
    print("  %-30s %12.2f" % ("cycle from submitted_at, days",
                              numbers["median_naive_cycle_days"]))
    print("  %-30s %12d" % ("rows that query can use",
                            numbers["naive_rows"]))
    print("  %-30s %12.2f" % ("submitted_at gap, minutes",
                              numbers["median_submitted_at_gap_minutes"]))
    print("")


# --------------------------------------------------------------------------
# Step 7: CSV output
# --------------------------------------------------------------------------

def write_csv(name, header, rows):
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle, quoting=csv.QUOTE_MINIMAL,
                            lineterminator="\n")
        writer.writerow(header)
        for row in rows:
            writer.writerow(["" if v is None else v for v in row])
    return path


POLICY_DOCUMENTS = [
    # file_name, title, kind, tenant, product, version, effective_from, by, uploaded
    ("credit-policy-2024.pdf", "Northstar Credit Policy 2024", "BASE", None,
     None, "2024.1", "2024-01-01", "doug.feinberg", "2024-01-04 09:12:00"),
    ("credit-policy-2025.pdf", "Northstar Credit Policy 2025", "BASE", None,
     None, "2025.1", "2025-01-01", "doug.feinberg", "2025-01-06 08:44:00"),
    ("credit-policy-FINAL.pdf", "Credit Policy FINAL", "BASE", None, None,
     "draft", None, "m.webb", "2023-11-02 17:31:00"),
    ("credit-policy-FINAL2.pdf", "Credit Policy FINAL2", "BASE", None, None,
     "2025.2", None, "m.webb", "2025-07-19 21:02:00"),
    ("credit-policy-2026.pdf", "Northstar Credit Policy 2026", "BASE", None,
     None, "2026.1", "2026-03-01", "doug.feinberg", "2026-01-22 10:05:00"),
    ("California-overlay.pdf", "California Lending Overlay",
     "TENANT_OVERLAY", "CASCADE", None, "2025.1", "2025-04-01",
     "doug.feinberg", "2025-03-28 15:19:00"),
    ("SBA-overlay.pdf", "SBA 7(a) Program Overlay", "PRODUCT_OVERLAY", None,
     "SBA_7A", "2025.3", None, "renee.blackwell", "2025-09-11 11:47:00"),
    ("grants-program-addendum.docx", "State Grants Program Addendum",
     "ADDENDUM", None, None, "1.0", None, "b.tran", "2022-06-14 13:26:00"),
]


def write_all(applicants, apps, events, documents, extractions, transactions,
              decisions, fraud_signals):
    os.makedirs(OUT_DIR, exist_ok=True)

    write_csv("applicants.csv",
              ["applicant_id", "legal_name", "dba_name", "ein",
               "owner_ssn_last4", "email", "phone", "tenant_id", "created_at",
               "mailing_city", "mailing_state", "mailing_zip"],
              [[a.applicant_id, a.legal_name, a.dba_name, a.ein,
                a.owner_ssn_last4, a.email, a.phone, a.tenant_id,
                et(a.created_at), a.mailing_city, a.mailing_state,
                a.mailing_zip] for a in applicants])

    write_csv("applications.csv",
              ["application_id", "applicant_id", "product", "amount_requested",
               "status", "submitted_at", "decided_at", "customer_id",
               "created_at", "updated_at"],
              [[a.application_id, a.applicant_id, a.product,
                money(a.amount_requested), a.status,
                et(a.submitted_at) if a.submitted_at else None,
                et(a.decided_at) if a.decided_at else None,
                a.customer_id, et(a.created_at), et(a.updated_at)]
               for a in apps])

    write_csv("application_events.csv",
              ["event_id", "application_id", "event_type", "from_status",
               "to_status", "actor_type", "actor_id", "occurred_at",
               "recorded_at", "detail"],
              [[index + 1, e.application_id, e.event_type, e.from_status,
                e.to_status, e.actor_type, e.actor_id, et(e.occurred_at),
                et(e.recorded_at), e.detail]
               for index, e in enumerate(events)])

    write_csv("documents.csv",
              ["document_id", "application_id", "doc_type", "file_name",
               "mime_type", "size_bytes", "storage_key", "source",
               "page_count", "uploaded_by", "uploaded_at", "status", "sha256",
               "ocr_quality"],
              [[d.document_id, d.application_id, d.doc_type, d.file_name,
                d.mime_type, d.size_bytes, d.storage_key, d.source,
                d.page_count, d.uploaded_by, et(d.uploaded_at), d.status,
                d.sha256, d.ocr_quality] for d in documents])

    write_csv("document_extractions.csv",
              ["extraction_id", "document_id", "extractor",
               "extractor_version", "field_name", "field_value", "confidence",
               "is_correct", "raw_response", "extracted_at"],
              [[e.extraction_id, e.document_id, e.extractor,
                e.extractor_version, e.field_name, e.field_value,
                e.confidence,
                ("true" if e.is_correct else "false") if e.is_correct is not None else None,
                e.raw_response, et(e.extracted_at)] for e in extractions])

    write_csv("bank_transactions.csv",
              ["transaction_id", "application_id", "document_id",
               "account_last4", "posted_date", "description", "amount",
               "running_balance", "category", "category_source", "created_at"],
              [[t.transaction_id, t.application_id, t.document_id,
                t.account_last4, t.posted_date.isoformat(), t.description,
                money(t.amount), money(t.running_balance), t.category,
                t.category_source, et(t.created_at)] for t in transactions])

    write_csv("decisions.csv",
              ["decision_id", "application_id", "outcome", "approved_amount",
               "rate_apr", "term_months", "reason_codes", "decided_by",
               "policy_version", "monthly_revenue_used", "dscr", "decided_at",
               "created_at"],
              [[d.decision_id, d.application_id, d.outcome,
                money(d.approved_amount) if d.approved_amount else None,
                d.rate_apr, d.term_months, d.reason_codes, d.decided_by,
                d.policy_version, money(d.monthly_revenue_used), d.dscr,
                et(d.decided_at), et(d.created_at)] for d in decisions])

    write_csv("fraud_signals.csv",
              ["signal_id", "application_id", "vendor", "score", "band",
               "reason_codes", "raw_response", "vendor_latency_ms",
               "received_at"],
              [[s.signal_id, s.application_id, s.vendor, s.score, s.band,
                s.reason_codes, s.raw_response, s.vendor_latency_ms,
                et(s.received_at)] for s in fraud_signals])

    write_csv("policy_documents.csv",
              ["policy_document_id", "file_name", "title", "doc_kind",
               "tenant_id", "product", "version_label", "storage_key",
               "uploaded_by", "uploaded_at", "effective_from"],
              [[index + 1, row[0], row[1], row[2], row[3], row[4], row[5],
                "northstar-policies/" + row[0], row[7], row[8], row[6]]
               for index, row in enumerate(POLICY_DOCUMENTS)])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="fail if any canon number is off")
    parser.add_argument("--report", action="store_true",
                        help="measure only, write nothing")
    args = parser.parse_args()

    rng = random.Random(RANDOM_SEED)
    apps = build_apps(rng)
    tenant_by_application = [a.tenant_id for a in apps]
    applicant_rng = random.Random(RANDOM_SEED + 1)
    applicants = build_applicants(applicant_rng, tenant_by_application)
    applicants_by_id = {a.applicant_id: a for a in applicants}
    for app in apps:
        app.tenant_id = applicants_by_id[app.applicant_id].tenant_id

    scale = calibrate(apps)
    stamp_rng = random.Random(RANDOM_SEED + 9)
    assign_submitted_at_offsets(stamp_rng, apps)
    event_rng = random.Random(RANDOM_SEED + 2)
    events = build_events(event_rng, apps)
    events.sort(key=lambda e: (e.occurred_at, e.application_id))

    mismatch_rng = random.Random(RANDOM_SEED + 3)
    mismatched = plant_tenant_mismatches(mismatch_rng, apps)

    numbers = measure(apps, events)
    print_report(numbers)
    print("  calibration scale: %.6f" % scale)
    print("  cross tenant customer_id rows: %s" % mismatched[:4])

    failures = []
    for key, target, tolerance in CHECKS:
        if abs(numbers[key] - target) > tolerance:
            failures.append("%s is %.4f, wanted %.4f" % (key, numbers[key], target))

    if args.report:
        return 1 if (args.check and failures) else 0

    apps_by_id = {a.application_id: a for a in apps}
    doc_rng = random.Random(RANDOM_SEED + 4)
    documents, canon_doc = build_documents(doc_rng, apps, applicants_by_id)
    extraction_rng = random.Random(RANDOM_SEED + 5)
    extractions = build_extractions(extraction_rng, documents, applicants_by_id,
                                    apps_by_id)
    txn_rng = random.Random(RANDOM_SEED + 6)
    transactions = build_transactions(txn_rng, documents, apps_by_id, canon_doc)
    transactions_by_app = {}
    for t in transactions:
        transactions_by_app.setdefault(t.application_id, []).append(t)
    decision_rng = random.Random(RANDOM_SEED + 7)
    decisions = build_decisions(decision_rng, apps, transactions_by_app)
    fraud_rng = random.Random(RANDOM_SEED + 8)
    fraud_signals = build_fraud_signals(fraud_rng, apps)

    write_all(applicants, apps, events, documents, extractions, transactions,
              decisions, fraud_signals)

    print("  rows written")
    print("    applicants           %6d" % len(applicants))
    print("    applications         %6d" % len(apps))
    print("    application_events   %6d" % len(events))
    print("    documents            %6d" % len(documents))
    print("    document_extractions %6d" % len(extractions))
    print("    bank_transactions    %6d" % len(transactions))
    print("    decisions            %6d" % len(decisions))
    print("    fraud_signals        %6d" % len(fraud_signals))
    print("    policy_documents     %6d" % len(POLICY_DOCUMENTS))
    print("")
    print("  canon bank statement on application_id %d, document_id %d"
          % (CANON_STATEMENT_APPLICATION_ID, canon_doc.document_id))
    print("  Corner Rise Bakery applicant_ids %s" % CORNER_RISE_APPLICANT_IDS)
    print("")

    if failures:
        for line in failures:
            print("  FAIL: " + line)
        return 1
    print("  all canon numbers match")
    return 0


if __name__ == "__main__":
    sys.exit(main())
