document.addEventListener('DOMContentLoaded', () => {
    const API_BASE = '/api/v1';
    const statusLight = document.querySelector('.status-light');
    const statusText = document.getElementById('status-text');
    const resultBox = document.getElementById('result-box');

    const sendForm = document.getElementById('send-form');
    const deliveryForm = document.getElementById('delivery-form');
    const renderForm = document.getElementById('render-form');
    const clearBtn = document.getElementById('clear-btn');

    const deliveryMsgIdInput = document.getElementById('delivery-msg-id');
    const renderMsgIdInput = document.getElementById('render-msg-id');

    // --- Helper to display results ---
    const showResult = (data) => {
        resultBox.textContent = JSON.stringify(data, null, 2);
    };

    // --- API Health Check ---
    const checkApiHealth = async () => {
        try {
            const response = await fetch(`${API_BASE}/health`);
            if (!response.ok) throw new Error('API no responde correctamente');
            const data = await response.json();
            statusLight.classList.add('ok');
            statusText.textContent = data.message;
        } catch (error) {
            statusLight.classList.add('error');
            statusText.textContent = 'API Desconectada';
            showResult({ error: 'No se pudo conectar con la API de RLx.' });
        }
    };

    // --- Form Handlers ---
    sendForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            author: document.getElementById('author').value,
            text: document.getElementById('text').value,
            group_id: document.getElementById('group_id').value,
        };
        try {
            const response = await fetch(`${API_BASE}/chat/send`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await response.json();
            showResult(data);
            if (data.message_id) {
                deliveryMsgIdInput.value = data.message_id;
                renderMsgIdInput.value = data.message_id;
            }
        } catch (error) {
            showResult({ error: error.message });
        }
    });

    deliveryForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const messageId = deliveryMsgIdInput.value;
        const recipient = document.getElementById('recipient').value;
        if (!messageId || !recipient) return;
        try {
            const response = await fetch(`${API_BASE}/chat/delivery/${messageId}?recipient=${recipient}`);
            const data = await response.json();
            showResult(data);
        } catch (error) {
            showResult({ error: error.message });
        }
    });

    renderForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const messageId = renderMsgIdInput.value;
        const recipient = document.getElementById('render-recipient').value;
        const lang = document.getElementById('render-lang').value;
        if (!messageId || !recipient || !lang) return;
        try {
            const response = await fetch(`${API_BASE}/render/summary?message_id=${messageId}&recipient=${recipient}&lang=${lang}`);
            const data = await response.json();
            showResult(data);
        } catch (error) {
            showResult({ error: error.message });
        }
    });

    clearBtn.addEventListener('click', () => {
        resultBox.textContent = 'El resultado de la API aparecerá aquí...';
        deliveryMsgIdInput.value = '';
        renderMsgIdInput.value = '';
    });

    // --- Initial Load ---
    checkApiHealth();
});
