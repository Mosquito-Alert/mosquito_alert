import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path + "util_scripts/")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

### CODE STARTS HERE

from tigaserver_app.models import *
import pandas as pd

titles = {
	"en": "Inspire other users this November!",
	"es": "Inspira a otros usuarios este Noviembre!",
	"ca": "Inspira a altres usuaris aquest Novembre!",
}
titles['gl'] = titles['es']

translations = {
    "en": {
        "title": "Top contributors like you inspire us!",
        "line1": "You are one of the <strong>top 100 users</strong> with the most activity on our platform.",
        "line2": "This November, we’re hosting an <strong>Open Dialogue on citizen science</strong>, and we’d love for you to share your story in a short 5-min talk.",
        "line3": 'If you’re interested, please email <a href="mailto:elizabethkate.tyson@upf.edu?subject=Open%20Dialogue%20Lightning%20Talk">elizabethkate.tyson@upf.edu</a>.'
    },
    "es": {
        "title": "¡Los contribuidores como tú nos inspiran!",
        "line1": "Eres uno de los <strong>top 100 usuarios</strong> con más actividad en nuestra plataforma.",
        "line2": "Este noviembre organizamos un <strong>Diálogo Abierto sobre ciencia ciudadana</strong>, y nos encantaría que compartieras tu historia en una charla corta de 5 minutos.",
        "line3": 'Si estás interesado, por favor escribe a <a href="mailto:elizabethkate.tyson@upf.edu?subject=Open%20Dialogue%20Lightning%20Talk">elizabethkate.tyson@upf.edu</a>.'
    },
    "ca": {
        "title": "Els contribuïdors com tu ens inspiren!",
        "line1": "Ets un dels <strong>top 100 usuaris</strong> amb més activitat a la nostra plataforma.",
        "line2": "Aquest novembre organitzem un <strong>Diàleg Obert sobre ciència ciutadana</strong>, i ens encantaria que compartissis la teva història en una xerrada curta de 5 minuts.",
        "line3": 'Si hi estàs interessat, si us plau escriu a <a href="mailto:elizabethkate.tyson@upf.edu?subject=Open%20Dialogue%20Lightning%20Talk">elizabethkate.tyson@upf.edu</a>.'
    }
}
translations['gl'] = translations['es']

html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
</head>
<body>
<div>
    <h4>{title}</h4>
    <p>{line1}</p>
    <p>{line2}</p>
    <p>{line3}</p>
</div>
</body>
</html>
"""

def generate_email(language="en"):
    text = translations.get(language, translations["en"])  # fallback to English
    return html_template.format(**text)

df = pd.DataFrame(
	TigaUser.objects.annotate(
		last_report=models.Subquery(Report.objects.filter(user=models.OuterRef('pk')).order_by('-server_upload_time').values('server_upload_time')[:1]), 
		num_reports=models.Count('user_reports', filter=models.Q(user_reports__type='adult'))
	).filter(
		models.Q(num_reports__gte=100, locale__in=('ca', 'es', 'gl'))
		| models.Q(num_reports__gte=20, locale='en')
	).filter(last_report__year__gte=2023).values('pk','locale')
)

for locale in df.locale.unique():
    notification_content = NotificationContent.objects.create(
        title_en=titles.get("en"),
        body_html_en=generate_email(language="en"),
        title_es=titles.get("es"),
        body_html_es=generate_email(language="es"),
        title_ca=titles.get("ca"),
        body_html_ca=generate_email(language="ca"),
        title_native=titles.get(locale),
        body_html_native=generate_email(language=locale),
        native_locale=locale,
    )
    for user in TigaUser.objects.filter(pk__in=df[df['locale'] == locale]['pk']):
        notification = Notification.objects.create(
            user=user,
            notification_content=notification_content
        )
        notification.send_to_user(user=user)