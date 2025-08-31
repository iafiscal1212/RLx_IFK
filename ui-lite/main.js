document.addEventListener('DOMContentLoaded', () => {
    const groupList = document.getElementById('group-list');
    const welcomeMessage = document.getElementById('welcome-message');
    const conversationView = document.getElementById('conversation-view');
    const createGroupBtn = document.querySelector('.create-group-btn');
    const langSelector = document.getElementById('lang-selector');
    // Elementos del modal de renombrar
    const renameModal = document.getElementById('rename-modal');
    const renameForm = document.getElementById('rename-form');
    const newGroupIdInput = document.getElementById('new-group-id-input');
    const cancelRenameBtn = document.getElementById('cancel-rename-btn');
    // Elementos del modal de eliminar
    const deleteModal = document.getElementById('delete-modal');
    const deleteModalText = document.getElementById('delete-modal-text');
    const cancelDeleteBtn = document.getElementById('cancel-delete-btn');
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    // Elementos del modal de crear
    const createModal = document.getElementById('create-modal');
    const createForm = document.getElementById('create-form');
    const createGroupIdInput = document.getElementById('create-group-id-input');
    const cancelCreateBtn = document.getElementById('cancel-create-btn');

    const API_BASE_URL = '/api/v1';

    const I18N = {
        'es': {
            'projectsTitle': 'Proyectos',
            'newProjectBtn': '+ Nuevo Proyecto',
            'welcomeHeader': 'Bienvenida, Carmen.',
            'welcomeSubtext': 'Selecciona un proyecto para ver la conversación o crea uno nuevo.',
            'welcomeHelptext': 'RLx está observando y listo para ayudar.',
            'renameModalTitle': 'Renombrar Proyecto',
            'cancelBtn': 'Cancelar',
            'confirmBtn': 'Confirmar',
            'deleteModalTitle': 'Eliminar Proyecto',
            'deleteModalText': '¿Estás seguro de que quieres eliminar el proyecto "{groupId}"? Esta acción no se puede deshacer.',
            'deleteBtn': 'Eliminar',
            'createModalTitle': 'Crear Nuevo Proyecto',
            'createBtn': 'Crear'
        },
        'en': {
            'projectsTitle': 'Projects',
            'newProjectBtn': '+ New Project',
            'welcomeHeader': 'Welcome, Carmen.',
            'welcomeSubtext': 'Select a project to see the conversation or create a new one.',
            'welcomeHelptext': 'RLx is observing and ready to help.',
            'renameModalTitle': 'Rename Project',
            'cancelBtn': 'Cancel',
            'confirmBtn': 'Confirm',
            'deleteModalTitle': 'Delete Project',
            'deleteModalText': 'Are you sure you want to delete the project "{groupId}"? This action cannot be undone.',
            'deleteBtn': 'Delete',
            'createModalTitle': 'Create New Project',
            'createBtn': 'Create'
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

    function createGroup() {
        // Muestra el modal de creación
        createGroupIdInput.value = '';
        createModal.classList.remove('hidden');
        createGroupIdInput.focus();
    }

    async function handleCreateSubmit(event) {
        event.preventDefault();
        const groupId = createGroupIdInput.value.trim();

        if (!groupId) return;

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
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Error: ${response.statusText}`);
            }
            await fetchGroups();
        } catch (error) {
            console.error('Error al crear el proyecto:', error);
            alert(`No se pudo crear el proyecto: ${error.message}`);
        } finally {
            closeCreateModal();
        }
    }

    function renameGroup(oldGroupId) {
        // Muestra el modal en lugar de un prompt
        newGroupIdInput.value = oldGroupId;
        renameModal.dataset.oldGroupId = oldGroupId; // Guarda el ID antiguo en el modal
        renameModal.classList.remove('hidden');
        newGroupIdInput.focus();
        newGroupIdInput.select();
    }

    async function handleRenameSubmit(event) {
        event.preventDefault();
        const oldGroupId = renameModal.dataset.oldGroupId;
        const newGroupId = newGroupIdInput.value.trim();

        if (!newGroupId || newGroupId === oldGroupId) {
            closeRenameModal();
            return;
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
            await fetchGroups();
        } catch (error) {
            console.error(`Error al renombrar el proyecto ${oldGroupId}:`, error);
            alert(`No se pudo renombrar el proyecto: ${error.message}`);
        } finally {
            closeRenameModal();
        }
    }

    function deleteGroup(groupId) {
        // Muestra el modal de confirmación
        const lang = langSelector.value;
        const text = I18N[lang].deleteModalText.replace('{groupId}', groupId);
        deleteModalText.textContent = text;
        deleteModal.dataset.groupId = groupId;
        deleteModal.classList.remove('hidden');
    }

    async function handleConfirmDelete() {
        const groupId = deleteModal.dataset.groupId;
        if (!groupId) return;

        try {
            const response = await fetch(`${API_BASE_URL}/groups/${groupId}`, { method: 'DELETE' });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Error: ${response.statusText}`);
            }
            await fetchGroups();
            // Si el proyecto eliminado era el activo, volver a la pantalla de bienvenida
            const activeItem = document.querySelector('#group-list li.active');
            if (activeItem && activeItem.dataset.groupId === groupId) {
                welcomeMessage.classList.remove('hidden');
                conversationView.classList.add('hidden');
            }
        } catch (error) {
            console.error(`Error al eliminar el proyecto ${groupId}:`, error);
            alert(`No se pudo eliminar el proyecto: ${error.message}`);
        } finally {
            closeDeleteModal();
        }
    }

    function closeDeleteModal() {
        deleteModal.classList.add('hidden');
        delete deleteModal.dataset.groupId;
    }

    function closeCreateModal() {
        createModal.classList.add('hidden');
    }

    function closeRenameModal() {
        renameModal.classList.add('hidden');
        delete renameModal.dataset.oldGroupId;
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

    // Eventos del modal de renombrar
    renameForm.addEventListener('submit', handleRenameSubmit);
    cancelRenameBtn.addEventListener('click', closeRenameModal);
    renameModal.addEventListener('click', (e) => {
        if (e.target === renameModal) closeRenameModal();
    });

    // Eventos del modal de eliminar
    confirmDeleteBtn.addEventListener('click', handleConfirmDelete);
    cancelDeleteBtn.addEventListener('click', closeDeleteModal);
    deleteModal.addEventListener('click', (e) => {
        if (e.target === deleteModal) closeDeleteModal();
    });

    // Eventos del modal de crear
    createForm.addEventListener('submit', handleCreateSubmit);
    cancelCreateBtn.addEventListener('click', closeCreateModal);
    createModal.addEventListener('click', (e) => {
        if (e.target === createModal) closeCreateModal();
    });

    // Carga inicial
    fetchGroups();
    loadLangPreference();
});
