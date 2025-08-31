document.addEventListener('DOMContentLoaded', () => {
    const groupList = document.getElementById('group-list');
    const welcomeMessage = document.getElementById('welcome-message');
    const conversationView = document.getElementById('conversation-view');
    const createGroupBtn = document.querySelector('.create-group-btn');
    const statusIndicator = document.querySelector('.status-indicator');
    const themeSwitch = document.getElementById('theme-switch-checkbox');
    const groupSearchInput = document.getElementById('group-search-input');
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
    const toastContainer = document.getElementById('toast-container');

    let metricsIntervalId = null;

    const LAST_SEEN_KEY = 'rlx-last-seen';

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
            'createBtn': 'Crear',
            'loadingBtn': 'Cargando...',
            'searchProjectPlaceholder': 'Buscar proyecto...',
            'noProjects': 'No hay proyectos.',
            'messagePlaceholder': 'Escribe un mensaje...',
            'sendBtn': 'Enviar',
            'summaryTopics': 'Temas',
            'summaryDecisions': 'Decisiones',
            'summaryActions': 'Acciones',
            'copySummaryTitle': 'Copiar resumen al portapapeles',
            'copySuccess': 'Resumen copiado.',
            'metricFrictionTitle': 'Índice de Fricción (alertas / mensajes en 24h)',
            'metricArousalTitle': 'Energía del Grupo (Arousal Z-Score mediano en 10 min)',
            'metricValenceTitle': 'Tono del Grupo (Valence Z-Score mediano en 10 min)',
            'metricFrictionLabel': 'Fricción',
            'metricArousalLabel': 'Energía',
            'metricValenceLabel': 'Tono',
            'arousalSpikeToast': '¡Atención! Nivel de energía elevado detectado.',
            'suggestionToast': 'RLx tiene una nueva sugerencia para el grupo.',
            'templateLabel': 'Plantilla inicial',
            'templateNone': 'Ninguna (vacío)',
            'templateScientific': 'Científico',
            'templateBusiness': 'Empresarial',
            'templateCreative': 'Creativo',
            'templateStrategic': 'Estratégico',
            'createSuccess': "Proyecto '{groupId}' creado.",
            'renameSuccess': "Proyecto renombrado a '{newGroupId}'.",
            'deleteSuccess': "Proyecto '{groupId}' eliminado."
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
            'createBtn': 'Create',
            'loadingBtn': 'Loading...',
            'searchProjectPlaceholder': 'Search project...',
            'noProjects': 'No projects.',
            'messagePlaceholder': 'Write a message...',
            'sendBtn': 'Send',
            'summaryTopics': 'Topics',
            'summaryDecisions': 'Decisions',
            'summaryActions': 'Actions',
            'copySummaryTitle': 'Copy summary to clipboard',
            'copySuccess': 'Summary copied.',
            'metricFrictionTitle': 'Friction Index (alerts / messages in 24h)',
            'metricArousalTitle': 'Group Energy (median Arousal Z-Score in 10 min)',
            'metricValenceTitle': 'Group Tone (median Valence Z-Score in 10 min)',
            'metricFrictionLabel': 'Friction',
            'metricArousalLabel': 'Energy',
            'metricValenceLabel': 'Tone',
            'arousalSpikeToast': 'Attention! Elevated energy level detected.',
            'suggestionToast': 'RLx has a new suggestion for the group.',
            'templateLabel': 'Initial Template',
            'templateNone': 'None (empty)',
            'templateScientific': 'Scientific',
            'templateBusiness': 'Business',
            'templateCreative': 'Creative',
            'templateStrategic': 'Strategic',
            'createSuccess': "Project '{groupId}' created.",
            'renameSuccess': "Project renamed to '{newGroupId}'.",
            'deleteSuccess': "Project '{groupId}' deleted."
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
            showToast('Error al cargar proyectos.', 'error');
        }
    }

    function renderGroupList(groups) {
        if (!groups || groups.length === 0) {
            const lang = langSelector.value;
            groupList.innerHTML = `<li class="loading">${I18N[lang].noProjects}</li>`;
            return;
        }

        groupList.innerHTML = ''; // Limpiar la lista
        groups.forEach(group => {
            const li = document.createElement('li');
            li.dataset.groupId = group.group_id;
            li.title = `Última actividad: ${new Date(group.last_modified).toLocaleString()}`;

            if (group.has_recent_alerts) {
                li.classList.add('has-alert');
            }

            const alertIndicator = document.createElement('span');
            alertIndicator.className = 'alert-indicator';
            alertIndicator.title = 'Este proyecto tiene alertas recientes.';

            const groupNameSpan = document.createElement('span');
            groupNameSpan.textContent = group.group_id;

            const groupNameWrapper = document.createElement('div');
            groupNameWrapper.className = 'group-name-wrapper';

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

                // Si tenía una alerta, la eliminamos visualmente al hacer clic
                if (li.classList.contains('has-alert')) {
                    li.classList.remove('has-alert');
                }

                // Cargar la conversación (lógica futura)
                loadConversation(group.group_id, langSelector.value);
            });

            groupNameWrapper.appendChild(alertIndicator);
            groupNameWrapper.appendChild(groupNameSpan);
            li.appendChild(groupNameWrapper);
            li.appendChild(renameBtn); // Botón de renombrar
            li.appendChild(deleteBtn);
            groupList.appendChild(li);
        });
        updateUIText(langSelector.value);
    }

    async function loadConversation(groupId, lang) {
        if (metricsIntervalId) {
            clearInterval(metricsIntervalId);
            metricsIntervalId = null;
        }

        try {
            welcomeMessage.classList.add('hidden');
            conversationView.classList.remove('hidden');
            conversationView.dataset.currentGroupId = groupId;
            document.title = `RLx - ${groupId}`;
            conversationView.querySelector('#log-container').innerHTML = `<p class="loading">${I18N[lang].loadingBtn}</p>`;

            const response = await fetch(`${API_BASE_URL}/groups/${groupId}/state`);
            if (!response.ok) {
                throw new Error(`Error al cargar el estado del grupo: ${response.statusText}`);
            }
            const state = await response.json();

            // --- Lógica para encontrar la primera alerta no vista ---
            const lastSeenTimestamps = JSON.parse(localStorage.getItem(LAST_SEEN_KEY) || '{}');
            const lastSeenTs = lastSeenTimestamps[groupId] ? new Date(lastSeenTimestamps[groupId]) : new Date(0);
            let firstUnreadAlertId = null;

            // Iteramos para encontrar la primera alerta más nueva que la última vez que se vio.
            for (const record of (state.log || [])) {
                if (record.type === 'alert' && new Date(record.ts) > lastSeenTs) {
                    firstUnreadAlertId = record.msg_id;
                    break; // Nos quedamos con la primera que encontramos
                }
            }
            // --- Fin de la lógica ---

            // Iniciar la actualización de métricas
            updateMetrics(groupId);
            metricsIntervalId = setInterval(() => updateMetrics(groupId), 7000);

            checkForNewNotifications(state.log || [], lang);
            renderLog(state.log || [], lang, firstUnreadAlertId); // Pasamos el ID para resaltarlo

            // Si encontramos una alerta, hacemos scroll hacia ella y la resaltamos
            if (firstUnreadAlertId) {
                const alertElement = document.getElementById(`log-item-${firstUnreadAlertId}`);
                if (alertElement) {
                    alertElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }

            // Actualizamos el timestamp de "última vez visto" para este grupo
            lastSeenTimestamps[groupId] = new Date().toISOString();
            localStorage.setItem(LAST_SEEN_KEY, JSON.stringify(lastSeenTimestamps));

            // Adjuntar el evento al formulario de mensajes
            const messageForm = document.getElementById('message-form');
            // Clonar y reemplazar para eliminar listeners antiguos
            const newForm = messageForm.cloneNode(true);
            conversationView.replaceChild(newForm, messageForm);
            newForm.addEventListener('submit', handleMessageSubmit);
            updateUIText(lang); // Para actualizar placeholders, etc.

        } catch (error) {
            console.error(`Error al cargar la conversación para ${groupId}:`, error);
            showToast(error.message, 'error');
            conversationView.querySelector('#log-container').innerHTML = `<p class="error">${error.message}</p>`;
        }
    }

    function renderLog(log, lang, highlightId = null) {
        const logContainer = document.getElementById('log-container');
        logContainer.innerHTML = ''; // Limpiar

        if (log.length === 0) {
            logContainer.innerHTML = `<p class="loading">No hay mensajes en este proyecto.</p>`;
            return;
        }

        log.forEach(record => {
            const logItem = createLogItemElement(record, lang, highlightId);
            logContainer.appendChild(logItem);
        });

        // Scroll hasta el final, solo si no estamos haciendo scroll a una alerta específica
        if (!highlightId) {
            logContainer.scrollTop = logContainer.scrollHeight;
        }
    }

    function createLogItemElement(record, lang, highlightId = null) {
        const item = document.createElement('div');
        item.className = `log-item log-item--${record.type}`;
        item.id = `log-item-${record.msg_id}`; // Asignar ID único

        // Resaltar si coincide con el ID
        if (record.msg_id === highlightId) {
            item.classList.add('log-item--highlight');
        }

        const header = document.createElement('div');
        header.className = 'log-item__header';

        const timestamp = document.createElement('span');
        timestamp.className = 'log-item__timestamp';
        timestamp.textContent = new Date(record.ts).toLocaleString();

        switch (record.type) {
            case 'message':
                const author = document.createElement('strong');
                author.className = 'log-item__author';
                author.textContent = record.author;
                header.appendChild(author);
                header.appendChild(timestamp);
                item.appendChild(header);
                const text = document.createElement('p');
                text.textContent = record.text;
                text.style.margin = '0';
                item.appendChild(text);
                break;

            case 'alert':
                header.innerHTML = `<span class="log-item__icon">⚠️</span><strong>Alerta del Sistema</strong>`;
                header.appendChild(timestamp);
                item.appendChild(header);
                const rationale = document.createElement('p');
                rationale.textContent = record.details.rationale;
                rationale.style.margin = '0';
                item.appendChild(rationale);
                break;

            case 'daily_summary':
                header.innerHTML = `<span class="log-item__icon">📋</span><strong>Resumen Diario</strong>`;
                header.appendChild(timestamp);

                // --- Añadir botón de copiar ---
                const copyBtn = document.createElement('button');
                copyBtn.className = 'copy-summary-btn';
                copyBtn.innerHTML = '📄'; // Icono de documento
                copyBtn.title = I18N[lang].copySummaryTitle;
                copyBtn.addEventListener('click', () => {
                    const summaryText = generateSummaryText(record.details, lang, record.ts);
                    navigator.clipboard.writeText(summaryText).then(() => {
                        showToast(I18N[lang].copySuccess, 'success');
                    }).catch(err => {
                        console.error('Error al copiar el resumen:', err);
                        showToast('No se pudo copiar el resumen.', 'error');
                    });
                });
                header.appendChild(copyBtn);
                // --- Fin del botón de copiar ---

                item.appendChild(header);
                item.appendChild(createSummarySection(I18N[lang].summaryTopics, record.details.topics, lang));
                item.appendChild(createSummarySection(I18N[lang].summaryDecisions, record.details.decisions, lang));
                item.appendChild(createSummarySection(I18N[lang].summaryActions, record.details.actions, lang, true));
                break;

            case 'suggestion':
                header.innerHTML = `<span class="log-item__icon">💡</span><strong>Sugerencia de RLx</strong>`;
                header.appendChild(timestamp);
                item.appendChild(header);
                const suggestionText = document.createElement('p');
                suggestionText.textContent = record.details.suggestion_text;
                suggestionText.style.margin = '0';
                item.appendChild(suggestionText);
                break;

            default:
                item.textContent = `Tipo de registro desconocido: ${record.type}`;
        }
        return item;
    }

    function createSummarySection(title, items, lang, isAction = false) {
        const section = document.createElement('div');
        if (!items || items.length === 0) return section;

        section.className = 'summary-section';
        section.innerHTML = `<h4>${title}</h4>`;
        const ul = document.createElement('ul');
        items.forEach(item => {
            const li = document.createElement('li');
            li.textContent = isAction ? `${item.assignee}: ${item.task}` : item;
            ul.appendChild(li);
        });
        section.appendChild(ul);
        return section;
    }

    function generateSummaryText(details, lang, timestamp) {
        const i18n = I18N[lang];
        const dateStr = new Date(timestamp).toLocaleDateString();
        let text = `Resumen Diario (${dateStr})\n`;
        text += '----------------------------------\n\n';

        if (details.topics && details.topics.length > 0) {
            text += `${i18n.summaryTopics}:\n`;
            details.topics.forEach(topic => {
                text += `- ${topic}\n`;
            });
            text += '\n';
        }

        if (details.decisions && details.decisions.length > 0) {
            text += `${i18n.summaryDecisions}:\n`;
            details.decisions.forEach(decision => {
                text += `- ${decision}\n`;
            });
            text += '\n';
        }

        if (details.actions && details.actions.length > 0) {
            text += `${i18n.summaryActions}:\n`;
            details.actions.forEach(action => {
                text += `- ${action.assignee}: ${action.task}\n`;
            });
            text += '\n';
        }

        return text.trim();
    }

    function checkForNewNotifications(log, lang) {
        if (!log || log.length === 0) return;

        const lastRecord = log[log.length - 1];
        const recordTime = new Date(lastRecord.ts);
        const now = new Date();
        const timeDiffSeconds = (now - recordTime) / 1000;

        // Solo mostrar toast para registros muy recientes para evitar re-notificar en cada carga.
        if (timeDiffSeconds > 5) {
            return;
        }

        const i18n = I18N[lang];
        if (lastRecord.type === 'alert' && lastRecord.alert_type === 'arousal_spike_detected') {
            showToast(i18n.arousalSpikeToast, 'warning');
        } else if (lastRecord.type === 'suggestion') {
            // Usar un tipo 'info' para sugerencias
            showToast(i18n.suggestionToast, 'info');
        }
    }

    function createGroup() {
        // Muestra el modal de creación
        createGroupIdInput.value = '';
        createModal.classList.remove('hidden');
        createGroupIdInput.focus();
    }

    async function handleMessageSubmit(event) {
        event.preventDefault();
        const input = document.getElementById('message-input');
        const text = input.value.trim();
        const groupId = conversationView.dataset.currentGroupId;

        if (!text || !groupId) return;

        try {
            const response = await fetch(`${API_BASE_URL}/groups/${groupId}/ingest`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ author: 'Carmen', text: text }), // Autor hardcodeado por ahora
            });
            if (!response.ok) {
                throw new Error(`Error al enviar el mensaje: ${response.statusText}`);
            }
            input.value = '';
            loadConversation(groupId, langSelector.value); // Recargar para ver el nuevo mensaje
        } catch (error) {
            console.error('Error al enviar mensaje:', error);
            showToast(error.message, 'error');
        }
    }

    async function handleCreateSubmit(event) {
        event.preventDefault();
        const groupId = createGroupIdInput.value.trim();
        const templateSelect = document.getElementById('create-group-template-select');
        const template = templateSelect.value;

        if (!groupId) return;

        if (!/^[a-zA-Z0-9_-]+$/.test(groupId)) {
            showToast("Nombre de proyecto no válido. Usa solo letras, números, guiones y guiones bajos.", 'error');
            return;
        }

        try {
            setModalLoadingState(createModal, true);
            const payload = { group_id: groupId };
            if (template) {
                payload.template = template;
            }
            const response = await fetch(`${API_BASE_URL}/groups`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Error: ${response.statusText}`);
            }
            await fetchGroups();

            // Seleccionar automáticamente el nuevo proyecto simulando un clic
            const newGroupItem = document.querySelector(`#group-list li[data-group-id="${groupId}"]`);
            if (newGroupItem) {
                newGroupItem.click();
            }

            const lang = langSelector.value;
            showToast(I18N[lang].createSuccess.replace('{groupId}', groupId), 'success');

        } catch (error) {
            console.error('Error al crear el proyecto:', error);
            showToast(`No se pudo crear el proyecto: ${error.message}`, 'error');
        } finally {
            setModalLoadingState(createModal, false);
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
            showToast("Nombre de proyecto no válido. Usa solo letras, números, guiones y guiones bajos.", 'error');
            return;
        }

        try {
            setModalLoadingState(renameModal, true);
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
            const lang = langSelector.value;
            showToast(I18N[lang].renameSuccess.replace('{newGroupId}', newGroupId), 'success');
        } catch (error) {
            console.error(`Error al renombrar el proyecto ${oldGroupId}:`, error);
            showToast(`No se pudo renombrar el proyecto: ${error.message}`, 'error');
        } finally {
            setModalLoadingState(renameModal, false);
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
            setModalLoadingState(deleteModal, true);
            const response = await fetch(`${API_BASE_URL}/groups/${groupId}`, { method: 'DELETE' });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Error: ${response.statusText}`);
            }
            await fetchGroups();
            // Si el proyecto eliminado era el activo, volver a la pantalla de bienvenida
            const activeItem = document.querySelector('#group-list li.active');
            if (activeItem && activeItem.dataset.groupId === groupId) {
                // Detener la actualización de métricas
                if (metricsIntervalId) {
                    clearInterval(metricsIntervalId);
                    metricsIntervalId = null;
                }
                // Limpiar el panel de métricas
                resetMetricsPanel();

                welcomeMessage.classList.remove('hidden');
                conversationView.classList.add('hidden');
                document.title = 'RLx - Panel de Control';
            }
            const lang = langSelector.value;
            showToast(I18N[lang].deleteSuccess.replace('{groupId}', groupId), 'success');
        } catch (error) {
            console.error(`Error al eliminar el proyecto ${groupId}:`, error);
            showToast(`No se pudo eliminar el proyecto: ${error.message}`, 'error');
        } finally {
            setModalLoadingState(deleteModal, false);
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

    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type.toLowerCase()}`;

        const messageSpan = document.createElement('span');
        messageSpan.textContent = message;

        const closeBtn = document.createElement('button');
        closeBtn.className = 'toast-close-btn';
        closeBtn.innerHTML = '&times;';

        toast.appendChild(messageSpan);
        toast.appendChild(closeBtn);

        toastContainer.appendChild(toast);

        const removeToast = () => {
            toast.classList.add('fade-out');
            toast.addEventListener('animationend', () => toast.remove());
        };

        const timeoutId = setTimeout(removeToast, 5000);

        closeBtn.addEventListener('click', () => {
            clearTimeout(timeoutId);
            removeToast();
        });
    }

    function setModalLoadingState(modal, isLoading) {
        const confirmBtn = modal.querySelector('#confirm-create-btn, #confirm-rename-btn, #confirm-delete-btn');
        const cancelBtn = modal.querySelector('#cancel-create-btn, #cancel-rename-btn, #cancel-delete-btn');

        if (!confirmBtn || !cancelBtn) return;

        if (isLoading) {
            confirmBtn.disabled = true;
            cancelBtn.disabled = true;
            if (!confirmBtn.dataset.originalText) {
                confirmBtn.dataset.originalText = confirmBtn.textContent;
            }
            const lang = langSelector.value;
            confirmBtn.textContent = I18N[lang].loadingBtn;
        } else {
            confirmBtn.disabled = false;
            cancelBtn.disabled = false;
            if (confirmBtn.dataset.originalText) {
                confirmBtn.textContent = confirmBtn.dataset.originalText;
                delete confirmBtn.dataset.originalText;
            }
        }
    }

    function updateUIText(lang) {
        const elements = document.querySelectorAll('[data-i18n-key]');
        elements.forEach(el => {
            const key = el.dataset.i18nKey;
            if (I18N[lang] && I18N[lang][key]) {
                el.textContent = I18N[lang][key];
        }
        const placeholderKey = el.dataset.i18nPlaceholder;
        if (I18N[lang] && I18N[lang][placeholderKey]) {
            el.placeholder = I18N[lang][placeholderKey];
            }
        const titleKey = el.dataset.i18nTitle;
        if (I18N[lang] && I18N[lang][titleKey]) {
            el.title = I18N[lang][titleKey];
        }
    });
    }

    async function updateMetrics(groupId) {
        try {
            const response = await fetch(`${API_BASE_URL}/groups/${groupId}/metrics`);
            if (!response.ok) return; // Fallar silenciosamente, el panel simplemente no se actualizará
            const metrics = await response.json();

            const frictionEl = document.getElementById('metric-friction');
            const arousalEl = document.getElementById('metric-arousal');
            const valenceEl = document.getElementById('metric-valence');

            if (frictionEl) {
                frictionEl.textContent = metrics.friction_index.toFixed(2);
                frictionEl.classList.toggle('is-high', metrics.friction_index > 0.25);
            }
            if (arousalEl) {
                arousalEl.textContent = metrics.affective_proxy.arousal_z.toFixed(2);
                arousalEl.classList.toggle('is-high', metrics.affective_proxy.arousal_z > 1.0);
            }
            if (valenceEl) {
                valenceEl.textContent = metrics.affective_proxy.valence_z.toFixed(2);
                valenceEl.classList.toggle('is-low', metrics.affective_proxy.valence_z < -0.5);
            }

        } catch (error) {
            console.error(`Fallo al actualizar las métricas para ${groupId}:`, error);
        }
    }

    function resetMetricsPanel() {
        const frictionEl = document.getElementById('metric-friction');
        const arousalEl = document.getElementById('metric-arousal');
        const valenceEl = document.getElementById('metric-valence');
        if (frictionEl) frictionEl.textContent = '0.00';
        if (arousalEl) arousalEl.textContent = '0.00';
        if (valenceEl) valenceEl.textContent = '0.00';
        document.querySelectorAll('.metric-value').forEach(el => {
            el.classList.remove('is-high', 'is-low');
        });
    }

    async function checkHealth() {
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            }
        });
    }

    async function checkHealth() {
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            statusIndicator.classList.toggle('online', response.ok);
            statusIndicator.classList.toggle('offline', !response.ok);
        } catch (error) {
            statusIndicator.classList.remove('online');
            statusIndicator.classList.add('offline');
        }
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

    function handleThemeChange() {
        if (themeSwitch.checked) {
            document.body.classList.add('dark-mode');
            localStorage.setItem('rlx-ui-theme', 'dark');
        } else {
            document.body.classList.remove('dark-mode');
            localStorage.setItem('rlx-ui-theme', 'light');
        }
    }

    function loadThemePreference() {
        const savedTheme = localStorage.getItem('rlx-ui-theme');
        if (savedTheme === 'dark') {
            themeSwitch.checked = true;
            document.body.classList.add('dark-mode');
        }
    }

    function handleGroupSearch() {
        const searchTerm = groupSearchInput.value.toLowerCase();
        const groupItems = groupList.querySelectorAll('li');

        groupItems.forEach(item => {
            // Only filter items that are actual groups (have a data-group-id)
            if (item.dataset.groupId) {
                const groupId = item.dataset.groupId.toLowerCase();
                const isVisible = groupId.includes(searchTerm);
                // The default display is 'flex' from the stylesheet
                item.style.display = isVisible ? 'flex' : 'none';
            }
        });
    }

    createGroupBtn.addEventListener('click', createGroup);
    langSelector.addEventListener('change', handleLangChange);
    themeSwitch.addEventListener('change', handleThemeChange);

    // Evento para el campo de búsqueda
    groupSearchInput.addEventListener('input', handleGroupSearch);

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
    loadLangPreference();
    checkHealth();
    setInterval(checkHealth, 15000); // Comprobar cada 15 segundos
});
