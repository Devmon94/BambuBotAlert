Antes de nada, hace falta el interprete de python para que funcione:
    sudo apt update
    sudo apt install python3 python3-pip

Luego hay una serie de dependencias que utiliza la app, se instalan con:
    pip install -r requirements.txt
    playwright install

Renombra el fichero .env_example a .env con tus datos

La app a poder ser instalala en:
    /home/tu_usuario/bambu_alert_bot/

Si quieres ejecutarla cada hora por ejemplo hay que hacer un cron:
    crontab -e
    0 * * * * /usr/bin/python3 /home/tu_usuario/bambu_alert_bot/main.py >> /home/tu_usuario/bambu_alert_bot/log.txt 2>&1