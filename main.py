import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Эти строки оставляем строго так! Они сами возьмут данные из Render
ROBLOX_API_KEY = os.environ.get("ROBLOX_API_KEY")
UNIVERSE_ID = os.environ.get("UNIVERSE_ID")
PLACE_ID = os.environ.get("PLACE_ID")

URL = f"https://roblox.com{UNIVERSE_ID}/places/{PLACE_ID}/versions"

@app.route("/deploy-script", methods=["POST"])
def deploy_script():
    ai_code = request.data.decode('utf-8')
    
    if not ai_code:
        return jsonify({"error": "Телефон отправил пустой код"}), 400

    # Правильный минимальный скелет плейса для Roblox
    rbxlx_template = f"""<roblox xmlns:xmime="http://w3.org" xmlns:xsi="http://w3.org" xsi:noNamespaceSchemaLocation="http://roblox.com" version="4">
	<Meta name="ExplicitAutoJoints">true</Meta>
	<Item class="Workspace" referent="RBX0">
		<Properties>
			<string name="Name">Workspace</string>
		</Properties>
	</Item>
	<Item class="ServerScriptService" referent="RBX1">
		<Properties>
			<string name="Name">ServerScriptService</string>
		</Properties>
		<Item class="Script" referent="RBX2">
			<Properties>
				<string name="Name">AI_Final_Test</string>
				<ProtectedString name="Source"><![CDATA[{ai_code}]]></ProtectedString>
			</Properties>
		</Item>
	</Item>
</roblox>"""

    headers = {
        "x-api-key": ROBLOX_API_KEY,
        "Content-Type": "application/xml"
    }
    
    res = requests.post(URL, headers=headers, params={"versionType": "Published"}, data=rbxlx_template.encode('utf-8'))
    
    if res.status_code == 200:
        new_version = res.json().get("versionNumber")
        return jsonify({
            "status": "Success", 
            "message": f"🎉 ПОБЕДА! Игра успешно обновлена! Новая версия плейса: {new_version}"
        })
    else:
        return jsonify({"status": "Roblox API Error", "code": res.status_code, "details": res.text}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    
