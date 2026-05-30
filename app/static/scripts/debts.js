import * as THREE from 'three';
import { ParametricGeometry } from 'three/addons/geometries/ParametricGeometry.js';

/* Fondo 3D */
const container = document.getElementById('bg-animation');

if (container) {
    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(
        45,
        window.innerWidth / window.innerHeight,
        0.1,
        100
    );

    camera.position.set(0, 0, 9);

    const renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true
    });

    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 1);
    container.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0xffffff, 0.32));

    const blueLight = new THREE.PointLight(0x00bfff, 2.4, 50);
    blueLight.position.set(5, 4, 5);
    scene.add(blueLight);

    const purpleLight = new THREE.PointLight(0x8a2be2, 2.1, 50);
    purpleLight.position.set(-5, -3, 4);
    scene.add(purpleLight);

    function mobius(u, v, target) {
        u = u * Math.PI * 2;
        v = (v - 0.5) * 1.1;

        const R = 2.5;

        const x = (R + v * Math.cos(u / 2)) * Math.cos(u);
        const y = (R + v * Math.cos(u / 2)) * Math.sin(u);
        const z = v * Math.sin(u / 2);

        target.set(x, y, z);
    }

    const geometry = new ParametricGeometry(mobius, 220, 30);

    const material = new THREE.MeshPhysicalMaterial({
        color: 0x00bfff,
        metalness: 0.35,
        roughness: 0.22,
        clearcoat: 1,
        clearcoatRoughness: 0.16,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.35
    });

    const mobiusMesh = new THREE.Mesh(geometry, material);
    mobiusMesh.rotation.x = 0.95;
    mobiusMesh.rotation.y = 0.3;
    scene.add(mobiusMesh);

    const wireframe = new THREE.Mesh(
        geometry,
        new THREE.MeshBasicMaterial({
            color: 0xffffff,
            wireframe: true,
            transparent: true,
            opacity: 0.08
        })
    );

    wireframe.rotation.copy(mobiusMesh.rotation);
    scene.add(wireframe);

    function animate() {
        requestAnimationFrame(animate);

        mobiusMesh.rotation.y += 0.004;
        mobiusMesh.rotation.x += 0.0016;

        wireframe.rotation.y += 0.004;
        wireframe.rotation.x += 0.0016;

        renderer.render(scene, camera);
    }

    animate();

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();

        renderer.setSize(window.innerWidth, window.innerHeight);
    });
}

/* Gráficos de deudas */
const groupsDebts = window.groupsDebts || [];

groupsDebts.forEach((group) => {
    const canvas = document.getElementById(`chart-group-${group.id}`);

    if (!canvas) return;

    const labels = group.items.map((item) => {
        if (item.is_debtor) {
            return `Debes a ${item.to_user_name}`;
        }

        if (item.is_creditor) {
            return `${item.from_user_name} te debe`;
        }

        return `${item.from_user_name} → ${item.to_user_name}`;
    });
    const data = group.items.map((item) => item.amount);

    new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [
                {
                    data,
                    borderWidth: 2,
                    borderColor: 'rgba(10, 10, 18, 0.95)',
                    backgroundColor: [
                        'rgba(0, 191, 255, 0.85)',
                        'rgba(138, 43, 226, 0.85)',
                        'rgba(221, 36, 118, 0.85)',
                        'rgba(255, 81, 47, 0.85)',
                        'rgba(255, 255, 255, 0.65)',
                        'rgba(90, 220, 180, 0.85)'
                    ]
                }
            ]
        },
        options: {
            responsive: true,
            cutout: '62%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.75)',
                        boxWidth: 12,
                        padding: 14
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const value = context.raw || 0;
                            return `${context.label}: ${value.toFixed(2)} €`;
                        }
                    }
                }
            }
        }
    });
});