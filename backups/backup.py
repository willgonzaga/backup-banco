import os
from dotenv import load_dotenv
import json
import subprocess
from datetime import datetime, timedelta
import psycopg
import requests

load_dotenv("/app/.env")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

with open(CONFIG_PATH) as f:
    config = json.load(f)

BACKUP_DIR = os.path.join(BASE_DIR, config["backup_dir"])
os.makedirs(BACKUP_DIR, exist_ok=True)

DUMP_ROOT = BACKUP_DIR
MAX_AGE_DAYS = 7
now = datetime.now()

def sendWebhookBackupNotification(banco):
    webhook_url = os.getenv("WEBHOOK_DISCORD_URL")
    if not webhook_url:
        print("⚠️ WEBHOOK_URL não configurado.")
        return

    payload = {
        "content": f"Erro ao gerar backup do banco de dados do cliente: {banco}",
    }

    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204:
            print("✅ Notificação enviada com sucesso.")
        else:
            print(f"❌ Erro ao enviar notificação: {response.status_code}")
    except Exception as e:
        print(f"Erro ao enviar notificação: {e}")


def SendWebhookErrorConectionNotification(error):
    webhook_url = os.getenv("WEBHOOK_DISCORD_URL")
    if not webhook_url:
        print("⚠️ WEBHOOK_URL não configurado.")
        return

    payload = {
        "content": f"Erro ao conectar ao banco de dados: {error}",
    }

    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204:
            print("✅ Notificação de erro enviada com sucesso.")
        else:
            print(f"❌ Erro ao enviar notificação: {response.status_code}")
    except Exception as e:
        print(f"Erro ao enviar notificação: {e}")


print("🔍 Verificando arquivos antigos para exclusão com base no nome...")

for db_folder in os.listdir(DUMP_ROOT):
    db_path = os.path.join(DUMP_ROOT, db_folder)
    if not os.path.isdir(db_path):
        continue

    for filename in os.listdir(db_path):
        file_path = os.path.join(db_path, filename)
        if not os.path.isfile(file_path):
            continue

        try:
            date_part = filename.rsplit("_", 1)[-1].replace(".dump", "")
            file_date = datetime.strptime(date_part, "%d-%m-%Y")
            file_age = now - file_date

            if file_age > timedelta(days=MAX_AGE_DAYS):
                os.remove(file_path)
                print(f"🗑️  Removido: {file_path} (idade: {file_age.days} dias)")
        except Exception as e:
            print(f"⚠️  Ignorando arquivo inválido '{filename}': {e}")

timestamp = datetime.now().strftime("%d-%m-%Y")

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "dbname": os.getenv("POSTGRES_DB")
}

try:
    print("Conectando ao PostgreSQL...")
    conn_str = (
        f"host={DB_CONFIG['host']} "
        f"port={DB_CONFIG['port']} "
        f"user={DB_CONFIG['user']} "
        f"password={DB_CONFIG['password']} "
        f"dbname={DB_CONFIG['dbname']}"
    )

    with psycopg.connect(conn_str, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT datname FROM pg_database
                WHERE datistemplate = false AND datname NOT IN ('postgres')
            """)
            databases = [row[0] for row in cur.fetchall()]

    for db_name in databases:
        db_dir = os.path.join(BACKUP_DIR, db_name)
        os.makedirs(db_dir, exist_ok=True)

        filename = f"{db_name}_{timestamp}.dump"
        filepath = os.path.join(db_dir, filename)

        print(f"🔄 Dump do banco: {db_name}")
        env = os.environ.copy()
        env["PGPASSWORD"] = DB_CONFIG["password"]

        result = subprocess.run([
            "/usr/bin/pg_dump",
            "-h", DB_CONFIG["host"],
            "-p", str(DB_CONFIG["port"]),
            "-U", DB_CONFIG["user"],
            "-F", "c",
            "-f", filepath,
            db_name
        ], env=env)

        if result.returncode == 0:
            print(f"✅ Backup gerado: {filepath}")
        else:
            print(f"❌ Erro ao gerar backup do banco: {db_name}")
            sendWebhookBackupNotification(db_name)
            
except Exception as e:
    print(f"Erro: {e}")
    SendWebhookErrorConectionNotification(e)