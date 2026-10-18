#!/usr/bin/env python3
"""Build the PDF report from real screenshots and recorded browser checks."""
import json
from html import escape
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate,
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
styles.add(ParagraphStyle('BodyRu', fontName='Report', fontSize=9.3, leading=14.5, textColor=INK, spaceAfter=9))
styles.add(ParagraphStyle('SmallRu', parent=styles['BodyRu'], fontSize=8, leading=11.7, spaceAfter=5))
styles.add(ParagraphStyle('CellRu', parent=styles['BodyRu'], fontSize=7.4, leading=10.6, spaceAfter=0))
styles.add(ParagraphStyle('HeadRu', parent=styles['BodyRu'], fontName='Report-Bold', fontSize=19, leading=25, spaceAfter=13))
styles.add(ParagraphStyle('SubRu', parent=styles['BodyRu'], fontName='Report-Bold', fontSize=11, leading=16, spaceBefore=7, spaceAfter=9))
styles.add(ParagraphStyle('HeroRu', parent=styles['HeadRu'], fontSize=33, leading=40))
styles.add(ParagraphStyle('TagRu', parent=styles['SmallRu'], fontName='Report-Bold', textColor=ACCENT, spaceAfter=15))
styles.add(ParagraphStyle('CaptionRu', parent=styles['SmallRu'], alignment=TA_CENTER, textColor=MUTED))

def p(text, style='BodyRu'):
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

def table(rows, widths, heading=True, cell='CellRu'):
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
    PageTemplate(id='wide', frames=Frame(36, 46, landscape(A4)[0]-72, landscape(A4)[1]-88, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0), pagesize=landscape(A4), onPage=footer),
])

# A shorter report: seven pages, with only the required evidence.
doc.pagesize = landscape(A4)
doc.pageTemplates.reverse()
story = []
def newpage(template='portrait'):
    story.extend([NextPageTemplate(template), PageBreak()])
repository = META['repository']
repo_text = f'<link href="{escape(repository, quote=True)}" color="#6554C0">{literal(repository)}</link>' if repository else 'GitHub: ссылка пока не предоставлена.'
live_site = META['live_site']
site_text = f'<link href="{escape(live_site, quote=True)}" color="#6554C0">{literal(live_site)}</link>'

story += [p('Assignment 4. Forms and Validation', 'HeadRu'),
          p(f'{literal(META["student"])} · {literal(META["group"])} · {META["date"]}', 'BodyRu'),
          p('GitHub: ' + repo_text, 'SmallRu'),
          p('GitHub Pages: ' + site_text, 'SmallRu'),
          p('Task 1. Билет на поезд - 1280 px', 'SubRu')]
comparison = Table([[p('Образец из задания', 'CaptionRu'),p('Моя страница · 1280 px', 'CaptionRu')],
                    [pic('reference-desktop.png',365,290),pic('task1-1280.png',365,290)]],colWidths=[384,384])
comparison.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('ALIGN',(0,0),(-1,-1),'CENTER')]))
story += [comparison,Spacer(1,8),p('Для формы использованы Bootstrap grid, radio, select, input-group, switch и checkbox. Использована собственная сине-сиреневая палитра: #252C48, #6554C0, #F0EDF9 и #F6F5FA. Цвета и оформление отличаются от образца по выбранному варианту дизайна; Montserrat и компоненты Bootstrap сохранены. Для сравнения с рисунком выбраны One way, Coupé и 1 adult; маршрут введён вручную.', 'SmallRu')]

newpage()
story += [p('Task 1. Телефон - 375 px', 'HeadRu')]
comparison = Table([[p('Образец', 'CaptionRu'),p('Моя страница · 375 px','CaptionRu')],
                    [pic('reference-mobile.png',230,570),pic('task1-375.png',230,570)]],colWidths=[261,261])
comparison.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('ALIGN',(0,0),(-1,-1),'CENTER')]))
story += [comparison,Spacer(1,8),p('На телефоне поля идут друг под другом. flex-column-reverse ставит Find trains выше Clear, а flex-md-row возвращает кнопки в строку на компьютере.', 'SmallRu'),
          p('Обязательные поля помечены required. Passengers принимает 1-6 взрослых. Clear имеет type=reset и очищает форму, потому что начальные значения пустые. Каждое поле связано с label; Return необязателен.', 'SmallRu')]

newpage()
story += [p('Task 2. Регистрация на AITU Hack 2026', 'HeadRu'),
          p('Правила заданы HTML-атрибутами. Ошибки появляются через :user-invalid и .invalid-feedback после взаимодействия. При первом открытии красных сообщений нет.', 'SmallRu'),
          pic('task2-form.png',500,500),Spacer(1,8),p('Пример после ввода слишком короткого имени:', 'SmallRu')]
with PILImage.open(SHOTS / 'task2-errors-form.png') as im:
    im.crop((0,75,im.width,210)).save(SHOTS / 'task2-errors-detail.png')
story += [pic('task2-errors-detail.png',500,138)]

newpage('wide')
story += [p('Task 2. Результаты проверки', 'HeadRu')]
entries = [
 ('Full name', 'required; minlength=2; maxlength=40', 'Anna-Maria Lee', 'A'),
 ('University email', 'email; required', 'a.fedenko@astanait.edu.kz', 'a.fedenko; a.fedenko@'),
 ('Age', 'number; 16–30; step=1; required', '18', '15; 31'),
 ('Team size', 'number; 1–4; step=1; required', '4', '5; 2.5'),
 ('Track', 'select; required; пустой value у Choose…', 'Web', 'Choose…'),
 ('Arrival day', 'date; 2026-11-20…2026-11-22; required', '21.11.2026', '25.11.2026'),
 ('Check-in time', 'time; 09:00–18:00; step=1800; required', '10:30', '10:15; 19:00'),
 ('Entry fee', 'number; 0–5000; step=500; required', '1500', '1250; 6000'),
 ('Experience', 'radio; общий name; required', 'Beginner', 'ничего не выбрано'),
 ('GitHub profile', 'url; без required', 'пусто; https://github.com/yerassyl-dev', 'github.com/yerassyl-dev'),
 ('Password', 'password; 8–20 символов; required', 'Astana2026', 'short'),
 ('Motivation', 'textarea; 50–300 символов; required', '120 символов', '49 символов'),
 ('Rules agreement', 'checkbox; required', 'выбрано', 'не выбрано'),
]
rows = [['Поле','Правило','Принято','Отклонено','Результат']]
for entry in entries:
    rows.append([*(literal(t) for t in entry),'Совпало'])
story += [table(rows,[88,230,180,175,95]),Spacer(1,10),p('Все значения из задания дают ожидаемый результат. Дополнительно проверены границы и пустые обязательные поля. Всего 64 теста значений прошли успешно. step=1800 для времени означает 30 минут, а maxlength не даёт набрать лишние символы.', 'SmallRu')]

newpage()
story += [p('Task 3. Исправленная форма кафе', 'HeadRu'),
          p('Я сохранил все поля исходной формы. Добавил label, уникальные id, name и правильные типы ввода. Radio Inside и Terrace используют общий name. Вместо div используется настоящая кнопка submit.', 'BodyRu'),
          pic('task3-form.png',510,500),Spacer(1,14),
          p('Проверка', 'SubRu'),p('Форма работает с клавиатурой: Tab перемещает фокус, стрелки меняют вариант radio, пробел переключает согласие, Enter отправляет форму. На 375 и 1280 px нет горизонтальной прокрутки.', 'BodyRu'),
          p('Официальный W3C Validator не нашёл ошибок или предупреждений в task1.html, task2.html и task3.html. Учебный обработчик только подтверждает отправку; реальное бронирование не создаётся.', 'SmallRu')]

newpage('wide')
story += [p('Task 3. 10 проблем исходной формы', 'HeadRu'),
          p('Строки относятся к исходному фрагменту из PDF, сохранённому в report/original-task3.txt.', 'SmallRu')]
rows = [['№ / строки','Исходный фрагмент','Почему это проблема','Исправление']]
for i,item in enumerate(PROBLEMS,1):
    rows.append([f'{i}<br/>{literal(item["lines"])}',literal(item['original']),literal(item['problem']),literal(item['fix'])])
story += [table(rows,[55,260,230,223])]

newpage()
story += [p('Альтернативы и вывод', 'HeadRu')]
for item in PROBLEMS:
    if item.get('alternative'):
        story += [p('Строки '+literal(item['lines']), 'SubRu'),
                  p('<b>Другой способ.</b> '+literal(item['alternative'])),
                  p('<b>Почему выбран текущий.</b> '+literal(item['rationale']))]
story += [p('Вывод', 'SubRu'),p('В этой работе я разобрал, как строить форму с сеткой Bootstrap, проверять данные HTML-атрибутами и связывать поля с подписями. Основные правила находятся прямо в HTML, а CSS отвечает за оформление и показ ошибок.'),
          p('Проверки и запуск', 'SubRu'),p(f'Пройдены {len(RESULTS["checks"])} функциональных проверок и {len(RESULTS["task2_cases"])} проверок значений. JavaScript, pattern и novalidate на страницах отсутствуют. Открыть формы можно через index.html. Для демонстрации отправки: python3 scripts/serve.py, затем http://127.0.0.1:8000/.', 'SmallRu'),
          p('GitHub', 'SubRu'),p(repo_text, 'SmallRu'),
          p('GitHub Pages', 'SubRu'),p(site_text, 'SmallRu'),
          p('Источники', 'SubRu')]
for label,url in [
    ('Bootstrap: формы','https://getbootstrap.com/docs/5.3/forms/overview/'),
    ('MDN: :user-invalid','https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/:user-invalid'),
    ('MDN: input time','https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/time'),
    ('W3C Validator','https://validator.w3.org/nu/'),
]:
    story.append(p(f'<link href="{url}" color="#6554C0">{label}</link>', 'SmallRu'))
story += [p('Требования, образец первой формы и исходная форма кафе взяты из Assignment 4.pdf.', 'SmallRu')]
for name in ('index','task1','task2','task3'):
    data=json.loads((REPORT / f'{name}-w3c.json').read_text())
    if data.get('messages'): raise ValueError(f'Review validator output for {name}')
OUT.parent.mkdir(parents=True, exist_ok=True)
doc.build(story)
print(OUT)
