# Assignment 4

**Zhumazhan Miras · IT-2512**

Three HTML and Bootstrap forms with a shared design: a light background, navy text, and lavender accents. No JavaScript is used.

## Live demo

[Open the website on GitHub Pages](https://mmionya.github.io/web-technologies-assignment4/).

The hosted preview supports navigation, form inputs, native HTML validation, and reset buttons. Successful form submission requires the local server described below: [GitHub Pages serves static files and does not run Python](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site), so it cannot process the forms' POST requests.

The site is published from the root of the `main` branch and updates automatically after each push. `.nojekyll` disables Jekyll processing.

## Project files

- `task1.html` — train ticket booking form.
- `task2.html` — hackathon registration form.
- `task3.html` — corrected cafe form.
- `style.css` — shared colors, styling for all three forms, responsive layouts, and validation feedback.
- `index.html` — links to the assignment tasks.

Bootstrap and the font are included in `assets/`, so the pages can be viewed offline.

## How to run

Open `index.html` in a browser. Form inputs, validation, and the Clear button work without installing any additional software.

To also demonstrate a successful form submission, run:

```bash
python3 scripts/serve.py
```

Then open http://127.0.0.1:8000/. The demo server displays a confirmation message. It does not store submitted data or create real bookings or registrations. The pages use only HTML and CSS.

## Key points for the assignment defense

1. `row` and `col-md-6` form a Bootstrap grid: two fields side by side on desktop and stacked vertically on mobile.
2. A label's `for` attribute matches the input's `id`. The `name` attribute identifies the value when the form is submitted.
3. `required` prevents empty values. `min` and `max` set limits, while `step` defines the allowed increments.
4. For time inputs, `step="1800"` means 30 minutes.
5. `minlength` and `maxlength` limit text length. The `email` and `url` input types validate the format.
6. Radio buttons with the same `name` allow one option to be selected. `fieldset` and `legend` group related controls and provide a group label.
7. `:user-invalid` displays validation feedback after the user interacts with a field. No errors are shown when the page first opens.
8. `type="reset"` restores the initial values. The first form starts empty, so Clear clears the form.
9. `flex-column-reverse flex-md-row` changes the button layout on mobile without changing the HTML order.

In this version, the color palette and the first form's design were changed at the user's request. They differ from the green and yellow reference in the assignment PDF.

The Return field in the first form is optional, as specified in the assignment. `type="tel"` does not validate the phone number format by itself. Email addresses are not restricted to a university domain: the assignment requires a valid email format.

## Report

`output/pdf/Assignment4_Zhumazhan_Miras.pdf` contains the report with screenshots and tables. Source code: [GitHub](https://github.com/mmionya/web-technologies-assignment4).

The `scripts/` and `report/` folders contain supporting tools and validation results. These files are not loaded by the web pages. Report metadata is stored in `report/metadata.json`.

## Sources

- [Bootstrap: Forms](https://getbootstrap.com/docs/5.3/forms/overview/)
- [MDN: :user-invalid](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/:user-invalid)
- [MDN: input time](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/time)
- [W3C Validator](https://validator.w3.org/nu/)

The reference designs come from Assignment 4.pdf. The Bootstrap and Montserrat licenses are included in `assets/`.
