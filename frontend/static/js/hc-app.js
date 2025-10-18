/**
 * HauteCarat - Single Page Application
 * Complete, fixed hc-app.js
 * - Uses your backend API at Azure Container Apps
 * - Removes placeholder/simulate flow
 * - Renders generated image from backend image_url
 * - Download button uses direct SAS link (no CORS needed)
 */

/* =========================
   GLOBAL STATE
========================= */
const AppState = {
    currentPage: 'login',
    selectedCategory: '',
    selectedFiles: [],
    isAuthenticated: false,
    generatedImageUrl: null
  };
  
  /* =========================
     NAVIGATION
  ========================= */
  function showPage(pageName) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const el = document.getElementById(`${pageName}-page`);
    if (el) {
      el.classList.add('active');
      AppState.currentPage = pageName;
    }
  }
  
  /* =========================
     ALERTS
  ========================= */
  function showAlert(message, type = 'error', containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
  
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
  
    container.innerHTML = '';
    container.appendChild(alertDiv);
  
    setTimeout(() => alertDiv.remove(), 5000);
  }
  
  /* =========================
     LOGIN
  ========================= */
  function initLoginPage() {
    const loginForm = document.getElementById('login-form');
    const loginBtn = document.getElementById('login-btn');
  
    loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
  
      const email = document.getElementById('email').value.trim();
      const password = document.getElementById('password').value;
  
      const VALID_EMAIL = 'abdul.mazin@gmail.com';
      const VALID_PASSWORD = 'HauteCarat@2024!';
  
      loginBtn.disabled = true;
      loginBtn.textContent = 'Signing In...';
  
      setTimeout(() => {
        if (email === VALID_EMAIL && password === VALID_PASSWORD) {
          AppState.isAuthenticated = true;
          showAlert('Login successful!', 'success', 'login-alert');
          setTimeout(() => showPage('category'), 800);
        } else {
          showAlert('Invalid email or password', 'error', 'login-alert');
          loginBtn.disabled = false;
          loginBtn.textContent = 'Sign In';
        }
      }, 500);
    });
  }
  
  /* =========================
     CATEGORY
  ========================= */
  function initCategoryPage() {
    const categoryCards = document.querySelectorAll('.category-card');
    const logoutBtn1 = document.getElementById('logout-btn-1');
  
    categoryCards.forEach(card => {
      card.addEventListener('click', () => {
        const category = card.getAttribute('data-category');
        AppState.selectedCategory = category;
        document.getElementById('category-title').textContent = `${category} Details`;
        showPage('details');
      });
    });
  
    logoutBtn1.addEventListener('click', (e) => {
      e.preventDefault();
      handleLogout();
    });
  }
  
  /* =========================
     DETAILS / GENERATION
  ========================= */
  function initDetailsPage() {
    const imageUpload = document.getElementById('image-upload');
    const uploadArea = document.getElementById('upload-area');
    const previewGrid = document.getElementById('preview-grid');
    const jewelryForm = document.getElementById('jewelry-form');
    const generateBtn = document.getElementById('generate-btn');
    const backBtn = document.getElementById('back-btn');
    const logoutBtn2 = document.getElementById('logout-btn-2');
    const downloadBtn = document.getElementById('download-btn');
  
    // Click-to-upload
    uploadArea.addEventListener('click', () => imageUpload.click());
  
    // Drag & drop styling
    uploadArea.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadArea.style.borderColor = 'var(--primary-black)';
    });
    uploadArea.addEventListener('dragleave', () => {
      uploadArea.style.borderColor = 'var(--border-color)';
    });
    uploadArea.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadArea.style.borderColor = 'var(--border-color)';
      handleFileSelection(Array.from(e.dataTransfer.files));
    });
  
    // File input change
    imageUpload.addEventListener('change', (e) => {
      handleFileSelection(Array.from(e.target.files));
    });
  
    function handleFileSelection(files) {
      const newFiles = [...AppState.selectedFiles, ...files];
  
      if (newFiles.length > 3) {
        showAlert(`Maximum 3 images allowed. You can add ${3 - AppState.selectedFiles.length} more image(s)`, 'error', 'details-alert');
        imageUpload.value = '';
        return;
      }
  
      const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
      const invalid = files.filter(f => !validTypes.includes(f.type));
      if (invalid.length > 0) {
        showAlert('Only JPG, JPEG, and PNG files are allowed', 'error', 'details-alert');
        imageUpload.value = '';
        return;
      }
  
      AppState.selectedFiles = newFiles;
      renderPreviews();
      imageUpload.value = '';
    }
  
    function renderPreviews() {
      previewGrid.innerHTML = '';
      AppState.selectedFiles.forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          const wrap = document.createElement('div');
          wrap.className = 'preview-item';
  
          const img = document.createElement('img');
          img.src = e.target.result;
  
          const remove = document.createElement('button');
          remove.className = 'preview-remove';
          remove.type = 'button';
          remove.textContent = '×';
          remove.onclick = () => removeImage(index);
  
          wrap.appendChild(img);
          wrap.appendChild(remove);
          previewGrid.appendChild(wrap);
        };
        reader.readAsDataURL(file);
      });
    }
  
    function removeImage(idx) {
      AppState.selectedFiles.splice(idx, 1);
      const dt = new DataTransfer();
      AppState.selectedFiles.forEach(f => dt.items.add(f));
      imageUpload.files = dt.files;
      renderPreviews();
      if (AppState.selectedFiles.length === 0) imageUpload.value = '';
    }
  
    // Submit → REAL backend call
    jewelryForm.addEventListener('submit', async (e) => {
      e.preventDefault();
  
      if (AppState.selectedFiles.length < 1 || AppState.selectedFiles.length > 3) {
        showAlert('Please upload between 1 and 3 images', 'error', 'details-alert');
        return;
      }
  
      const width = document.getElementById('width').value;
      const fitLength = document.getElementById('fit_length').value;
      const metalType = document.getElementById('metal_type').value;
  
      generateBtn.disabled = true;
      document.getElementById('loading-overlay').classList.add('active');
      document.getElementById('results-section').classList.add('hidden');
  
      const formData = new FormData();
      formData.append('category', AppState.selectedCategory);
      formData.append('width', width);
      formData.append('fit_length', fitLength);
      formData.append('metal_type', metalType);
      AppState.selectedFiles.forEach(file => formData.append('images', file));
  
      try {
        const result = await callBackendAPI('/generate', formData);
        if (!result || !result.image_url) throw new Error('Backend did not return image_url');
        displayResults(result.image_url, result.description || '');
      } catch (err) {
        console.error('API Error:', err);
        showAlert('Generation failed: ' + (err.message || 'Unknown error'), 'error', 'details-alert');
        document.getElementById('loading-overlay').classList.remove('active');
        generateBtn.disabled = false;
      }
    });
  
    function displayResults(imageUrl /*, description */) {
      AppState.generatedImageUrl = imageUrl;
  
      const imgEl = document.getElementById('generated-image');
      imgEl.src = imageUrl; // works with public or SAS URLs (no CORS needed for <img>)
      imgEl.alt = 'Generated Jewelry Image';
  
      document.getElementById('results-section').classList.remove('hidden');
      document.getElementById('loading-overlay').classList.remove('active');
      generateBtn.disabled = false;
      showAlert('Jewelry generated successfully!', 'success', 'details-alert');
      document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
    }
  
    // DOWNLOAD: open SAS link directly (no fetch → no CORS)
    downloadBtn.addEventListener('click', async () => {
      if (!AppState.generatedImageUrl) return;
  
      downloadBtn.disabled = true;
      downloadBtn.textContent = 'Downloading...';
  
      try {
        const a = document.createElement('a');
        a.href = AppState.generatedImageUrl; // SAS/public blob URL from backend
        // Some browsers ignore cross-origin filename; still triggers download/open
        a.download = `hautecarat_${AppState.selectedCategory.toLowerCase()}_${Date.now()}.png`;
        a.rel = 'noopener';
        document.body.appendChild(a);
        a.click();
        a.remove();
        showAlert('Image download triggered.', 'success', 'details-alert');
      } catch (error) {
        showAlert('Download failed: ' + (error.message || 'Unknown error'), 'error', 'details-alert');
      } finally {
        downloadBtn.disabled = false;
        downloadBtn.textContent = 'Download Image';
      }
    });
  
    // Back & logout
    backBtn.addEventListener('click', (e) => {
      e.preventDefault();
      showPage('category');
      resetDetailsForm();
    });
    logoutBtn2.addEventListener('click', (e) => {
      e.preventDefault();
      handleLogout();
    });
  
    function resetDetailsForm() {
      jewelryForm.reset();
      AppState.selectedFiles = [];
      previewGrid.innerHTML = '';
      imageUpload.value = '';
      document.getElementById('results-section').classList.add('hidden');
      AppState.generatedImageUrl = null;
    }
  }
  
  /* =========================
     LOGOUT
  ========================= */
  function handleLogout() {
    AppState.isAuthenticated = false;
    AppState.selectedCategory = '';
    AppState.selectedFiles = [];
    AppState.generatedImageUrl = null;
  
    document.getElementById('login-form').reset();
    document.getElementById('jewelry-form').reset();
  
    showPage('login');
    showAlert('Logged out successfully', 'success', 'login-alert');
  }
  
  /* =========================
     INIT
  ========================= */
  document.addEventListener('DOMContentLoaded', () => {
    initLoginPage();
    initCategoryPage();
    initDetailsPage();
    showPage('login');
  });
  
  /* =========================
     API INTEGRATION
  ========================= */
  // Your Azure Container App backend:
  const API_BASE_URL = 'https://haute-backend.grayrock-2ee3c09e.eastus2.azurecontainerapps.io/api';
  
  async function callBackendAPI(endpoint, data) {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
      method: 'POST',
      body: data
    });
  
    // Try to parse JSON; if not JSON, surface text
    const ct = response.headers.get('content-type') || '';
    let result;
    if (ct.includes('application/json')) {
      result = await response.json();
    } else {
      const text = await response.text();
      result = { message: text };
    }
  
    if (!response.ok) {
      throw new Error(result.message || `API call failed (${response.status})`);
    }
    return result;
  }
  