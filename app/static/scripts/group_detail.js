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

camera.position.set(0, 0, 9);

const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true
});

renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setClearColor(0x000000, 1);

container.appendChild(renderer.domElement);

const ambientLight = new THREE.AmbientLight(0xffffff, 0.34);
scene.add(ambientLight);

const blueLight = new THREE.PointLight(0x00bfff, 2.6, 50);
blueLight.position.set(5, 4, 5);
scene.add(blueLight);

const purpleLight = new THREE.PointLight(0x8a2be2, 2.2, 50);
purpleLight.position.set(-5, -3, 4);
scene.add(purpleLight);

const pinkLight = new THREE.PointLight(0xff2d75, 1.7, 50);
pinkLight.position.set(0, 4, -4);
scene.add(pinkLight);

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
    opacity: 0.42
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
        opacity: 0.09
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

let selectedExpense = null;

const expenseModal = document.getElementById('expenseModal');

if (expenseModal) {
    expenseModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;

        selectedExpense = {
            id: button.getAttribute('data-id'),
            name: button.getAttribute('data-name'),
            amount: button.getAttribute('data-amount'),
            date: button.getAttribute('data-date'),
            paidBy: button.getAttribute('data-paid-by'),
            paidById: button.getAttribute('data-paid-by-id'),
            googleApi: button.getAttribute('data-google-api') || ''
        };

        document.getElementById('modalExpenseName').textContent = selectedExpense.name;
        document.getElementById('modalExpenseAmount').textContent = `Cantidad: ${selectedExpense.amount} €`;
        document.getElementById('modalExpensePaidBy').textContent = `Pagado por: ${selectedExpense.paidBy}`;
        document.getElementById('modalExpenseDate').textContent = `Fecha: ${selectedExpense.date}`;
    });
}

const editExpenseBtn = document.getElementById('modalExpenseEditBtn');
const createExpenseModalElement = document.getElementById('createExpenseModal');

if (editExpenseBtn && createExpenseModalElement) {
    editExpenseBtn.addEventListener('click', async () => {
        if (!selectedExpense) return;

        const detailModalInstance = bootstrap.Modal.getInstance(expenseModal);
        detailModalInstance.hide();

        await fillExpenseForm(selectedExpense);

        const createModalInstance = new bootstrap.Modal(createExpenseModalElement);

        expenseModal.addEventListener('hidden.bs.modal', function openEditModalOnce() {
            createModalInstance.show();
            expenseModal.removeEventListener('hidden.bs.modal', openEditModalOnce);
        });
    });
}

async function fillExpenseForm(expense) {
    document.getElementById('expenseIdInput').value = expense.id;
    document.getElementById('expenseNameInput').value = expense.name;
    document.getElementById('expenseAmountInput').value = expense.amount;
    document.getElementById('expensePaidByInput').value = expense.paidById;
    document.getElementById('expenseGoogleApiInput').value = expense.googleApi;

    document.getElementById('expenseDateInput').value = formatDateForDatetimeLocal(expense.date);

    const title = document.getElementById('createExpenseModalLabel');
    if (title) {
        title.textContent = 'Editar gasto';
    }

    const submitBtn = document.querySelector('#createExpenseModal button[type="submit"]');
    if (submitBtn) {
        submitBtn.innerHTML = '<i class="bi bi-check-circle"></i> Guardar cambios';
    }

    try {
        const response = await fetch(`/expense/${expense.id}/shared-users`);
        const data = await response.json();

        const sharedUsers = data.users.map(String);

        document.querySelectorAll('input[name="shared_users"]').forEach((checkbox) => {
            checkbox.checked = sharedUsers.includes(checkbox.value);
        });
    } catch (error) {
        console.error('Error cargando integrantes del gasto:', error);
    }
    updateSplitPreview();
}

function formatDateForDatetimeLocal(dateValue) {
    if (!dateValue) return '';

    /*
        MySQL puede venir como:
        2026-04-01 10:00:00
        o como:
        Tue, 01 Apr 2026 10:00:00 GMT
    */

    if (dateValue.includes(' ')) {
        return dateValue.replace(' ', 'T').slice(0, 16);
    }

    const date = new Date(dateValue);

    if (Number.isNaN(date.getTime())) {
        return '';
    }

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');

    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

const amountInput = document.getElementById('expenseAmountInput');
const splitPreviewText = document.getElementById('splitPreviewText');
const selectAllButton = document.getElementById('selectAllMembers');
const memberCheckboxes = document.querySelectorAll('input[name="shared_users"]');

function updateSplitPreview() {
    if (!amountInput || !splitPreviewText) return;

    const amount = parseFloat(amountInput.value);
    const selectedMembers = document.querySelectorAll('input[name="shared_users"]:checked');
    const selectedCount = selectedMembers.length;

    if (!amount || amount <= 0) {
        splitPreviewText.textContent = 'Introduce una cantidad para calcular el reparto.';
        return;
    }

    if (selectedCount === 0) {
        splitPreviewText.textContent = 'Selecciona al menos un integrante.';
        return;
    }

    const amountPerPerson = amount / selectedCount;

    splitPreviewText.textContent =
        `${selectedCount} integrante(s): ${amountPerPerson.toFixed(2)} € por persona.`;
}

if (amountInput) {
    amountInput.addEventListener('input', updateSplitPreview);
}

memberCheckboxes.forEach((checkbox) => {
    checkbox.addEventListener('change', updateSplitPreview);
});

if (selectAllButton) {
    selectAllButton.addEventListener('click', () => {
        const checkboxes = document.querySelectorAll('input[name="shared_users"]');
        const allChecked = Array.from(checkboxes).every((checkbox) => checkbox.checked);

        checkboxes.forEach((checkbox) => {
            checkbox.checked = !allChecked;
        });

        selectAllButton.textContent = allChecked ? 'Seleccionar todos' : 'Deseleccionar todos';

        updateSplitPreview();
    });
}

updateSplitPreview();
const openCreateExpenseBtn = document.getElementById('openCreateExpenseBtn');

if (openCreateExpenseBtn) {
    openCreateExpenseBtn.addEventListener('click', () => {
        resetExpenseForm();
    });
}

function resetExpenseForm() {
    const form = document.getElementById('expenseForm');

    if (form) {
        form.reset();
    }

    const expenseIdInput = document.getElementById('expenseIdInput');

    if (expenseIdInput) {
        expenseIdInput.value = '';
    }

    document.querySelectorAll('input[name="shared_users"]').forEach((checkbox) => {
        checkbox.checked = true;
    });

    const title = document.getElementById('createExpenseModalLabel');

    if (title) {
        title.textContent = 'Crear nuevo gasto';
    }

    const submitBtn = document.querySelector('#createExpenseModal button[type="submit"]');

    if (submitBtn) {
        submitBtn.innerHTML = '<i class="bi bi-check-circle"></i> Guardar gasto';
    }

    updateSplitPreview();
}