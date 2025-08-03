// Conectar al servidor WebSocket
const socket = io.connect('http://127.0.0.1:9999');

// Escuchar el evento 'log' para actualizar el contenido del div de logs
socket.on('log', function(data) {
    const logs = document.getElementById('attempts');
    const newLog = document.createElement('p');
    newLog.textContent = data;
    logs.appendChild(newLog);  // Agregar el nuevo log al div
});

//Limpieza visual desde Flask (si se emite el evento 'clear')
socket.on('clear', function() {
    document.getElementById('attempts').innerHTML = '';
    document.getElementById('results').innerHTML = '';
});

// Evento para iniciar el ataque
document.getElementById('attack-form').addEventListener('submit', function(event) {
    event.preventDefault();

    const url = document.getElementById('url').value;
    const usernamesInput = document.getElementById('usernames').value;
    const passwordInput = document.getElementById('passwords').value;

    // Verificar si la URL está vacía
    if (!url) {
        alert("Por favor, ingresa una URL válida.");
        return;
    }

    let usernames = [];
    if (usernamesInput) {
        usernames = [usernamesInput.trim()];
    }

    const data = {
        url: url,
        usernames: usernames,
        password: passwordInput ? passwordInput : null  // Si no hay contraseña, la dejamos como null
    };

    fetch('/start_attack', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        let results = '';
        if (data.success) {
            results = `<p>Éxito! Credenciales válidas: ${data.username}:${data.password}</p>`;
        } else {
            results = `<p>Error: ${data.error}</p>`;
        }
        document.getElementById('results').innerHTML = results;
    })
    .catch(error => {
        document.getElementById('results').innerHTML = `<p>Error: ${error}</p>`;
    });
});

// Función para detener el ataque
document.getElementById('stop-attack').addEventListener('click', function() {
    fetch('/stop_attack', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.message); 
    })
    .catch(error => console.error('Error:', error));
});