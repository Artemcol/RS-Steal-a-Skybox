import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Считываем переменные из настроек Render
ROBLOX_API_KEY = os.environ.get("DwHLdqkXUEaLykS9mJwW5VLGn3fp28vn6Z+JKob+dyUmbDhUZXlKaGJHY2lPaUpTVXpJMU5pSXNJbXRwWkNJNkluTnBaeTB5TURJeExUQTNMVEV6VkRFNE9qVXhPalE1V2lJc0luUjVjQ0k2SWtwWFZDSjkuZXlKaGRXUWlPaUpTYjJKc2IzaEpiblJsY201aGJDSXNJbWx6Y3lJNklrTnNiM1ZrUVhWMGFHVnVkR2xqWVhScGIyNVRaWEoyYVdObElpd2lZbUZ6WlVGd2FVdGxlU0k2SWtSM1NFeGtjV3RZVlVWaFRIbHJVemx0U25kWE5WWk1SMjR6Wm5BeU9IWnVObG9yU2t0dllpdGtlVlZ0WWtSb1ZTSXNJbTkzYm1WeVNXUWlPaUl4TVRVek16UTBNelF5SWl3aVpYaHdJam94TnpnMU5EZzBOamt6TENKcFlYUWlPakUzT0RVME9ERXdPVE1zSW01aVppSTZNVGM0TlRRNE1UQTVNMzAubGVYTUU1bVB6Znp0LWZSX3B3RTg2YUxITWR6YmJENkt4Sm5TQjd6Ni1kSHRwZjIxdGVFVnZyOXd4bHRlQjhBWkJobm5ibnVCSHJNSVBNa0JuSzRYOFZoalA2N1MtQ1FGQ2lpTmNKMnNuUnRSNmhMY3N0dHRuMk1YZUloTGNwbDExS2VFbS14Y1JWSksxWEhVUGtpbWlYR2xWRlZwZ1E1b3E4djh6UGFuSFBLWUMzakxubm94YncxWWFrX0pRNGlGRnFQbllGcUVIdkdGTW9KWWxCeTBpTXMtUlBNN1RFMHNmeWw3UktYampCOUt1SFcwc05KdHVoWVpDQVBZM0t0SFpsYU1ySThVQTVzMDBDQndwRTVqODh4dHktZkIzZno3ZXlaM3NSVlhFMHpkRHdEbnQzMVFUWFZDOVQ2dklIaXIxallpakpBOHluZUd1SHlwbUQyZnJn")
UNIVERSE_ID = os.environ.get("2729496227")
PLACE_ID = os.environ.get("7074744901")
MY_SECRET_PASSWORD = os.environ.get("Test2026")

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
  
