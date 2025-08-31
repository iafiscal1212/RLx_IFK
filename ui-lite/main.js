document.addEventListener('DOMContentLoaded', () => {
    const groupList = document.getElementById('group-list');
    const welcomeMessage = document.getElementById('welcome-message');
    const conversationView = document.getElementById('conversation-view');
    const createGroupBtn = document.querySelector('.create-group-btn');

    const API_BASE_URL = '/api/v1';

    async function fetchGroups() {
        try {
            const response = await fetch(`${API_BASE_URL}/groups`);
            if (!response.ok) {
                throw new Error(`Error en la red: ${response.statusText}`);
            }
            const data = await response.json();
            renderGroupList(data.groups);
        } catch (error) {
            console.error('Error al cargar los grupos:', error);
            groupList.innerHTML = '<li class="loading">Error al cargar proyectos.</li>';
        }
    }

    function renderGroupList(groups) {
        if (!groups || groups.length === 0) {
            groupList.innerHTML = '<li class="loading">No hay proyectos.</li>';
            return;
        }

        groupList.innerHTML = ''; // Limpiar la lista
        groups.forEach(group => {
            const li = document.createElement('li');
            li.textContent = group.group_id;
            li.dataset.groupId = group.group_id;
            li.title = `Última actividad: ${new Date(group.last_modified).toLocaleString()}`;
            li.addEventListener('click', () => {
                // Marcar como activo
                document.querySelectorAll('#group-list li').forEach(item => item.classList.remove('active'));
                li.classList.add('active');

                // Cargar la conversación (lógica futura)
                loadConversation(group.group_id);
            });
            groupList.appendChild(li);
        });
    }

    function loadConversation(groupId) {
        welcomeMessage.classList.add('hidden');
        conversationView.classList.remove('hidden');
        conversationView.innerHTML = `<h2>Conversación de ${groupId}</h2><p>Cargando mensajes...</p>`;
        // Aquí iría la lógica para llamar a GET /groups/{groupId}/state y renderizar los mensajes
        console.log(`Cargando conversación para ${groupId}...`);
    }

    async function createGroup() {
        const groupId = prompt("Introduce el nombre del nuevo proyecto (letras, números, guiones y guiones bajos):");

        if (!groupId) {
            return; // El usuario canceló
        }

        // Validación básica en el cliente
        if (!/^[a-zA-Z0-9_-]+$/.test(groupId)) {
            alert("Nombre de proyecto no válido. Usa solo letras, números, guiones y guiones bajos.");
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/groups`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ group_id: groupId }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Error: ${response.statusText}`);
            }

            // Éxito: refrescar la lista para mostrar el nuevo proyecto
            await fetchGroups();

        } catch (error) {
            console.error('Error al crear el proyecto:', error);
            alert(`No se pudo crear el proyecto: ${error.message}`);
        }
    }

    createGroupBtn.addEventListener('click', createGroup);
    // Carga inicial
    fetchGroups();
});
