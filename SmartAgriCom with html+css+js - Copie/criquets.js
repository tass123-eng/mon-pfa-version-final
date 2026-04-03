// ===== STATE MANAGEMENT ===== 

const appState = {
    isDetectionActive: false,
    stream: null,
    cricketCount: 0
};

// ===== INITIALIZATION ===== 

document.addEventListener('DOMContentLoaded', function() {
    initializeButtons();
});

// ===== BUTTON INITIALIZATION ===== 

function initializeButtons() {
    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');
    const btnTestGreen = document.getElementById('btn-test-green');
    const btnTestRed = document.getElementById('btn-test-red');
    const modalClose = document.getElementById('modal-close');
    const btnOk = document.getElementById('btn-ok');

    if (btnStart) {
        btnStart.addEventListener('click', startAnalysis);
    }

    if (btnStop) {
        btnStop.addEventListener('click', stopAnalysis);
    }

    if (btnTestGreen) {
        btnTestGreen.addEventListener('click', testGreenLED);
    }

    if (btnTestRed) {
        btnTestRed.addEventListener('click', testRedLED);
    }

    if (modalClose) {
        modalClose.addEventListener('click', closeModal);
    }

    if (btnOk) {
        btnOk.addEventListener('click', closeModal);
    }
}

// ===== ANALYSIS FUNCTIONS ===== 

function startAnalysis() {
    appState.isDetectionActive = true;
    
    // Toggle buttons
    document.getElementById('btn-start').classList.add('hidden');
    document.getElementById('btn-stop').classList.remove('hidden');
    
    // Show camera section
    document.getElementById('camera-section').classList.remove('hidden');
    
    // Update detection status
    updateDetectionStatus('Accès à la caméra en cours...');
    
    // Request camera access
    requestCameraAccess();
}

function stopAnalysis() {
    appState.isDetectionActive = false;
    
    // Toggle buttons
    document.getElementById('btn-start').classList.remove('hidden');
    document.getElementById('btn-stop').classList.add('hidden');
    
    // Hide camera section
    document.getElementById('camera-section').classList.add('hidden');
    
    // Stop camera stream
    if (appState.stream) {
        appState.stream.getTracks().forEach(track => track.stop());
        appState.stream = null;
    }
    
    // Reset count
    appState.cricketCount = 0;
    document.getElementById('crickets-count').textContent = '0';
}

// ===== CAMERA FUNCTIONS ===== 

function requestCameraAccess() {
    const video = document.getElementById('camera-video');
    const constraints = {
        video: {
            width: { ideal: 640 },
            height: { ideal: 480 }
        },
        audio: false
    };

    navigator.mediaDevices.getUserMedia(constraints)
        .then(stream => {
            appState.stream = stream;
            video.srcObject = stream;
            video.onloadedmetadata = () => {
                video.play();
                updateDetectionStatus('✅ Caméra active - Analyse en cours...');
                startDetectionSimulation();
            };
        })
        .catch(error => {
            console.error('Erreur d\'accès à la caméra:', error);
            stopAnalysis();
            showErrorModal(error);
        });
}

function startDetectionSimulation() {
    // Simulate cricket detection every 3-7 seconds
    const detectionInterval = setInterval(() => {
        if (!appState.isDetectionActive) {
            clearInterval(detectionInterval);
            return;
        }

        // Random detection
        const random = Math.random();
        if (random > 0.3) {
            // 70% chance to detect something
            appState.cricketCount++;
            document.getElementById('crickets-count').textContent = appState.cricketCount;
            
            updateDetectionStatus(`🟢 Criquet #${appState.cricketCount} détecté! Confiance: ${Math.floor(Math.random() * 30 + 70)}%`);
        } else {
            updateDetectionStatus('⏳ Analyse en cours... en attente de détection');
        }
    }, Math.random() * 4000 + 3000);
}

function updateDetectionStatus(message) {
    const statusElement = document.getElementById('detection-status');
    if (statusElement) {
        statusElement.textContent = message;
    }
}

// ===== LED TEST FUNCTIONS ===== 

function testGreenLED() {
    showNotification('🟢 LED verte activée pendant 2 secondes', 'success');
    
    // Simulate LED activation
    const btn = document.getElementById('btn-test-green');
    btn.style.opacity = '0.7';
    btn.disabled = true;
    
    setTimeout(() => {
        btn.style.opacity = '1';
        btn.disabled = false;
        showNotification('✅ LED verte désactivée', 'info');
    }, 2000);
}

function testRedLED() {
    showNotification('🔴 LED rouge activée pendant 2 secondes', 'danger');
    
    // Simulate LED activation
    const btn = document.getElementById('btn-test-red');
    btn.style.opacity = '0.7';
    btn.disabled = true;
    
    setTimeout(() => {
        btn.style.opacity = '1';
        btn.disabled = false;
        showNotification('✅ LED rouge désactivée', 'info');
    }, 2000);
}

// ===== MODAL FUNCTIONS ===== 

function showErrorModal(error) {
    const modal = document.getElementById('error-modal');
    const message = document.getElementById('error-message');
    
    let errorMsg = 'Une erreur s\'est produite lors de l\'accès à la caméra.';
    
    if (error.name === 'NotAllowedError') {
        errorMsg = 'L\'accès à la caméra a été refusé. Veuillez autoriser l\'accès à la caméra dans les paramètres du navigateur.';
    } else if (error.name === 'NotFoundError') {
        errorMsg = 'Aucune caméra détectée sur votre appareil.';
    } else if (error.name === 'NotReadableError') {
        errorMsg = 'La caméra est déjà utilisée par une autre application.';
    }
    
    message.textContent = errorMsg;
    modal.classList.remove('hidden');
}

function closeModal() {
    const modal = document.getElementById('error-modal');
    modal.classList.add('hidden');
}

// ===== NOTIFICATION FUNCTION ===== 

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#4caf50' : type === 'danger' ? '#f44336' : '#2196F3'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 5px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        z-index: 2000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// ===== ANIMATION STYLES ===== 

const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);