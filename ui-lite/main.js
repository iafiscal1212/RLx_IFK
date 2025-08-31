document.addEventListener('DOMContentLoaded', () => {
    const groupList = document.getElementById('group-list');
    const welcomeMessage = document.getElementById('welcome-message');
    const conversationView = document.getElementById('conversation-view');
    const createGroupBtn = document.querySelector('.create-group-btn');
    const langSelector = document.getElementById('lang-selector');

    const API_BASE_URL = '/api/v1';

    const I18N = {
        'es': {
            'projectsTitle': 'Proyectos',
            'newProjectBtn': '+ Nuevo Proyecto',
            'welcomeHeader': 'Bienvenida, Carmen.',
            'welcomeSubtext': 'Selecciona un proyecto para ver la conversación o crea uno nuevo.',
            'welcomeHelptext': 'RLx está observando y listo para ayudar.'
        },
        'en': {
            'projectsTitle': 'Projects',
            'newProjectBtn': '+ New Project',
            'welcomeHeader': 'Welcome, Carmen.',
            'welcomeSubtext': 'Select a project to see the conversation or create a new one.',
            'welcomeHelptext': 'RLx is observing and ready to help.'
        }
    };

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

            const groupNameSpan = document.createElement('span');
            groupNameSpan.textContent = group.group_id;
            groupNameSpan.style.flexGrow = '1';

            const renameBtn = document.createElement('button');
            renameBtn.className = 'rename-btn';
            renameBtn.innerHTML = '✏️'; // Pencil emoji
            renameBtn.title = `Renombrar proyecto ${group.group_id}`;
            renameBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                renameGroup(group.group_id);
            });

            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'delete-btn';
            deleteBtn.innerHTML = '&times;'; // 'x' symbol
            deleteBtn.title = `Eliminar proyecto ${group.group_id}`;
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation(); // Evitar que se dispare el click del 'li'
                deleteGroup(group.group_id);
            });

            li.addEventListener('click', () => {
                // Marcar como activo
                document.querySelectorAll('#group-list li').forEach(item => item.classList.remove('active'));
                li.classList.add('active');

                // Cargar la conversación (lógica futura)
                loadConversation(group.group_id);
            });
            li.appendChild(groupNameSpan); // Contenedor para el nombre
            li.appendChild(renameBtn); // Botón de renombrar
            li.appendChild(deleteBtn);
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

    async function renameGroup(oldGroupId) {
        const newGroupId = prompt(`Introduce el nuevo nombre para el proyecto "${oldGroupId}":`, oldGroupId);

        if (!newGroupId || newGroupId === oldGroupId) {
            return; // El usuario canceló o no cambió el nombre
        }

        if (!/^[a-zA-Z0-9_-]+$/.test(newGroupId)) {
            alert("Nombre de proyecto no válido. Usa solo letras, números, guiones y guiones bajos.");
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/groups/${oldGroupId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ new_group_id: newGroupId }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Error: ${response.statusText}`);
            }

            // Éxito: refrescar la lista para mostrar el proyecto renombrado
            await fetchGroups();
            // Opcional: seleccionar automáticamente el proyecto renombrado

        } catch (error) {
            console.error(`Error al renombrar el proyecto ${oldGroupId}:`, error);
            alert(`No se pudo renombrar el proyecto: ${error.message}`);
        }
    }

    async function deleteGroup(groupId) {
        const confirmation = confirm(`¿Estás seguro de que quieres eliminar el proyecto "${groupId}"? Esta acción no se puede deshacer.`);
        if (!confirmation) {
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/groups/${groupId}`, {
                method: 'DELETE',
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Error: ${response.statusText}`);
            }

            // Éxito: refrescar la lista para eliminar el proyecto de la vista
            await fetchGroups();

        } catch (error) {
            console.error(`Error al eliminar el proyecto ${groupId}:`, error);
            alert(`No se pudo eliminar el proyecto: ${error.message}`);
        }
    }

    function updateUIText(lang) {
        const elements = document.querySelectorAll('[data-i18n-key]');
        elements.forEach(el => {
            const key = el.dataset.i18nKey;
            if (I18N[lang] && I18N[lang][key]) {
                el.textContent = I18N[lang][key];
            }
        });
    }

    function handleLangChange() {
        const selectedLang = langSelector.value;
        // Guardar la preferencia del usuario en el almacenamiento local del navegador.
        localStorage.setItem('rlx-ui-lang', selectedLang);
        updateUIText(selectedLang);
        console.log(`Idioma de la interfaz cambiado a: ${selectedLang}`);
    }

    function loadLangPreference() {
        const savedLang = localStorage.getItem('rlx-ui-lang') || 'es';
        if (savedLang && ['es', 'en'].includes(savedLang)) {
            langSelector.value = savedLang;
        }
        updateUIText(savedLang);
    }

    createGroupBtn.addEventListener('click', createGroup);
    langSelector.addEventListener('change', handleLangChange);
    // Carga inicial
    fetchGroups();
    loadLangPreference();
});
