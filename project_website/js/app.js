// Lenis smooth scrolling
const lenis = new Lenis({
    duration: 1.5,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    smooth: true, wheelMultiplier: 1,
});

lenis.on('scroll', ScrollTrigger.update);
gsap.ticker.add((time) => { lenis.raf(time * 1000); });
gsap.ticker.lagSmoothing(0);

// Smooth scroll for in-page hash links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const targetId = this.getAttribute('href');
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
            lenis.scrollTo(targetElement, {
                duration: 1.5,
                easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t))
            });
        }
    });
});

window.addEventListener("load", () => ScrollTrigger.refresh());

// Three.js background plane
const container = document.getElementById('canvas-container');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xFAF6EF);
scene.fog = new THREE.FogExp2(0xF5EFE6, 0.009);
const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, -15, 35);
camera.lookAt(0, 0, 0);

const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.12;
if (container) container.appendChild(renderer.domElement);

const ambientLight = new THREE.AmbientLight(0xfffaf5, 0.88);
scene.add(ambientLight);
const directionalLight = new THREE.DirectionalLight(0xffefd8, 0.62);
directionalLight.position.set(20, 20, 10);
scene.add(directionalLight);

const geometry = new THREE.PlaneGeometry(120, 120, 45, 45);
const material = new THREE.MeshStandardMaterial({
    color: 0xEDE6DC,
    emissive: 0xfffbf7,
    emissiveIntensity: 0.14,
    roughness: 0.42,
    metalness: 0.06,
    side: THREE.DoubleSide
});

const plane = new THREE.Mesh(geometry, material);
plane.rotation.x = -Math.PI / 2;
scene.add(plane);

const positions = geometry.attributes.position;
const clock = new THREE.Clock();

function animate3D() {
    requestAnimationFrame(animate3D);
    const time = clock.getElapsedTime() * 0.4;
    for (let i = 0; i < positions.count; i++) {
        const x = positions.getX(i); const y = positions.getY(i);
        const wave = Math.sin(x * 0.08 + time) * 1.5 + Math.cos(y * 0.08 + time) * 1.5;
        positions.setZ(i, wave);
    }
    positions.needsUpdate = true;
    geometry.computeVertexNormals();
    plane.rotation.z = time * 0.03;
    renderer.render(scene, camera);
}
animate3D();

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// Desktop magnetic hover on .magnetic targets
if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
    const hoverTargets = document.querySelectorAll('.hover-target');
    hoverTargets.forEach(target => {
        target.addEventListener('mouseleave', () => {
            if (target.classList.contains('magnetic')) {
                gsap.to(target, { x: 0, y: 0, duration: 0.5, ease: "power3.out" });
            }
        });

        if (target.classList.contains('magnetic')) {
            target.addEventListener('mousemove', (e) => {
                const rect = target.getBoundingClientRect();
                const relX = e.clientX - (rect.left + rect.width / 2);
                const relY = e.clientY - (rect.top + rect.height / 2);
                gsap.to(target, { x: relX * 0.3, y: relY * 0.3, duration: 0.3, ease: "power2.out" });
            });
        }
    });
}

gsap.registerPlugin(ScrollTrigger);

// Navbar glass / compact padding after scroll
window.addEventListener('scroll', () => {
    const nav = document.getElementById('navbar');
    if (!nav) return;
    if (window.scrollY > 50) {
        nav.classList.add('glass-light', 'py-4', 'md:py-4');
        nav.classList.remove('py-6', 'md:py-8', 'border-transparent');
    } else {
        nav.classList.remove('glass-light', 'py-4', 'md:py-4');
        nav.classList.add('py-6', 'md:py-8');
    }
});

// Hero headline and fade-in lines
const tl = gsap.timeline();
tl.to(".hero-line", { y: 0, duration: 1.2, stagger: 0.1, ease: "power4.out", delay: 0.2 })
    .from(".hero-fade", { y: 20, opacity: 0, duration: 1, stagger: 0.1, ease: "power3.out" }, "-=0.8");

// --- Desktop: polaroid scroll parallax (overview) ---
if (window.innerWidth > 768) {
    const polaroids = ['.p1', '.p2', '.p3', '.p4'];
    polaroids.forEach((p, index) => {
        const el = document.querySelector(p);
        if (!el) return;
        const img = el.querySelector('.para-img');
        const xOffset = index % 2 === 0 ? -150 : 150;
        const rot = index % 2 === 0 ? -15 : 15;

        gsap.fromTo(el,
            { x: xOffset, y: 150, rotation: rot, opacity: 0 },
            {
                x: 0, y: 0, rotation: index === 0 ? -6 : (index === 1 ? 12 : (index === 2 ? 3 : -6)),
                opacity: 1, duration: 1.5, ease: "power3.out",
                scrollTrigger: { trigger: "#overview", start: "top 70%", end: "center center", scrub: 1 }
            }
        );

        if (img) {
            gsap.to(img, {
                y: "10%", ease: "none",
                scrollTrigger: { trigger: "#overview", start: "top bottom", end: "bottom top", scrub: true }
            });
        }
    });
}

// --- Mobile: polaroid strip entrance ---
if (window.innerWidth <= 768) {
    gsap.from(".polaroid-mob", {
        scrollTrigger: { trigger: ".polaroid-mobile-container", start: "top 85%" },
        y: 60, opacity: 0, duration: 1, stagger: 0.15, ease: "power3.out"
    });
}

// Section titles, tech cards, footer reveal on scroll
gsap.utils.toArray('.section-title').forEach(title => {
    gsap.from(title, {
        scrollTrigger: { trigger: title, start: "top 85%" },
        y: 40, opacity: 0, duration: 1.2, ease: "power3.out"
    });
});

gsap.utils.toArray(".tech-card").forEach((card, i) => {
    gsap.from(card, {
        scrollTrigger: {
            trigger: card,
            start: "top 90%",
            toggleActions: "play none none none",
            fastScrollEnd: true,
        },
        y: 56,
        opacity: 0,
        duration: 1,
        delay: i * 0.07,
        ease: "power3.out",
    });
});

gsap.from(".footer-elem", {
    scrollTrigger: {
        trigger: "#about",
        start: "top 85%"
    },
    y: 40,
    opacity: 0,
    duration: 1.2,
    stagger: 0.15,
    ease: "power3.out"
});

const garments = gsap.utils.toArray('.garment-item');
const featurePanels = gsap.utils.toArray('.feature-panel');
let currentActiveIndex = 0;

function updateCloset(activeIndex, isInitial = false) {
    currentActiveIndex = activeIndex;
    const isMobile = window.innerWidth < 1024;
    const vw = Math.min(window.innerWidth || 390, 430);
    const pushOffset = isMobile ? Math.min(88, Math.round(vw * 0.2)) : 320;
    const stackGap = isMobile ? Math.min(28, Math.round(vw * 0.065)) : 70;

    const centerScale = isMobile ? 1.06 : 1.15;
    const sideScale = isMobile ? 0.82 : 0.85;

    garments.forEach((garment, i) => {
        let xPos = 0;
        let scale = sideScale;
        let rot = 0;
        let z = 10;
        let cardOpacity = 0.5;
        let blur = "blur(4px)";

        if (i === activeIndex) {
            xPos = 0;
            scale = centerScale;
            rot = 0;
            z = 50;
            cardOpacity = 1;
            blur = "blur(0px)";
        } else if (i < activeIndex) {
            const diff = i - activeIndex;
            xPos = -pushOffset + (diff * stackGap);
            rot = -3 + diff;
            z = 20 + i;
        } else {
            const diff = i - activeIndex;
            xPos = pushOffset + (diff * stackGap);
            rot = 3 + diff;
            z = 20 - i;
        }

        const hook = garment.querySelector(".garment-hook");
        const crossbar = garment.querySelector(".garment-crossbar");
        const card = garment.querySelector(".garment-card");
        const t = { duration: isInitial ? 1 : 0.8, ease: "power3.out", overwrite: "auto" };

        gsap.to(garment, {
            x: xPos,
            scale: scale,
            rotation: rot,
            zIndex: z,
            opacity: 1,
            filter: "none",
            ...t
        });
        if (hook) {
            gsap.to(hook, { opacity: cardOpacity, filter: blur, ...t });
        }
        if (crossbar) {
            gsap.to(crossbar, { opacity: 1, filter: "none", ...t });
        }
        if (card) {
            gsap.to(card, { opacity: cardOpacity, filter: blur, ...t });
        }
    });

    featurePanels.forEach((panel, i) => {
        if (i === activeIndex) {
            gsap.to(panel, { opacity: 1, y: 0, pointerEvents: "auto", duration: 0.6, ease: "power2.out", delay: 0.2 });
        } else {
            gsap.to(panel, { opacity: 0, y: 20, pointerEvents: "none", duration: 0.4, ease: "power2.in" });
        }
    });
}

garments.forEach((g, i) => {
    g.addEventListener('click', () => {
        if (currentActiveIndex !== i) updateCloset(i);
    });
});

ScrollTrigger.create({
    trigger: "#features",
    start: "top 60%",
    once: true,
    onEnter: () => {
        gsap.from(garments, {
            y: -150,
            opacity: 0,
            rotation: () => -15 + Math.random() * 30,
            stagger: 0.1,
            duration: 1.2,
            ease: "elastic.out(1, 0.6)",
            onComplete: () => updateCloset(0, true)
        });
    }
});

// Mobile hamburger drawer menu
const menuBtn = document.getElementById('menu-toggle');
const mobileMenu = document.getElementById('mobile-menu');
const mobileOverlay = document.getElementById('mobile-overlay');
const menuLinksContainer = document.getElementById('mobile-menu-links');
const line1 = document.getElementById('line1');
const line2 = document.getElementById('line2');
let isMenuOpen = false;

function toggleMenu() {
    isMenuOpen = !isMenuOpen;
    if (isMenuOpen) {
        mobileOverlay.classList.remove('opacity-0', 'pointer-events-none');
        mobileOverlay.classList.add('opacity-100', 'pointer-events-auto');

        mobileMenu.classList.remove('pointer-events-none');
        mobileMenu.classList.add('pointer-events-auto');

        mobileMenu.classList.remove('translate-x-full');
        mobileMenu.classList.add('translate-x-0', 'shadow-2xl');

        menuLinksContainer.classList.remove('opacity-0');

        line1.classList.add('rotate-45', 'translate-y-[2.5px]');
        line2.classList.add('-rotate-45', '-translate-y-[4px]');
    } else {
        mobileOverlay.classList.add('opacity-0', 'pointer-events-none');
        mobileOverlay.classList.remove('opacity-100', 'pointer-events-auto');

        mobileMenu.classList.add('pointer-events-none');
        mobileMenu.classList.remove('pointer-events-auto');

        mobileMenu.classList.add('translate-x-full');
        mobileMenu.classList.remove('translate-x-0', 'shadow-2xl');

        menuLinksContainer.classList.add('opacity-0');

        line1.classList.remove('rotate-45', 'translate-y-[2.5px]');
        line2.classList.remove('-rotate-45', '-translate-y-[4px]');
    }
}

if (menuBtn) menuBtn.addEventListener('click', toggleMenu);
if (mobileOverlay) mobileOverlay.addEventListener('click', toggleMenu);

document.querySelectorAll('.mobile-link').forEach(link => {
    link.addEventListener('click', () => {
        if (isMenuOpen) toggleMenu();
    });
});

const siteLogo = document.getElementById('site-logo');
const scrollEase = (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t));
function scrollToPageTop() {
    if (isMenuOpen) toggleMenu();
    lenis.scrollTo(0, { duration: 1.5, easing: scrollEase });
}
if (siteLogo) {
    siteLogo.addEventListener('click', () => scrollToPageTop());
    siteLogo.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            scrollToPageTop();
        }
    });
}

let touchStartX = 0;
let touchEndX = 0;
const rackContainer = document.getElementById('clothing-rack');
if (rackContainer) {
    rackContainer.addEventListener('touchstart', e => {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });
    rackContainer.addEventListener('touchend', e => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }, { passive: true });
}

function handleSwipe() {
    const swipeThreshold = 40;

    if (touchEndX < touchStartX - swipeThreshold) {
        if (currentActiveIndex < garments.length - 1) {
            updateCloset(currentActiveIndex + 1);
        }
    }
    if (touchEndX > touchStartX + swipeThreshold) {
        if (currentActiveIndex > 0) {
            updateCloset(currentActiveIndex - 1);
        }
    }
}

let closetResizeTimer;
window.addEventListener('resize', () => {
    clearTimeout(closetResizeTimer);
    closetResizeTimer = setTimeout(() => {
        updateCloset(currentActiveIndex, true);
        ScrollTrigger.refresh();
    }, 120);
});
