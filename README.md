# Spotter Fuel Route 🚗⛽

**Spotter Fuel Route** is a Django-based application that helps users find optimal fuel stations along a given route based on fuel price and distance. The application integrates with **Geoapify API** for geolocation and routing.

---

## 🚀 Features
- 📍 Fetch latitude and longitude for a given location.
- 🛣 Retrieve optimized route between start and end locations.
- ⛽ Identify nearby fuel stations along the route.
- 📊 Calculate the best fuel stops based on price and distance.
- 🔗 API-based integration for location data and routing.

---

## 🛠 Project Setup

### ✅ Prerequisites
Ensure you have the following installed:
- **Python** (>=3.6)
- **Django** (>=3.2)
- **Virtual Environment**

### 🔹 Step 1: Clone the Repository
```bash
git clone https://github.com/SuhagSundarSwain/spotter_fuel_route.git
cd spotter_fuel_route
```

### 🔹 Step 2: Create and Activate Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # For Linux/macOS
venv\Scripts\activate  # For Windows
```

### 🔹 Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### 🔹 Step 4: Set Up Environment Variables
Create a `.env` file in the root directory and add:
```bash
API_KEY=your_geoapify_api_key
```
👉 Get your API key from [Geoapify](https://www.geoapify.com/)

### 🔹 Step 5: Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 🔹 Step 6: Load Fuel Station Data
Ensure your fuel station data is in a CSV file format. Run the import command:
```bash
python manage.py import_fuel_stations
```
📄 **[Fuel Stations CSV File](https://drive.google.com/file/d/1EC2fjEX3YPuvItffS-pP225cplw-Tden/view?usp=sharing)**

### 🔹 Step 7: Start the Django Development Server
```bash
python manage.py runserver
```
🌍 The application will be available at **`http://127.0.0.1:8000/`**

---

## 📡 API Usage

### 🔍 Get Optimized Fuel Stops Along a Route
**Endpoint:**
```http
GET /getroute?start=<start_location>&end=<end_location>
```

**Example:**
```http
GET http://127.0.0.1:8000/getroute?start=New+York&end=Los+Angeles
```

**Response:**
```json
{
    "route": [
        [40.7128, -74.006],
        [39.7392, -104.9903],
        [34.0522, -118.2437]
    ],
    "fuel_stops": [
        {
            "name": "Cheap Fuel Station",
            "address": "123 Main St",
            "city": "Denver",
            "state": "CO",
            "retail_price": 3.45,
            "latitude": 39.7392,
            "longitude": -104.9903
        }
    ],
    "total_fuel_cost": 150.75
}
```

---

## 📂 Project Structure
```
spotter_fuel_route/
│── manage.py
│── .env
│── requirements.txt
│── fuel_stations.csv
│── app/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── utils.py
│── templates/
│── static/
```

---

## 🤝 Contributing
Contributions are welcome! Follow these steps:
1. **Fork** the repository.
2. **Create a feature branch** (`git checkout -b feature-name`).
3. **Commit your changes** (`git commit -m 'Add feature'`).
4. **Push to the branch** (`git push origin feature-name`).
5. **Open a Pull Request**.

---

## 📜 License
This project is licensed under the **MIT License**.

---

## 📞 Contact
For any queries, reach out to:
📧 **suhagsundarswain1@gmail.com**

🎥 **[Demo Video](#)**(https://www.loom.com/share/5a6821e426b741c391ee0827da95a4c1?sid=d8842cec-6109-47d9-8a04-7e9f543a01b1)
