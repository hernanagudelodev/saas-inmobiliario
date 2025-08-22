# 🏠 SaaS Inmobiliario – Multi-Tenant Real Estate Management Platform

**Status:** In Development – Internal project, currently in data modeling phase. Integrated **AppInventarios** module completed and functional, with **multi-tenant architecture** already implemented.

## 📌 Overview
**SaaS Inmobiliario** is a **multi-tenant real estate management system** built with Django 5.1.5 and Python 3.13.6.  
It is the next-generation evolution of **[AppInventarios](https://github.com/hernanagudelodev/appInventarios)**, expanding beyond property inventory management to cover **rental administration, contracts, payments, accounting integration, and AI-assisted real estate analysis**.

Designed with a **modular architecture** to integrate all essential services required by real estate agencies into a single, scalable platform.

---

## 🚀 Implemented Features

### Core & Multi-Tenancy Module
- **Multi-Tenant Architecture:** Multiple real estate agencies can operate independently and securely, with all their data isolated.
- **User and Profile Management:** Authentication system and extended user profiles, associating each user with a real estate agency (tenant).

### Clients & Properties Module (`core_inmobiliario`)
- **Full CRUD for Clients and Properties:** Complete management of the client and property portfolio.
- **Geolocation:** Interactive map (Leaflet.js) to register the exact location of properties.
- **Dynamic Relationships:** System for linking clients to properties with different roles (Owner, Tenant, etc.).

### Inventory Module (`inventarioapp`)
- **Dynamic Onboarding Forms:** Creation of fully customizable property onboarding forms by section and field type.
- **Detailed Handover Forms:** A complete workflow to document the handover of a property, recording specific rooms and items.
- **Digital Signature:** Integration with SignaturePad.js for the electronic signing of documents directly on the platform.
- **PDF Generation:** Automatic creation of professional PDF documents for signed onboarding and handover forms.

---

## 🛠 Planned Features (Roadmap)
### Phase 1 – Core Rental Management
The next major development is the **Lease Management Module**, which will automate the entire lifecycle of a rental agreement.

### Phase 1 – Contract & Terms Management
- [ ] Creation of **Mandate (Owner)** and **Lease (Tenant)** contracts.
- [ ] Definition of economic terms: rent amount, commission percentage, and scheduled (e.g., admin fees) and unscheduled (e.g., repairs) discounts.

### Phase 2 – Monthly Cycle Automation
- [ ] **Automatic invoicing** for tenants at the beginning of each month.
- [ ] **Payment verification and sending automatic reminders** to tenants with overdue payments.
- [ ] **Automatic calculation** of the monthly payout for each property owner.

### Phase 3 – Payouts & Financial Documentation
- [ ] Generation of **batch payment files** to facilitate mass payouts to owners via their bank.
- [ ] Automatic generation of the **Egress Voucher** (detailed payout statement) and the **Commission Invoice** for the owner.


### Phase 2 – Integrations & Automation
- Integration with accounting systems (to be defined)

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
- **`usuarios`**: Core of the multi-tenancy system, profiles, and agencies.
- **`core_inmobiliario`**: Models and logic for clients and properties.
- **`inventarioapp`**: Business workflows for onboarding and handover inventories.
- **`gestion_arriendos`**: (In development) Module for lease contract administration.

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
