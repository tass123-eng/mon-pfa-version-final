// ===== INIT GLOBAL =====
document.addEventListener('DOMContentLoaded', function () {
    initCarousel();
    setupNavigation();
});

// ===== CAROUSEL STATE =====
const carouselState = {
    currentIndex: 0,
    itemsPerView: 3,
    maxIndex: 0,
    autoRotateInterval: null
};

// ===== INIT CAROUSEL =====
function initCarousel() {
    const prevBtn = document.getElementById('carousel-prev');
    const nextBtn = document.getElementById('carousel-next');
    const viewport = document.querySelector('.viewport');
    const slides = document.querySelectorAll('.slide');

    if (!slides.length) return;

    updateCarouselConfig();

    if (prevBtn) prevBtn.addEventListener('click', goToPrevious);
    if (nextBtn) nextBtn.addEventListener('click', goToNext);

    if (viewport) {
        viewport.addEventListener('mouseenter', stopAutoRotate);
        viewport.addEventListener('mouseleave', startAutoRotate);
    }

    window.addEventListener('resize', () => {
        updateCarouselConfig();
        updateCarousel();
    });

    updateCarousel();
    startAutoRotate();
}

// ===== RESPONSIVE =====
function updateCarouselConfig() {
    const slides = document.querySelectorAll('.slide');

    if (window.innerWidth <= 768) {
        carouselState.itemsPerView = 1;
    } else if (window.innerWidth <= 1024) {
        carouselState.itemsPerView = 2;
    } else {
        carouselState.itemsPerView = 3;
    }

    carouselState.maxIndex = Math.max(0, slides.length - carouselState.itemsPerView);

    if (carouselState.currentIndex > carouselState.maxIndex) {
        carouselState.currentIndex = carouselState.maxIndex;
    }
}

// ===== UPDATE POSITION =====
function updateCarousel() {
    const track = document.getElementById('carousel-track');
    const slides = document.querySelectorAll('.slide');

    if (!track || !slides.length) return;

    const slideWidth = slides[0].offsetWidth;
    const gap = parseFloat(window.getComputedStyle(track).gap) || 0;
    const offset = carouselState.currentIndex * (slideWidth + gap);

    track.style.transform = `translateX(-${offset}px)`;
}

// ===== NAVIGATION =====
function goToPrevious() {
    if (carouselState.currentIndex <= 0) {
        carouselState.currentIndex = carouselState.maxIndex;
    } else {
        carouselState.currentIndex--;
    }
    updateCarousel();
    restartAutoRotate();
}

function goToNext() {
    if (carouselState.currentIndex >= carouselState.maxIndex) {
        carouselState.currentIndex = 0;
    } else {
        carouselState.currentIndex++;
    }
    updateCarousel();
    restartAutoRotate();
}

// ===== AUTO ROTATION =====
function startAutoRotate() {
    stopAutoRotate();
    carouselState.autoRotateInterval = setInterval(() => {
        goToNext();
    }, 5000);
}

function stopAutoRotate() {
    if (carouselState.autoRotateInterval) {
        clearInterval(carouselState.autoRotateInterval);
        carouselState.autoRotateInterval = null;
    }
}

function restartAutoRotate() {
    startAutoRotate();
}

// ===== NAVIGATION ACTIVE LINK =====
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const currentPage = window.location.pathname;

    navLinks.forEach(link => {
        if (
            link.getAttribute('href') === currentPage ||
            (currentPage.includes(link.getAttribute('href').replace('.html', '')) &&
                link.getAttribute('href') !== 'index.html')
        ) {
            link.classList.add('active');
        }
    });
}

// ===== LED FUNCTIONS =====
function testGreenLED() {
    alert('🟢 LED verte activée pendant 2 secondes');
}

function testRedLED() {
    alert('🔴 LED rouge activée pendant 2 secondes');
}

// ===== ANALYSIS =====
function startAnalysis() {
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = '⏳ Analyse en cours...';

    alert('📹 Accès à la caméra demandé');

    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                setTimeout(() => {
                    stream.getTracks().forEach(track => track.stop());
                    btn.disabled = false;
                    btn.textContent = '▶ Démarrer Analyse';
                    alert('✅ Analyse terminée!');
                }, 5000);
            })
            .catch(() => {
                btn.disabled = false;
                btn.textContent = '▶ Démarrer Analyse';
                alert('❌ Accès caméra refusé');
            });
    }
}

// ===== CONTACT =====
function sendContact(event) {
    event.preventDefault();

    const name = document.getElementById('name').value;

    if (name) {
        alert(`✅ Merci ${name}, message envoyé`);
        event.target.reset();
    } else {
        alert('❌ Remplir tous les champs');
    }
}