# HACK IA - IA de Ataque v1.0.0

Este proyecto es una herramienta educativa que simula ataques de fuerza bruta a formularios de login. Utiliza Flask, Socket.IO y Selenium para automatizar pruebas de contraseñas.

## Características

- Generación progresiva de usuarios y contraseñas
- Ataques automatizados con Selenium
- Consola en tiempo real con logs vía Socket.IO
- Botón para detener el ataque
- Botón para limpiar consola y logs

## Instalación

```bash
git clone https://github.com/Codeveloperr/HACKAI
cd HACKIA
python -m venv venv
source venv/bin/activate  # En Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python server.py
Uso
Ingresa la URL de login (por ejemplo, de WordPress)

(Opcional) Agrega usuario y contraseña

Inicia el ataque y observa los logs en tiempo real

Puedes detener el ataque o limpiar la consola

⚠ Solo para fines educativos y en entornos de prueba
