import * as THREE from 'three';
import { ParametricGeometry } from 'three/addons/geometries/ParametricGeometry.js';

const container = document.getElementById('bg-animation');

if (!container) {
    console.error('No existe el div #bg-animation');
}

const scene = new THREE.Scene();

const camera = new THREE.PerspectiveCamera(
    45,
    window.innerWidth / window.innerHeight,
    0.1,
    100
);
camera.position.set(0, 0, 8);

const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true
});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setClearColor(0x000000, 1);
container.appendChild(renderer.domElement);

// Luces
const ambientLight = new THREE.AmbientLight(0xffffff, 0.45);
scene.add(ambientLight);

const pointLight1 = new THREE.PointLight(0x8a2be2, 2.5, 50);
pointLight1.position.set(5, 5, 5);
scene.add(pointLight1);

const pointLight2 = new THREE.PointLight(0x00bfff, 2.2, 50);
pointLight2.position.set(-5, -3, 4);
scene.add(pointLight2);

const pointLight3 = new THREE.PointLight(0xff2d75, 1.8, 50);
pointLight3.position.set(0, 4, -4);
scene.add(pointLight3);

// Función paramétrica de la cinta de Möbius
function mobius(u, v, target) {
    u = u * Math.PI * 2;
    v = (v - 0.5) * 1.2;

    const R = 2.1;

    const x = (R + v * Math.cos(u / 2)) * Math.cos(u);
    const y = (R + v * Math.cos(u / 2)) * Math.sin(u);
    const z = v * Math.sin(u / 2);

    target.set(x, y, z);
}

const mobiusGeometry = new ParametricGeometry(mobius, 220, 30);

const mobiusMaterial = new THREE.MeshPhysicalMaterial({
    color: 0x8a2be2,
    metalness: 0.25,
    roughness: 0.2,
    clearcoat: 1,
    clearcoatRoughness: 0.15,
    transmission: 0.15,
    side: THREE.DoubleSide
});

const mobiusMesh = new THREE.Mesh(mobiusGeometry, mobiusMaterial);
mobiusMesh.rotation.x = 0.8;
mobiusMesh.rotation.y = 0.2;
scene.add(mobiusMesh);

// Malla tipo wireframe para darle más estilo
const wireframe = new THREE.Mesh(
    mobiusGeometry,
    new THREE.MeshBasicMaterial({
        color: 0xffffff,
        wireframe: true,
        transparent: true,
        opacity: 0.18
    })
);
wireframe.rotation.copy(mobiusMesh.rotation);
scene.add(wireframe);

// Partículas suaves de fondo (opcional)
const particlesCount = 250;
const particlesGeometry = new THREE.BufferGeometry();
const positions = new Float32Array(particlesCount * 3);

for (let i = 0; i < particlesCount; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 22;
    positions[i * 3 + 1] = (Math.random() - 0.5) * 22;
    positions[i * 3 + 2] = (Math.random() - 0.5) * 22;
}

particlesGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

const particlesMaterial = new THREE.PointsMaterial({
    color: 0xffffff,
    size: 0.03,
    transparent: true,
    opacity: 0.5
});

const particles = new THREE.Points(particlesGeometry, particlesMaterial);
scene.add(particles);

// Animación
function animate() {
    requestAnimationFrame(animate);

    mobiusMesh.rotation.y += 0.008;
    mobiusMesh.rotation.x += 0.003;

    wireframe.rotation.y += 0.008;
    wireframe.rotation.x += 0.003;

    particles.rotation.y += 0.0008;

    renderer.render(scene, camera);
}

animate();

// Responsive
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});