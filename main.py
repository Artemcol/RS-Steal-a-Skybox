import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# === КОНФИГУРАЦИЯ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ===
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_OWNER = os.environ.get("REPO_OWNER")
REPO_NAME = os.environ.get("REPO_NAME")
ROBLOX_API_KEY = os.environ.get("ROBLOX_API_KEY")
PLACE_ID = os.environ.get("PLACE_ID", "7074744901")
UNIVERSE_ID = os.environ.get("UNIVERSE_ID", "2729496227")
SECURITY_PASSWORD = os.environ.get("SECURITY_PASSWORD", "SuperSecret123")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

ASSETS_DB_PATH = "assets_db.json"

# === УПРАВЛЕНИЕ БАЗОЙ ДАННЫХ ASSET ID ===
def load_assets_db():
    if os.path.exists(ASSETS_DB_PATH):
        try:
            with open(ASSETS_DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("️ Файл assets_db.json поврежден, создаем новый")
            return {}
    return {}

def save_assets_db(db):
    with open(ASSETS_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

# === РАБОТА С ROBLOX OPEN CLOUD API ===
def fetch_asset_ids_from_roblox():
    url = f"https://apis.roblox.com/cloud/v2/universes/{UNIVERSE_ID}/places/{PLACE_ID}/scripts"
    headers = {
        "x-api-key": ROBLOX_API_KEY,
        "Content-Type": "application/json"
    }
    
    all_scripts = []
    page_token = None
    
    while True:
        params = {"pageSize": 100}
        if page_token:
            params["pageToken"] = page_token
            
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка соединения с Roblox API: {e}")
            break
            
        if response.status_code != 200:
            print(f"❌ Ошибка API Roblox: {response.status_code} - {response.text}")
            break
            
        data = response.json()
        scripts = data.get("scripts", [])
        all_scripts.extend(scripts)
        
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    
    assets = {}
    for script in all_scripts:
        name = script.get("displayName", "").strip()
        asset_id = script.get("assetId", "").strip()
        if name and asset_id:
            clean_name = name.replace(".lua", "").replace(".rbxm", "").replace(".rbxl", "")
            assets[clean_name] = str(asset_id)
            
    print(f"✅ Найдено {len(assets)} скриптов в плейсе")
    return assets

def update_script_on_roblox(asset_id, new_content):
    url = f"https://apis.roblox.com/cloud/v2/assets/{asset_id}/content"
    headers = {
        "x-api-key": ROBLOX_API_KEY,
        "Content-Type": "text/plain"
    }
    
    try:
        response = requests.put(
            url, 
            headers=headers, 
            data=new_content.encode('utf-8'),
            timeout=15
        )
    except requests.exceptions.RequestException as e:
        print(f" Ошибка соединения при обновлении скрипта {asset_id}: {e}")
        return False
    
    if response.status_code == 200:
        print(f"✅ Скрипт {asset_id} успешно обновлен!")
        return True
    else:
        print(f"❌ Ошибка обновления скрипта {asset_id}: {response.status_code} - {response.text}")
        return False

# === ГЕНЕРАЦИЯ КОДА ЧЕРЕЗ OPENROUTER API ===
def generate_code_with_llm(task_description, folder, filename):
    prompt = f"""Ты эксперт по разработке игр в Roblox на языке Luau.
Напиши полный, рабочий и оптимизированный код для файла '{filename}' 
в папке '{folder}'. 

ЗАДАЧА: {task_description}

ТРЕБОВАНИЯ:
- Код должен быть безопасным и проверять входные данные
- Используй современные практики Roblox (task.spawn, attributes, tags)
- Не используй устаревшие функции (wait, deprecated APIs)
- Добавь комментарии на русском языке
- Верни ТОЛЬКО код, без пояснений, markdown-оберток или текста вне кода
- Если задача сложная, раздели логику на читаемые блоки
"""

    if not OPENROUTER_API_KEY:
        print("⚠️ OPENROUTER_API_KEY не найден! Возвращаю заглушку.")
        return f"-- Auto-generated code for {folder}/{filename}\n-- Task: {task_description}\n\nprint('[{filename}] Загружен успешно!')"

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/Arten/StealASkybox",
                "X-Title": "StealASkybox Generator"
            },
            json={
                "model": "meta-llama/llama-3.1-8b-instruct:free",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 4096
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            code = data["choices"][0]["message"]["content"].strip()
            code = code.replace("```lua", "").replace("```", "").strip()
            print(f"✅ Код сгенерирован через OpenRouter ({len(code)} символов)")
            return code
        else:
            print(f"❌ Ошибка OpenRouter API: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"️ Исключение при вызове OpenRouter: {e}")

    return f"-- [OPENROUTER ERROR] Fallback for {folder}/{filename}\n-- Task: {task_description}\n\nprint('[{filename}] Ошибка генерации!')"

# === ОСНОВНОЙ ЭНДПОИНТ ДЛЯ HTTP SHORTCUTS ===
@app.route("/generate", methods=["POST"])
def generate_code():
    data = request.json
    
    if not data or data.get("password") != SECURITY_PASSWORD:
        return jsonify({"error": "Неверный пароль"}), 403
    
    task_description = data.get("task", "")
    folder = data.get("folder", "ServerScriptService")
    filename = data.get("filename", "")
    
    if not task_description:
        return jsonify({"error": "Нет описания задачи"}), 400
    if not filename:
        return jsonify({"error": "Не указано имя файла"}), 400
    
    # 1. Генерируем код через OpenRouter
    generated_code = generate_code_with_llm(task_description, folder, filename)
    
    # 2. Сохраняем в GitHub
    github_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/src/{folder}/{filename}"
    
    check_response = requests.get(github_url, headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }, timeout=10)
    
    sha = None
    if check_response.status_code == 200:
        sha = check_response.json().get("sha")
    
    payload = {
        "message": f"Auto-update: {filename} | {task_description[:50]}...",
        "content": generated_code,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha
        
    put_response = requests.put(github_url, json=payload, headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }, timeout=10)
    
    if put_response.status_code not in [200, 201]:
        return jsonify({
            "error": "Ошибка записи в GitHub", 
            "details": put_response.text
        }), 500
    
    # 3. Автоматическое обновление в Roblox
    db = load_assets_db()
    clean_name = filename.replace(".lua", "").replace(".rbxm", "").replace(".rbxl", "")
    
    if clean_name in db:
        success = update_script_on_roblox(db[clean_name], generated_code)
        if success:
            return jsonify({
                "status": "success", 
                "message": f"Файл {filename} создан и обновлен в Roblox!",
                "github": "ok",
                "roblox": "updated"
            })
        else:
            return jsonify({
                "status": "partial_success",
                "message": f"Файл {filename} создан в GitHub, но ошибка обновления в Roblox",
                "github": "ok",
                "roblox": "failed"
            })
    else:
        print(f"⚠️ Файл {clean_name} не найден в базе. Сканирую плейс...")
        fresh_assets = fetch_asset_ids_from_roblox()
        save_assets_db(fresh_assets)
        
        if clean_name in fresh_assets:
            print(f"✅ Найден новый Asset ID для {clean_name}: {fresh_assets[clean_name]}")
            success = update_script_on_roblox(fresh_assets[clean_name], generated_code)
            if success:
                return jsonify({
                    "status": "success",
                    "message": f"Файл {filename} зарегистрирован и обновлен!",
                    "asset_id": fresh_assets[clean_name],
                    "github": "ok",
                    "roblox": "registered_and_updated"
                })
            else:
                return jsonify({
                    "status": "partial_success",
                    "message": f"ID найден, но ошибка обновления",
                    "asset_id": fresh_assets[clean_name],
                    "github": "ok",
                    "roblox": "update_failed"
                })
        else:
            return jsonify({
                "status": "pending",
                "message": f"Файл {filename} создан в GitHub, но не найден в Roblox. Нажми Publish в Studio!",
                "github": "ok",
                "roblox": "pending_publish"
            })

# === ЭНДПОИНТ ДЛЯ РУЧНОГО СКАНИРОВАНИЯ ===
@app.route("/scan-assets", methods=["GET"])
def scan_assets():
    password = request.args.get("password", "")
    if password != SECURITY_PASSWORD:
        return jsonify({"error": "Неверный пароль"}), 403
        
    assets = fetch_asset_ids_from_roblox()
    save_assets_db(assets)
    return jsonify({"found": len(assets), "assets": assets})

# === HEALTH CHECK ===
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "StealASkybox Generator"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
