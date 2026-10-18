#!/usr/bin/env python3
"""Build the PDF report from real screenshots and recorded browser checks."""
import json
from html import escape
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image,
    PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'report'
SHOTS = REPORT / 'screenshots'
OUT = ROOT / 'output/pdf/Assignment4_Zhumazhan_Miras.pdf'
META = json.loads((REPORT / 'metadata.json').read_text())
RESULTS = json.loads((REPORT / 'browser-results.json').read_text())
PROBLEMS = json.loads((REPORT / 'task3-problems.json').read_text())
if not RESULTS['all_passed']:
    raise SystemExit('Resolve browser test failures before producing the report.')

font_dir = Path('/usr/share/fonts/TTF')
if not (font_dir / 'DejaVuSans.ttf').exists():
    font_dir = Path('/usr/share/fonts/truetype/dejavu')
pdfmetrics.registerFont(TTFont('Report', str(font_dir / 'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('Report-Bold', str(font_dir / 'DejaVuSans-Bold.ttf')))
pdfmetrics.registerFontFamily('Report', normal='Report', bold='Report-Bold', italic='Report', boldItalic='Report-Bold')
ACCENT = colors.HexColor('#6554C0')
INK = colors.HexColor('#252C48')
MUTED = colors.HexColor('#697087')
PALE = colors.HexColor('#F0EDF9')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle('BodyEn', fontName='Report', fontSize=9.3, leading=14.5, textColor=INK, spaceAfter=9))
styles.add(ParagraphStyle('SmallEn', parent=styles['BodyEn'], fontSize=8, leading=11.7, spaceAfter=5))
styles.add(ParagraphStyle('CellEn', parent=styles['BodyEn'], fontSize=8.5, leading=12.5, spaceAfter=0))
styles.add(ParagraphStyle('HeadEn', parent=styles['BodyEn'], fontName='Report-Bold', fontSize=19, leading=25, spaceAfter=13))
styles.add(ParagraphStyle('SubEn', parent=styles['BodyEn'], fontName='Report-Bold', fontSize=11, leading=16, spaceBefore=7, spaceAfter=9))
styles.add(ParagraphStyle('HeroEn', parent=styles['HeadEn'], fontSize=33, leading=40))
styles.add(ParagraphStyle('TagEn', parent=styles['SmallEn'], fontName='Report-Bold', textColor=ACCENT, spaceAfter=15))
styles.add(ParagraphStyle('CaptionEn', parent=styles['SmallEn'], alignment=TA_CENTER, textColor=MUTED))

def p(text, style='BodyEn'):
    text = text.replace('\u2011', '-').replace('\u2013', '-').replace('\u2014', '-')
    return Paragraph(text, styles[style])

def literal(text):
    return escape(str(text)).replace('\n', '<br/>')

def pic(name, width, height):
    path = SHOTS / name
    with PILImage.open(path) as im:
        w, h = im.size
    scale = min(width / w, height / h)
    return Image(str(path), width=w * scale, height=h * scale)

def table(rows, widths, heading=True, cell='CellEn'):
    content = [[p(str(c), cell) for c in row] for row in rows]
    t = Table(content, colWidths=widths, repeatRows=1 if heading else 0, hAlign='LEFT')
    commands = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -1), .5, colors.HexColor('#D3DFD9')),
    ]
    if heading:
        commands += [('BACKGROUND', (0, 0), (-1, 0), PALE), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F7F9F8')])]
    t.setStyle(TableStyle(commands))
    return t

def footer(canvas, doc):
    w, h = canvas._pagesize
    canvas.setFillColor(ACCENT)
    canvas.rect(36, h - 25, 28, 3, fill=1, stroke=0)
    canvas.setStrokeColor(PALE)
    canvas.line(36, 34, w - 36, 34)
    canvas.setFont('Report', 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(36, 22, 'ASSIGNMENT 04  /  Zhumazhan Miras  /  IT-2512')
    canvas.drawRightString(w - 36, 22, str(doc.page))

doc = BaseDocTemplate(str(OUT), pagesize=A4, title='Assignment 4 - Zhumazhan Miras - IT-2512', author=META['student'], leftMargin=36, rightMargin=36, topMargin=42, bottomMargin=46)
doc.addPageTemplates([
    PageTemplate(id='portrait', frames=Frame(36, 46, A4[0]-72, A4[1]-88, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0), pagesize=A4, onPage=footer),
])

# Use portrait A4 throughout, with tables sized to the available text width.
story = []
def newpage():
    story.append(PageBreak())
repository = META['repository']
repo_text = f'<link href="{escape(repository, quote=True)}" color="#6554C0">{literal(repository)}</link>' if repository else 'GitHub URL has not been provided.'
live_site = META['live_site']
site_text = f'<link href="{escape(live_site, quote=True)}" color="#6554C0">{literal(live_site)}</link>'

story += [p('Assignment 4. Forms and Validation', 'HeadEn'),
          p(f'{literal(META["student"])} · {literal(META["group"])} · {META["date"]}', 'BodyEn'),
          p('GitHub: ' + repo_text, 'SmallEn'),
          p('GitHub Pages: ' + site_text, 'SmallEn'),
          p('Task 1. Train ticket booking - 1280 px', 'SubEn')]
comparison = Table([[p('Assignment reference', 'CaptionEn'),p('My page · 1280 px', 'CaptionEn')],
                    [pic('reference-desktop.png',249,290),pic('task1-1280.png',249,290)]],colWidths=[261,261])
comparison.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('ALIGN',(0,0),(-1,-1),'CENTER')]))
story += [comparison,Spacer(1,8),p('The form uses the Bootstrap grid, radio buttons, a select menu, an input group, a switch, and a checkbox. The custom navy and lavender palette uses #252C48, #6554C0, #F0EDF9, and #F6F5FA. The colors and layout differ from the reference by design; Montserrat and the Bootstrap components are retained. For comparison, One way, Coupé, and 1 adult are selected, and the route is entered manually.', 'SmallEn')]

newpage()
story += [p('Task 1. Mobile layout - 375 px', 'HeadEn')]
comparison = Table([[p('Assignment reference', 'CaptionEn'),p('My page · 375 px','CaptionEn')],
                    [pic('reference-mobile.png',230,570),pic('task1-375.png',230,570)]],colWidths=[261,261])
comparison.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('ALIGN',(0,0),(-1,-1),'CENTER')]))
story += [comparison,Spacer(1,8),p('On mobile, the fields are stacked vertically. flex-column-reverse places Find trains above Clear, while flex-md-row restores the horizontal button layout on desktop.', 'SmallEn'),
          p('Mandatory fields use required. Passengers allows 1-6 adults. Clear uses type=reset and empties the form because its initial values are empty. Every field has an associated label; Return is optional.', 'SmallEn')]

newpage()
story += [p('Task 2. AITU Hack 2026 registration', 'HeadEn'),
          p('All rules use HTML attributes. :user-invalid and .invalid-feedback display errors after interaction. No red error messages appear when the page first opens.', 'SmallEn'),
          pic('task2-form.png',500,500),Spacer(1,8),p('Example after entering a name that is too short:', 'SmallEn')]
with PILImage.open(SHOTS / 'task2-errors-form.png') as im:
    im.crop((0,75,im.width,210)).save(SHOTS / 'task2-errors-detail.png')
story += [pic('task2-errors-detail.png',500,138)]

newpage()
story += [p('Task 2. Validation results', 'HeadEn')]
entries = [
 ('Full name', 'required; minlength=2; maxlength=40', 'Anna-Maria Lee', 'A'),
 ('University email', 'email; required', 'a.fedenko@astanait.edu.kz', 'a.fedenko; a.fedenko@'),
 ('Age', 'number; 16–30; step=1; required', '18', '15; 31'),
 ('Team size', 'number; 1–4; step=1; required', '4', '5; 2.5'),
 ('Track', 'select; required; empty value for Choose…', 'Web', 'Choose…'),
 ('Arrival day', 'date; 2026-11-20…2026-11-22; required', '21 Nov 2026', '25 Nov 2026'),
 ('Check-in time', 'time; 09:00–18:00; step=1800; required', '10:30', '10:15; 19:00'),
 ('Entry fee', 'number; 0–5000; step=500; required', '1500', '1250; 6000'),
 ('Experience', 'radio; shared name; required', 'Beginner', 'nothing selected'),
 ('GitHub profile', 'url; optional', 'empty; https://github.com/yerassyl-dev', 'github.com/yerassyl-dev'),
 ('Password', 'password; 8–20 characters; required', 'Astana2026', 'short'),
 ('Motivation', 'textarea; 50–300 characters; required', '120 characters', '49 characters'),
 ('Rules agreement', 'checkbox; required', 'checked', 'unchecked'),
]
rows = [['Field','Rule','Accepted','Rejected','Result']]
for entry in entries:
    rows.append([*(literal(t) for t in entry),'Passed'])
story += [table(rows,[68,153,118,130,54]),Spacer(1,10),p('All values from the assignment produced the expected results. Boundary values and empty required fields were also tested. All 64 value tests passed. For time inputs, step=1800 means 30 minutes; maxlength prevents typing extra characters.', 'SmallEn')]

newpage()
story += [p('Task 3. Improved cafe reservation form', 'HeadEn'),
          p('I kept all fields from the original form and added labels, unique id values, name attributes, and appropriate input types. The Inside and Terrace radio buttons share a name. A real submit button replaces the div.', 'BodyEn'),
          pic('task3-form.png',510,500),Spacer(1,14),
          p('Verification', 'SubEn'),p('The form works with the keyboard: Tab moves focus, arrow keys select a radio option, Space toggles the agreement, and Enter submits the form. There is no horizontal scrolling at 375 or 1280 px.', 'BodyEn'),
          p('The official W3C Validator found no errors or warnings in task1.html, task2.html, or task3.html. The local demo handler only confirms submission; it does not create a real reservation.', 'SmallEn')]

newpage()
story += [p('Task 3. 10 problems in the original form', 'HeadEn'),
          p('Line numbers refer to the original snippet from the assignment PDF, saved in report/original-task3.txt.', 'SmallEn')]
rows = [['No. / lines','Original code or issue','Why it is a problem','Fix']]
for i,item in enumerate(PROBLEMS,1):
    rows.append([f'{i}<br/>{literal(item["lines"])}',literal(item['original']),literal(item['problem']),literal(item['fix'])])
story += [table(rows,[55,179,145,144])]

newpage()
story += [p('Alternatives and conclusion', 'HeadEn')]
for item in PROBLEMS:
    if item.get('alternative'):
        story += [p('Lines '+literal(item['lines']), 'SubEn'),
                  p('<b>Alternative.</b> '+literal(item['alternative'])),
                  p('<b>Why I chose this fix.</b> '+literal(item['rationale']))]
story += [p('Conclusion', 'SubEn'),p('In this assignment, I learned how to build forms with the Bootstrap grid, validate data using HTML attributes, and connect fields to labels. The validation rules are defined in HTML, while CSS controls the appearance and error feedback.'),
          p('Checks and setup', 'SubEn'),p(f'All {len(RESULTS["checks"])} functional checks and {len(RESULTS["task2_cases"])} value tests passed. The pages contain no JavaScript, pattern, or novalidate. Open index.html to view the forms. To demonstrate successful submission, run python3 scripts/serve.py and open http://127.0.0.1:8000/.', 'SmallEn'),
          p('GitHub', 'SubEn'),p(repo_text, 'SmallEn'),
          p('GitHub Pages', 'SubEn'),p(site_text, 'SmallEn'),
          p('Sources', 'SubEn')]
for label,url in [
    ('Bootstrap: Forms','https://getbootstrap.com/docs/5.3/forms/overview/'),
    ('MDN: :user-invalid','https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/:user-invalid'),
    ('MDN: input time','https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/time'),
    ('W3C Validator','https://validator.w3.org/nu/'),
]:
    story.append(p(f'<link href="{url}" color="#6554C0">{label}</link>', 'SmallEn'))
story += [p('The requirements, train form reference, and original cafe form come from Assignment 4.pdf.', 'SmallEn')]
for name in ('index','task1','task2','task3'):
    data=json.loads((REPORT / f'{name}-w3c.json').read_text())
    if data.get('messages'): raise ValueError(f'Review validator output for {name}')
OUT.parent.mkdir(parents=True, exist_ok=True)
doc.build(story)
print(OUT)
