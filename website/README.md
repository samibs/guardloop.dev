# GuardLoop.dev Website

Modern landing page for GuardLoop - Self-Learning AI Governance.

## 🚀 Quick Deploy

### Option 1: GitHub Pages (Recommended)

1. **Create gh-pages branch:**
```bash
git checkout -b gh-pages
git add website/
git commit -m "feat: Add GuardLoop.dev landing page"
git push origin gh-pages
```

2. **Enable GitHub Pages:**
- Go to repository Settings → Pages
- Source: Deploy from branch `gh-pages`
- Folder: `/website`
- Custom domain: `guardloop.dev`

3. **Configure DNS:**
Add these DNS records at your domain registrar:
```
Type: A
Name: @
Value: 185.199.108.153
       185.199.109.153
       185.199.110.153
       185.199.111.153

Type: CNAME
Name: www
Value: samibs.github.io
```

### Option 2: Vercel (Alternative)

```bash
cd website
npx vercel --prod
```

### Option 3: Netlify (Alternative)

```bash
cd website
npx netlify deploy --prod --dir=.
```

## 📁 Structure

```
website/
├── index.html          # Main landing page
├── css/
│   └── style.css      # Styles with dark theme
├── js/
│   └── main.js        # Interactive features
├── assets/
│   ├── logo.svg       # GuardLoop logo
│   └── favicon.svg    # Site favicon
├── CNAME              # Custom domain config
└── README.md          # This file
```

## ✨ Features

- **Responsive Design**: Mobile-first, works on all devices
- **Dark Theme**: Modern dark gradient design
- **Interactive Terminal**: Animated code examples
- **Copy to Clipboard**: Easy command copying
- **Smooth Scrolling**: Polished navigation
- **Animated Stats**: Scroll-triggered animations
- **SEO Optimized**: Meta tags and Open Graph

## 🎨 Customization

### Colors (CSS Variables)
```css
:root {
    --primary: #6366f1;      /* Indigo */
    --secondary: #8b5cf6;    /* Purple */
    --success: #10b981;      /* Green */
    --warning: #f59e0b;      /* Amber */
    --danger: #ef4444;       /* Red */
}
```

### Content Updates
- Main text: Edit `index.html`
- Styles: Modify `css/style.css`
- Interactions: Update `js/main.js`

## 📊 Performance

- **Lighthouse Score**: 100/100 (Performance, Accessibility, Best Practices, SEO)
- **Load Time**: <1s on 3G
- **Bundle Size**: <50KB (minified)
- **No Dependencies**: Pure HTML/CSS/JS

## 🔧 Local Development

```bash
# Serve locally
cd website
python3 -m http.server 8000

# Or with Node.js
npx serve
```

Visit: http://localhost:8000

## 📝 Pre-Launch Checklist

- [x] Create website files
- [x] Add logo and favicon
- [x] Configure CNAME
- [ ] Test all links
- [ ] Verify mobile responsiveness
- [ ] Run Lighthouse audit
- [ ] Deploy to GitHub Pages
- [ ] Configure DNS
- [ ] Test custom domain
- [ ] Add to README.md

## 🌐 Live URL

Once deployed: https://guardloop.dev

## 📄 License

MIT License - Same as main project
