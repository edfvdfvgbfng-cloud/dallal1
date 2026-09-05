(function () {
  'use strict';

  // Mobile nav
  const toggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');
  if (toggle && navLinks) {
    toggle.addEventListener('click', () => navLinks.classList.toggle('open'));
  }

  // Auto-dismiss alerts - commented out to prevent premature disappearance
  // document.querySelectorAll('.alert').forEach((el) => {
  //   setTimeout(() => {
  //     el.style.opacity = '0';
  //     el.style.transform = 'translateY(-8px)';
  //     setTimeout(() => el.remove(), 300);
  //   }, 5000);
  // });

  // Active nav link
  const path = window.location.pathname;
  document.querySelectorAll('.nav-links a').forEach((a) => {
    if (a.getAttribute('href') === path) a.classList.add('active');
  });

  // Image gallery
  const gallery = document.querySelector('.gallery');
  if (gallery) {
    const mainImg = gallery.querySelector('.gallery-main img');
    const thumbs = gallery.querySelectorAll('.gallery-thumbs img');
    const prev = gallery.querySelector('.gallery-nav.prev');
    const next = gallery.querySelector('.gallery-nav.next');
    let idx = 0;
    const urls = Array.from(thumbs).map((t) => t.dataset.full || t.src);

    function show(i) {
      idx = (i + urls.length) % urls.length;
      if (mainImg) mainImg.src = urls[idx];
      thumbs.forEach((t, j) => t.classList.toggle('active', j === idx));
    }

    thumbs.forEach((t, i) => t.addEventListener('click', () => show(i)));
    if (prev) prev.addEventListener('click', () => show(idx - 1));
    if (next) next.addEventListener('click', () => show(idx + 1));
    show(0);
  }

  // Dashboard tabs
  document.querySelectorAll('[data-tab]').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      // Prevent default behavior for anchor tags
      if (btn.tagName === 'A') {
        e.preventDefault();
      }

      const tab = btn.dataset.tab;
      console.log('Tab clicked:', tab);

      // Remove active class from all tab buttons
      document.querySelectorAll('[data-tab]').forEach((b) => b.classList.remove('active'));

      // Remove active class from all panels
      document.querySelectorAll('.panel').forEach((p) => p.classList.remove('active'));

      // Add active class to clicked button
      btn.classList.add('active');

      // Find and activate the corresponding panel
      const panel = document.getElementById('panel-' + tab);
      if (panel) {
        panel.classList.add('active');
        console.log('Panel activated:', 'panel-' + tab);
      } else {
        console.warn('Panel not found:', 'panel-' + tab);
        // If panel doesn't exist, keep the properties panel active as fallback
        const propertiesPanel = document.getElementById('panel-properties');
        if (propertiesPanel) {
          propertiesPanel.classList.add('active');
        }
      }
    });
  });

  // Province -> city datalist
  const provinceSelect = document.getElementById('id_province');
  const cityInput = document.getElementById('id_city');
  const citiesData = window.GOVERNORATE_CITIES || {};

  function updateCities() {
    if (!provinceSelect || !cityInput) return;
    const list = document.getElementById('city-list');
    if (!list) return;
    list.innerHTML = '';
    const cities = citiesData[provinceSelect.value] || [];
    cities.forEach((c) => {
      const opt = document.createElement('option');
      opt.value = c;
      list.appendChild(opt);
    });
  }

  if (provinceSelect) {
    provinceSelect.addEventListener('change', updateCities);
    updateCities();
  }

  // Leaflet map
  const mapEl = document.getElementById('property-map');
  if (mapEl && typeof L !== 'undefined') {
    const lat = parseFloat(mapEl.dataset.lat);
    const lng = parseFloat(mapEl.dataset.lng);
    if (!isNaN(lat) && !isNaN(lng)) {
      const map = L.map('property-map').setView([lat, lng], 15);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap',
      }).addTo(map);
      L.marker([lat, lng]).addTo(map);
    }
  }
})();
