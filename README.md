# Actuator — Mobile App Landing Page for GitHub Pages

A modern, responsive, high-converting Jekyll landing page template designed specifically for mobile applications available on the **Apple App Store** and **Google Play Store**.

Built with native Jekyll architecture, optimized for GitHub Pages zero-configuration deployment, and fully compliant with Apple and Google Store legal requirements (including dedicated Privacy Policy, Terms of Service, and Support pages).

---

## 📱 Features

- **Store-Ready Badges:** Crisp, scalable SVG badges for Apple App Store and Google Play Store with direct links.
- **Interactive Phone Mockup:** Realistic smartphone frame showcasing key UI elements and app stats.
- **App Store Compliant Legal Pages:**
  - [Privacy Policy](/privacy/) — GDPR & CCPA compliant clauses, third-party disclosure, data deletion policy.
  - [Terms of Service](/terms/) — EULA license, acceptable use, in-app purchase terms, warranty disclaimer.
  - [Help & Support](/support/) — Dedicated contact info, troubleshooting guides, account deletion instructions (required by Apple App Store Connect).
- **Data-Driven Sections:** Features, FAQs, and screenshots are organized in `_data/` files so you can edit content without touching HTML.
- **Modern Responsive Design:** Mobile-first layout, smooth scrolling, interactive FAQ accordion, mobile hamburger drawer, and clean typography.
- **GitHub Pages Ready:** Works automatically out-of-the-box when pushed to GitHub.

---

## 📁 File Structure

```text
├── _config.yml               # Central site configuration (App name, store URLs, email)
├── _data/
│   ├── features.yml          # Feature cards and icons
│   ├── faq.yml               # Frequently asked questions
│   └── screenshots.yml       # Screenshot gallery data
├── _includes/
│   ├── head.html             # SEO meta tags, OpenGraph, font imports
│   ├── header.html           # Sticky navigation with mobile menu
│   ├── footer.html           # Footer links and copyright notice
│   └── app_badges.html       # Official-spec SVG store buttons
├── _layouts/
│   ├── default.html          # Main HTML structure
│   └── page.html             # Clean reading layout for legal & support pages
├── assets/
│   ├── css/style.css         # Modern, responsive styles and phone mockup
│   └── js/main.js            # Accordion and navigation script
├── index.html                # Main landing page
├── privacy.md                # Privacy Policy page (/privacy/)
├── terms.md                  # Terms of Service page (/terms/)
├── support.md                # Help & Support page (/support/)
└── Gemfile                   # Ruby dependencies for local development
```

---

## ⚙️ Configuration & Customization

All primary settings are managed in `_config.yml`:

```yaml
title: "Actuator"
tagline: "The modern mobile experience you've been waiting for"
description: "Actuator is a sleek, intuitive mobile app..."

# Your App Store & Google Play Store Links:
app_store_url: "https://apps.apple.com/app/id123456789"
google_play_url: "https://play.google.com/store/apps/details?id=com.actuator.app"

# App Metadata:
app_rating: "4.9"
app_reviews_count: "10K+"
app_version: "2.4.0"
support_email: "support@actuator.app"
copyright_name: "Actuator Inc."
```

### Modifying Content
- **Features:** Edit `_data/features.yml` to add or modify app highlights.
- **FAQ:** Edit `_data/faq.yml` to add custom questions & answers.
- **Screenshots:** Edit `_data/screenshots.yml` to update showcase cards.
- **Privacy & Terms:** Edit `privacy.md` and `terms.md` with your company details.

---

## 🚀 Local Development

To run the site locally on your computer:

```bash
# 1. Install dependencies
bundle install

# 2. Start Jekyll local server
bundle exec jekyll serve

# 3. View in browser
open http://localhost:4000
```

---

## 🌐 Deploying to GitHub Pages

1. Commit and push your changes to the `main` branch:
   ```bash
   git add .
   git commit -m "Add modern mobile app Jekyll landing page"
   git push origin main
   ```
2. In your GitHub repository:
   - Go to **Settings > Pages**.
   - Under **Build and deployment**, set **Source** to `Deploy from a branch`.
   - Select branch `main` and folder `/ (root)`.
   - Click **Save**.
3. Your site will automatically build and publish to your GitHub Pages URL!