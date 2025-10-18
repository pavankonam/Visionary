# HauteCarat Frontend

A single-page luxury jewelry generation interface matching the design aesthetic of hautecarat.com

## Files Structure

```
frontend/
├── index.html                          # Single HTML file with all pages
├── static/
│   ├── css/
│   │   └── hautecarat-style.css       # Luxury design styles
│   └── js/
│       └── hc-app.js                  # All JavaScript functionality
└── README.md                          # This file
```

## Design Features

### Design Aesthetic (Matching hautecarat.com)
- **Fonts**: Lora (serif) for headings, Work Sans (sans-serif) for body
- **Colors**: Black (#000000), Off-white (#fcfbf9), Cream (#f8f7f4)
- **Style**: Minimalist, luxury, sophisticated
- **Layout**: Clean, modern, image-driven with ample white space

### Three Pages in One HTML

**Page 1: Login**
- Email and password fields
- Hardcoded credentials: `abdul.mazin@gmail.com` / `HauteCarat@2024!`
- Clean, centered login form

**Page 2: Category Selection**
- Four categories: Earrings, Rings, Bracelets, Necklaces
- Elegant grid layout with icons
- Hover effects and smooth transitions

**Page 3: Jewelry Details**
- Input fields: Width, Fit/Length, Metal Type
- Image upload (1-3 images, drag & drop support)
- Live image preview with remove functionality
- Results display with download option

## How to Use

### 1. Open the Application

Simply open `index.html` in your web browser:
- Double-click the file, or
- Right-click → Open with → Your browser

### 2. Test the Flow

**Step 1: Login**
- Email: `abdul.mazin@gmail.com`
- Password: `HauteCarat@2024!`

**Step 2: Select Category**
- Click on any jewelry category card
- Each selection navigates to the details page

**Step 3: Fill Details**
- Enter jewelry width (e.g., 2.5)
- Enter fit/length (e.g., "Comfort Fit")
- Select metal type from dropdown
- Upload 1-3 jewelry images (JPG, JPEG, or PNG)

**Step 4: Generate**
- Click "Generate Jewelry" button
- See loading animation
- View generated results (currently showing mock data)

**Step 5: Download**
- Click "Download Image" to save the result

## Features Implemented

### ✅ Single-Page Application
- All pages in one HTML file
- JavaScript-based page navigation
- No page reloads, smooth transitions

### ✅ Authentication
- Login validation with hardcoded credentials
- Session state management
- Logout functionality on all pages

### ✅ Category Selection
- Visual category cards
- Click to select and navigate
- Responsive grid layout

### ✅ Image Upload
- Drag and drop support
- Multiple image selection (1-3 images)
- File type validation (JPG, JPEG, PNG)
- Live image preview
- Remove individual images

### ✅ Form Validation
- Required field validation
- Input type validation
- File format validation
- Visual feedback for errors

### ✅ User Experience
- Loading animations
- Success/error alerts
- Smooth page transitions
- Responsive design
- Hover effects
- Go back navigation
- Logout from any page

### ✅ Mock Generation
- Simulates AI generation process
- Displays mock results
- Download functionality

## Backend Integration

The frontend is ready for backend integration. Key integration points:

### API Endpoint Placeholder
Located in `hc-app.js`:

```javascript
const API_BASE_URL = 'http://localhost:5000/api';
```

### Form Submission
The `simulateGeneration()` function in `hc-app.js` prepares FormData:

```javascript
formData.append('category', AppState.selectedCategory);
formData.append('width', width);
formData.append('fit_length', fitLength);
formData.append('metal_type', metalType);
AppState.selectedFiles.forEach(file => {
    formData.append('images', file);
});
```

### Integration Steps

1. **Update API_BASE_URL** to your backend URL
2. **Replace `simulateGeneration()`** with actual API call:

```javascript
async function generateJewelry(formData) {
    try {
        const response = await fetch(`${API_BASE_URL}/generate`, {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });

        const result = await response.json();

        if (result.success) {
            displayResults(result.image_url, result.description);
        } else {
            showAlert(result.message, 'error', 'details-alert');
        }
    } catch (error) {
        showAlert('Generation failed: ' + error.message, 'error', 'details-alert');
    } finally {
        document.getElementById('loading-overlay').classList.remove('active');
        generateBtn.disabled = false;
    }
}
```

3. **Update login authentication** to call your backend:

```javascript
const response = await fetch(`${API_BASE_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
    credentials: 'include'
});
```

## Customization

### Colors
Edit CSS variables in `hautecarat-style.css`:

```css
:root {
    --primary-black: #000000;
    --primary-white: #fcfbf9;
    --cream: #f8f7f4;
    --soft-gray: #666666;
}
```

### Categories
Add/remove categories in `index.html`:

```html
<div class="category-card" data-category="YourCategory">
    <span class="category-icon">⚜️</span>
    <h3 class="category-title">Your Category</h3>
</div>
```

### Metal Types
Update dropdown options in `index.html`:

```html
<option value="Your Metal">Your Metal</option>
```

## Browser Compatibility

- ✅ Chrome (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ✅ Modern mobile browsers

## No Dependencies

This frontend uses:
- Pure HTML5
- Pure CSS3
- Vanilla JavaScript (no frameworks)
- Google Fonts (Lora & Work Sans)

No npm, no build process, no dependencies to install!

## Testing Checklist

- [ ] Login with correct credentials
- [ ] Login with wrong credentials (should show error)
- [ ] Navigate to category page after login
- [ ] Select each category
- [ ] Upload 1 image
- [ ] Upload 3 images
- [ ] Try uploading 4 images (should show error)
- [ ] Upload wrong file type (should show error)
- [ ] Remove uploaded images
- [ ] Fill all form fields
- [ ] Submit form (see loading animation)
- [ ] View mock results
- [ ] Download image
- [ ] Click "Go Back" button
- [ ] Logout from category page
- [ ] Logout from details page

## Next Steps

1. ✅ Frontend complete
2. ⏳ Integrate with your existing backend
3. ⏳ Replace mock generation with real AI calls
4. ⏳ Test end-to-end workflow
5. ⏳ Deploy to production

---

**Ready to integrate!** The frontend is fully functional and waiting for your backend API.
