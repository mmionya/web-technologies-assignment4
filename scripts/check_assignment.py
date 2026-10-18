#!/usr/bin/env python3
"""Run browser checks and save report evidence (the delivered pages contain no JS).

Start scripts/serve.py first, then run this script using a Python environment with
Playwright installed. --chrome may point to another locally installed Chromium.
"""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "report"
SHOTS = REPORT / "screenshots"
results = {"checks": [], "task2_cases": [], "screenshots": []}


def check(name, passed, detail=None):
    item = {"name": name, "passed": bool(passed)}
    if detail is not None:
        item["detail"] = detail
    results["checks"].append(item)
    print(f"{'PASS' if passed else 'FAIL'}: {name}")


def screenshot(page, filename):
    page.evaluate("document.fonts.ready")
    page.screenshot(path=str(SHOTS / filename), full_page=True, animations="disabled")
    results["screenshots"].append(f"report/screenshots/{filename}")
    form_filename = {
        "task2-initial-1280.png": "task2-form.png",
        "task2-invalid-1280.png": "task2-errors-form.png",
        "task3-1280.png": "task3-form.png",
    }.get(filename)
    if form_filename:
        page.locator("form").screenshot(path=str(SHOTS / form_filename), animations="disabled")
        results["screenshots"].append(f"report/screenshots/{form_filename}")


def validity(locator):
    return locator.evaluate("""el => ({valid:el.validity.valid,
        flags:['valueMissing','typeMismatch','rangeUnderflow','rangeOverflow',
        'stepMismatch','tooShort','tooLong','badInput'].filter(k=>el.validity[k]),
        message:el.validationMessage})""")


def edit(locator, value):
    kind = locator.get_attribute("type") or ""
    tag = locator.evaluate("e=>e.tagName")
    if tag == "SELECT":
        locator.select_option(value)
    elif kind == "checkbox":
        locator.set_checked(bool(value))
    elif kind == "radio":
        if value:
            locator.check()
    elif kind in ("date", "time", "number"):
        locator.fill(str(value))
    else:
        locator.fill("")
        locator.press_sequentially(str(value))
    locator.press("Tab")


def common_checks(page, filename, base):
    page.goto(f"{base}/{filename}")
    check(f"{filename}: no script, inline event handlers, novalidate or pattern", page.evaluate("""() =>
        !document.querySelector('script,[novalidate],[formnovalidate],[pattern]') &&
        ![...document.querySelectorAll('*')].some(e=>[...e.attributes].some(a=>a.name.startsWith('on')))"""))
    missing = page.locator("input:not([type=hidden]),select,textarea").evaluate_all(
        "es=>es.filter(e=>!e.labels?.length).map(e=>e.id||e.name)")
    check(f"{filename}: every field has a connected label", not missing, missing)
    ids = page.locator("[id]").evaluate_all("es=>es.map(e=>e.id)")
    check(f"{filename}: IDs are unique", len(ids) == len(set(ids)))
    for width in (375, 1280):
        page.set_viewport_size({"width": width, "height": 900})
        overflow = page.evaluate("document.documentElement.scrollWidth > innerWidth")
        check(f"{filename}: no horizontal overflow at {width}px", not overflow)


def task1(page, base):
    page.goto(f"{base}/task1.html")
    required_ids = ["from", "to", "departure", "seat", "coupe", "sleeper", "phone", "email", "agreement"]
    check("Task 1: mandatory fields have required", all(page.locator(f"#{i}").get_attribute("required") is not None for i in required_ids))
    passenger_values = page.locator("#passengers option").evaluate_all("es=>es.map(e=>e.value)")
    check("Task 1: passengers options are empty or 1–6", passenger_values == ["", "1", "2", "3", "4", "5", "6"])
    buttons = page.locator("form button").evaluate_all("es=>es.map(e=>e.textContent.trim())")
    check("Task 1: HTML button order is Clear then Find trains", buttons == ["Clear", "Find trains"])
    for width in (375, 1280):
        page.set_viewport_size({"width": width, "height": 900})
        clear = page.get_by_role("button", name="Clear", exact=True).bounding_box()
        find = page.get_by_role("button", name="Find trains").bounding_box()
        correct = find["y"] < clear["y"] if width == 375 else clear["x"] < find["x"] and abs(clear["y"]-find["y"]) < 2
        check(f"Task 1: visual button order at {width}px", correct, {"clear": clear, "find": find})
        page.locator("#from").fill("Astana")
        page.locator("#to").fill("Almaty")
        page.locator('label[for="one-way"]').click()
        page.locator("#coupe").check()
        page.locator("#passengers").select_option("1")
        page.locator("h1").click()
        screenshot(page, f"task1-{width}.png")
    for field, value in {"departure": "2026-11-21", "return": "2026-11-22", "phone": "7012345678", "email": "test@example.com"}.items():
        page.locator(f"#{field}").fill(value)
    page.locator("#sms").check()
    page.locator("#agreement").check()
    check("Task 1: completed form is valid", page.locator("form").evaluate("f=>f.checkValidity()"))
    page.get_by_role("button", name="Clear", exact=True).click()
    remaining = page.locator("form input:not([type=hidden]),form select,form textarea").evaluate_all(
        "es=>es.filter(e=>['radio','checkbox'].includes(e.type)?e.checked:e.value!=='').map(e=>e.id)")
    check("Task 1: Clear empties all visible fields and choices", not remaining, remaining)
    check("Task 1: hidden country prefix remains +7", page.locator('[name="phone_country_code"]').input_value() == "+7")

    page.goto(f"{base}/task1.html")
    sequence = []
    reached = tab_until(page, "one-way")
    page.keyboard.press("Space")
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowLeft")
    sequence.append({"id": "one-way", "reached_by_tab": reached})
    for id_, value in (("from", "Astana"), ("to", "Almaty"), ("departure", "11212026"), ("return", "11222026")):
        reached = tab_until(page, id_)
        page.keyboard.type(value)
        sequence.append({"id": id_, "reached_by_tab": reached})
    reached = tab_until(page, "passengers")
    page.keyboard.press("ArrowDown")
    sequence.append({"id": "passengers", "reached_by_tab": reached})
    reached = tab_until(page, "seat")
    page.keyboard.press("Space")
    page.keyboard.press("ArrowRight")
    sequence.append({"id": "coupe", "reached_by_tab": reached})
    for id_, value in (("phone", "7012345678"), ("email", "test@example.com")):
        reached = tab_until(page, id_)
        page.keyboard.type(value)
        sequence.append({"id": id_, "reached_by_tab": reached})
    for id_ in ("sms", "agreement"):
        reached = tab_until(page, id_)
        page.keyboard.press("Space")
        sequence.append({"id": id_, "reached_by_tab": reached})
    check("Task 1: every field works with the keyboard only", all(s["reached_by_tab"] for s in sequence), sequence)
    check("Task 1: keyboard-completed form is valid", page.locator("form").evaluate("f=>f.checkValidity()") and page.locator("#departure").input_value() == "2026-11-21" and page.locator("#return").input_value() == "2026-11-22")
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    check("Task 1: Find trains is keyboard reachable after Clear", page.evaluate("document.activeElement.type==='submit'"))
    with page.expect_navigation():
        page.keyboard.press("Enter")
    check("Task 1: Enter submits valid form", page.url.endswith("/submit"))


def task2(page, base):
    url = f"{base}/task2.html"
    page.goto(url)
    page.set_viewport_size({"width": 1280, "height": 1000})
    visible = page.locator(".invalid-feedback:visible").count()
    check("Task 2: no feedback visible on initial load", visible == 0, visible)
    check("Task 2: no :user-invalid field on initial load", page.locator(":user-invalid").count() == 0)
    screenshot(page, "task2-initial-1280.png")
    page.set_viewport_size({"width": 375, "height": 900})
    screenshot(page, "task2-initial-375.png")

    # Every acceptance/rejection listed in the assignment, followed by boundaries.
    cases = [
        ("Full name", "full-name", "Anna-Maria Lee", True, "table"),
        ("Full name", "full-name", "A", False, "table"),
        ("University email", "university-email", "a.fedenko@astanait.edu.kz", True, "table"),
        ("University email", "university-email", "a.fedenko", False, "table"),
        ("University email", "university-email", "a.fedenko@", False, "table"),
        ("Age", "age", "18", True, "table"), ("Age", "age", "15", False, "table"), ("Age", "age", "31", False, "table"),
        ("Team size", "team-size", "4", True, "table"), ("Team size", "team-size", "5", False, "table"), ("Team size", "team-size", "2.5", False, "table"),
        ("Track", "track", "web", True, "table"), ("Track", "track", "", False, "table"),
        ("Arrival day", "arrival-day", "2026-11-21", True, "table"), ("Arrival day", "arrival-day", "2026-11-25", False, "table"),
        ("Check-in time", "check-in-time", "10:30", True, "table"), ("Check-in time", "check-in-time", "10:15", False, "table"), ("Check-in time", "check-in-time", "19:00", False, "table"),
        ("Entry fee", "entry-fee", "1500", True, "table"), ("Entry fee", "entry-fee", "1250", False, "table"), ("Entry fee", "entry-fee", "6000", False, "table"),
        ("Experience", "experience-beginner", True, True, "table"), ("Experience", "experience-beginner", False, False, "table"),
        ("GitHub profile", "github-profile", "", True, "table"), ("GitHub profile", "github-profile", "https://github.com/yerassyl-dev", True, "table"), ("GitHub profile", "github-profile", "github.com/yerassyl-dev", False, "table"),
        ("Password", "password", "Astana2026", True, "table"), ("Password", "password", "short", False, "table"),
        ("Motivation", "motivation", "A" * 120, True, "table"), ("Motivation", "motivation", "A" * 49, False, "table"),
        ("Rules agreement", "rules-agreement", True, True, "table"), ("Rules agreement", "rules-agreement", False, False, "table"),
        ("Full name", "full-name", "AB", True, "boundary"), ("Full name", "full-name", "A" * 40, True, "boundary"),
        ("Age", "age", "16", True, "boundary"), ("Age", "age", "30", True, "boundary"), ("Age", "age", "18.5", False, "boundary"),
        ("Team size", "team-size", "1", True, "boundary"), ("Team size", "team-size", "0", False, "boundary"),
        ("Arrival day", "arrival-day", "2026-11-20", True, "boundary"), ("Arrival day", "arrival-day", "2026-11-22", True, "boundary"), ("Arrival day", "arrival-day", "2026-11-19", False, "boundary"),
        ("Check-in time", "check-in-time", "09:00", True, "boundary"), ("Check-in time", "check-in-time", "18:00", True, "boundary"), ("Check-in time", "check-in-time", "08:30", False, "boundary"),
        ("Entry fee", "entry-fee", "0", True, "boundary"), ("Entry fee", "entry-fee", "5000", True, "boundary"), ("Entry fee", "entry-fee", "-500", False, "boundary"),
        ("Password", "password", "A" * 8, True, "boundary"), ("Password", "password", "A" * 20, True, "boundary"),
        ("Motivation", "motivation", "A" * 50, True, "boundary"), ("Motivation", "motivation", "A" * 300, True, "boundary"),
    ]
    required = ["full-name", "university-email", "age", "team-size", "track", "arrival-day", "check-in-time", "entry-fee", "experience-beginner", "password", "motivation", "rules-agreement"]
    for field in required:
        cases.append((field, field, False if field in ("experience-beginner", "rules-agreement") else "", False, "required"))
    for field, id_, value, expected, category in cases:
        page.goto(url)
        edit(page.locator(f"#{id_}"), value)
        actual = validity(page.locator(f"#{id_}"))
        display_value = f"{len(value)} characters" if id_ == "motivation" else value
        results["task2_cases"].append({"field": field, "id": id_, "value": display_value, "expected_valid": expected, "actual_valid": actual["valid"], "passed": actual["valid"] == expected, "category": category, "validity": actual})
    check("Task 2: every table, boundary and required case matches", all(c["passed"] for c in results["task2_cases"]), {"cases": len(cases), "failed": [c for c in results["task2_cases"] if not c["passed"]]})

    for id_, limit in (("full-name", 40), ("password", 20), ("motivation", 300)):
        page.goto(url)
        edit(page.locator(f"#{id_}"), "A" * (limit + 1))
        check(f"Task 2: typing cannot exceed {id_} maxlength={limit}", len(page.locator(f"#{id_}").input_value()) == limit)

    page.goto(url)
    edit(page.locator("#full-name"), "A")
    # Allow Bootstrap's border-color transition to reach its final color.
    page.wait_for_function("""() => {
        const c=getComputedStyle(document.querySelector('#full-name')).borderTopColor.match(/\\d+/g).map(Number);
        return c[0]>c[1]*1.5 && c[0]>c[2]*1.5;
    }""")
    check("Task 2: edited invalid name has visible text and red border", page.locator("#full-name-error").is_visible() and page.locator("#full-name").evaluate("""e=>{
        const c=getComputedStyle(e).borderTopColor.match(/\\d+/g).map(Number);
        return e.matches(':user-invalid') && c[0]>c[1]*1.5 && c[0]>c[2]*1.5;
    }"""))
    edit(page.locator("#age"), "15")
    page.locator("#check-in-time").fill("10:15")
    # Chrome's segmented time widget needs real key edits to mark user interaction.
    page.locator("#check-in-time").press("ArrowUp")
    page.locator("#check-in-time").press("ArrowDown")
    edit(page.locator("#entry-fee"), "1250")
    page.locator("h1").click()
    check("Task 2: edited invalid time shows feedback after blur", page.locator("#check-in-time").input_value() == "10:15" and page.locator("#check-in-time-error").is_visible())
    page.set_viewport_size({"width": 1280, "height": 1000})
    screenshot(page, "task2-invalid-1280.png")
    edit(page.locator("#full-name"), "Anna-Maria Lee")
    check("Task 2: error disappears after correcting name", not page.locator("#full-name-error").is_visible())

    page.goto(url)
    valid_values = {"full-name": "Anna-Maria Lee", "university-email": "a.fedenko@astanait.edu.kz", "age": "18", "team-size": "4", "track": "web", "arrival-day": "2026-11-21", "check-in-time": "10:30", "entry-fee": "1500", "experience-beginner": True, "github-profile": "https://github.com/yerassyl-dev", "password": "Astana2026", "motivation": "I want to build a useful web app, learn from other students and practise working in a team during the AITU Hack event.", "rules-agreement": True}
    for id_, value in valid_values.items():
        edit(page.locator(f"#{id_}"), value)
    check("Task 2: completed form is valid", page.locator("form").evaluate("f=>f.checkValidity()"))
    screenshot(page, "task2-valid-1280.png")
    page.get_by_role("button", name="Register").click()
    check("Task 2: valid form submits to local demo", page.url.endswith("/submit") and page.get_by_role("heading", name="Form submitted successfully").is_visible())
    check("Submission response never echoes sample password or email", "Astana2026" not in page.content() and "a.fedenko@" not in page.content())


def tab_until(page, target, maximum=30):
    for _ in range(maximum):
        page.keyboard.press("Tab")
        if page.evaluate("document.activeElement.id") == target:
            return True
    return False


def task3(page, base):
    page.goto(f"{base}/task3.html")
    for width in (1280, 375):
        page.set_viewport_size({"width": width, "height": 1000})
        screenshot(page, f"task3-{width}.png")
    page.set_viewport_size({"width": 1280, "height": 1000})
    page.reload()
    sequence = []
    values = {"guest-name": "Miras Zhumazhan", "guest-email": "test@example.com", "guest-phone": "+7 701 234 56 78", "guests": "2"}
    for id_, value in values.items():
        reached = tab_until(page, id_)
        sequence.append({"id": id_, "reached_by_tab": reached})
        page.keyboard.type(value)
    reached = tab_until(page, "reservation-date")
    # Chrome is explicitly launched in en-US, so the native date widget is MDY.
    page.keyboard.type("11212026")
    sequence.append({"id": "reservation-date", "reached_by_tab": reached, "value": page.locator("#reservation-date").input_value()})
    reached = tab_until(page, "meal")
    page.keyboard.press("ArrowDown")
    sequence.append({"id": "meal", "reached_by_tab": reached})
    reached = tab_until(page, "seating-inside")
    page.keyboard.press("Space")
    page.keyboard.press("ArrowRight")
    sequence.append({"id": "seating-terrace", "reached_by_tab": reached, "selected_with_arrow": page.locator("#seating-terrace").is_checked()})
    reached = tab_until(page, "comments")
    page.keyboard.type("A table near the window, please.")
    sequence.append({"id": "comments", "reached_by_tab": reached})
    reached = tab_until(page, "terms")
    page.keyboard.press("Space")
    sequence.append({"id": "terms", "reached_by_tab": reached})
    check("Task 3: every field is reachable and fillable using keyboard only", all(s["reached_by_tab"] for s in sequence), sequence)
    check("Task 3: seating radio arrows select exactly one option", page.locator('[name="seating"]:checked').count() == 1 and page.locator("#seating-terrace").is_checked())
    check("Task 3: keyboard-completed form is valid", page.locator("form").evaluate("f=>f.checkValidity()") and page.locator("#reservation-date").input_value() == "2026-11-21")
    form_data = page.locator("form").evaluate("f=>Object.fromEntries(new FormData(f))")
    expected_names = {"full_name", "email", "phone", "guests", "date", "seating", "meal", "comments", "terms"}
    check("Task 3: all nine original field groups are serialized", set(form_data) == expected_names, {"names": sorted(form_data), "seating": form_data.get("seating"), "meal": form_data.get("meal"), "date": form_data.get("date")})
    screenshot(page, "task3-keyboard-complete-1280.png")
    page.keyboard.press("Tab")
    button = page.evaluate("document.activeElement.tagName==='BUTTON' && document.activeElement.type==='submit'")
    check("Task 3: submit button follows fields in keyboard order", button)
    with page.expect_navigation():
        page.keyboard.press("Enter")
    check("Task 3: Enter submits valid form", page.url.endswith("/submit"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--chrome", default="/opt/google/chrome/chrome")
    args = parser.parse_args()
    SHOTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        # Context locale alone does not translate Chrome's native controls and
        # validation messages. Set the browser UI language independently of the host.
        browser = p.chromium.launch(
            executable_path=args.chrome,
            headless=True,
            args=["--no-sandbox", "--lang=en-US"],
            env={**os.environ, "LANG": "en_US.UTF-8", "LANGUAGE": "en_US:en", "LC_ALL": "en_US.UTF-8"},
        )
        results["browser"] = f"Chromium {browser.version}"
        results["locale"] = "en-US"
        results["tested_at_utc"] = datetime.now(timezone.utc).isoformat()
        page = browser.new_page(viewport={"width": 1280, "height": 1000}, locale="en-US")
        for name in ("task1.html", "task2.html", "task3.html"):
            common_checks(page, name, args.base_url)
        page.goto(f"{args.base_url}/index.html")
        screenshot(page, "index-1280.png")
        task1(page, args.base_url)
        task2(page, args.base_url)
        task3(page, args.base_url)
        browser.close()
    results["all_passed"] = all(c["passed"] for c in results["checks"]) and all(c["passed"] for c in results["task2_cases"])
    (REPORT / "browser-results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Evidence: {REPORT / 'browser-results.json'}")
    raise SystemExit(0 if results["all_passed"] else 1)


if __name__ == "__main__":
    main()
