import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Считываем переменные из настроек Render
ROBLOX_API_KEY = os.environ.get("ROBLOX_API_KEY")
UNIVERSE_ID = os.environ.get("UNIVERSE_ID")
PLACE_ID = os.environ.get("PLACE_ID")
MY_SECRET_PASSWORD = os.environ.get("MY_SECRET_PASSWORD")

# URL классического API v1 под ваше разрешение universe-places (write)
URL = f"https://apis.roblox.com/universes/v1/{UNIVERSE_ID}/places/{PLACE_ID}/versions"

@app.route("/deploy-script", methods=["POST"])
def deploy_script():
    data = request.json
    
    # 1. Проверка безопасности пароля с телефона
    if data.get("password") != MY_SECRET_PASSWORD:
        return jsonify({"error": "Доступ заблокирован! Неверный пароль."}), 403
        
    ai_code = data.get("code")
    script_name = data.get("script_name", "AI_Script")
    target_folder = data.get("target_folder", "ServerScriptService") # По умолчанию
    script_type = data.get("script_type", "Script") # Обычный, Local или Module

    # 2. Собираем XML-структуру (.rbxlx). 
    # Сервер на лету упакует скрипт ИИ в виртуальную карту для Roblox
    rbxlx_template = f"""<roblox xmlns:xmime="http://w3.org" xmlns:xsi="http://w3.org" xsi:noNamespaceSchemaLocation="http://roblox.com" version="4">
    <Item class="{target_folder}" referent="RBX0">
        <Properties><string name="Name">{target_folder}</string></Properties>
        <Item class="{script_type}" referent="RBX1">
            <Properties>
                <string name="Name">{script_name}</string>
                <ProtectedString name="Source"><![CDATA[{ai_code}]]></ProtectedString>
            </Properties>
        </Item>
    </Item>
</roblox>"""

    # 3. Отправляем в Roblox
    headers = {
        "x-api-key": ROBLOX_API_KEY,
        "Content-Type": "application/xml"
    }
    # versionType = Published сразу активирует обновление в игре
    params = {"versionType": "Published"}
    
    res = requests.post(URL, headers=headers, params=params, data=rbxlx_template.encode('utf-8'))
    
    if res.status_code == 200:
        new_version = res.json().get("versionNumber")
        return jsonify({
            "status": "Success", 
            "message": f"Игра обновлена! Скрипт [{script_type}] '{script_name}' залит в {target_folder}. Новая версия плейса: {new_version}"
        })
    else:
        return jsonify({
            "status": "Roblox API Error", 
            "code": res.status_code, 
            "details": res.text
        }), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
  
