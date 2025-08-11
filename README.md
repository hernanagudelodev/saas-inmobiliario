# 🏠 SaaS Inmobiliario – Multi-Tenant Real Estate Management Platform

**Status:** In Development – Internal project, currently in data modeling phase. Integrated **AppInventarios** module completed and functional, with **multi-tenant architecture** already implemented.

## 📌 Overview
**SaaS Inmobiliario** is a **multi-tenant real estate management system** built with Django 5.1.5 and Python 3.13.6.  
It is the next-generation evolution of **[AppInventarios](https://github.com/hernanagudelodev/appInventarios)**, expanding beyond property inventory management to cover **rental administration, contracts, payments, accounting integration, and AI-assisted real estate analysis**.

Designed with a **modular architecture** to integrate all essential services required by real estate agencies into a single, scalable platform.

---

## 🚀 Current Features
- **Full Integration with AppInventarios**
  - Complete property inventory management for acquisition (*captación*) and delivery (*entrega*), with dynamic forms, digital signatures, and PDF generation.
- **Multi-Tenant Architecture**
  - Multiple real estate agencies can operate independently in the same system, with isolated data per tenant.

---

## 🛠 Planned Features (Roadmap)
### Phase 1 – Core Rental Management
- Clients, Properties, Contracts
- Rental Payment Reconciliation:
  - Tenant payments
  - Landlord payments
  - Building administration fees (if applicable)
  - Repairs and improvements
  - Real estate commission invoicing
- Access control by role (admin, agent, assistant)

### Phase 2 – Integrations & Automation
- Integration with accounting systems (to be defined)
- Automated commission invoicing

### Phase 3 – AI-Powered Real Estate Assistant
- AI module for property-specific market analysis
- Pricing suggestions, investment recommendations

---

## 🛠 Tech Stack
- **Backend:** Python 3.13.6, Django 5.1.5
- **Database:** PostgreSQL (production target)
- **Architecture:** Modular, Multi-Tenant (per field isolation)
- **Deployment:** Docker + CI/CD pipeline
- **Frontend:** HTML, CSS (Bootstrap 5), JavaScript
- **Maps:** Leaflet.js with browser geolocation
- **PDF & Signatures:** SignaturePad, Django templates

---

## 📂 Current Modules
- **Inventory Management** – Complete from AppInventarios, including dynamic form builder, digital signatures, and PDF reports.
- **Multi-Tenant Core** – Tenant-based data isolation for multiple real estate agencies.

---

## 📸 Screenshots
*(To be added)*  
Suggested: Dashboard, tenant management interface, inventory module views.

---

## ⚙️ Installation
```bash
# 1. Clone the repository
git clone https://github.com/hernanagudelodev/SaaSInmobiliario.git
cd SaaSInmobiliario

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
# Example: create a .env file and configure DATABASE_URL, SECRET_KEY, DEBUG, etc.

# 5. Run migrations
python manage.py migrate

# 6. Create a superuser
python manage.py createsuperuser

# 7. Start the development server
python manage.py runserver

```

---

## 📜 License
This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

## 📬 Contact
**Hernán Agudelo López**  
📧 hernanagudelodev@gmail.com  
🔗 [LinkedIn](https://www.linkedin.com/in/hernan-agudelo) | [GitHub](https://github.com/hernanagudelodev)
