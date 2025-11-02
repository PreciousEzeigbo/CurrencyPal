# 💱 CurrencyPal

> A simple, user-friendly currency conversion API with conversational chat capabilities

CurrencyPal is a FastAPI-based currency conversion service that provides real-time exchange rates for 160+ currencies worldwide. It features both RESTful API endpoints and an intelligent chat interface for natural language currency queries.

## ✨ Features

- 🌍 **160+ Currencies** - Support for major and minor currencies worldwide
- 💱 **Real-time Rates** - Live exchange rates from reliable sources
- 💬 **Conversational Chat** - Natural language interface for easy interactions
- 🎨 **Formatted Output** - Currency symbols (₦, $, €, £) and thousand separators
- ⚡ **Fast & Reliable** - Built with FastAPI for high performance
- 🔒 **Error Handling** - Graceful timeout handling and user-friendly error messages
- 📊 **Multiple Endpoints** - REST API for programmatic access

## � Table of Contents

- [Quick Start](#-quick-start)
- [API Documentation](#-api-documentation)
- [Testing the API](#-testing-the-api)
- [Supported Currencies](#-supported-currencies)
- [Common Issues](#-common-issues)
- [Deployment](#-deployment)
- [Technology Stack](#️-technology-stack)
- [Contributing](#-contributing)

## �🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation & Setup

```bash
# 1. Clone the repository
git clone https://github.com/PreciousEzeigbo/CurrencyPal
cd CurrencyPal

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the server
uvicorn main:app --reload
```

### Verify Installation

```bash
# Check Python version (should be 3.8+)
python --version

# Server should be running at:
# http://127.0.0.1:8000

# Access interactive API docs:
# http://127.0.0.1:8000/docs
```

## 📚 API Documentation

### Base URL

- **Local Development**: `http://127.0.0.1:8000`
- **Interactive Docs**: `http://127.0.0.1:8000/docs`
- **Alternative Docs**: `http://127.0.0.1:8000/redoc`

### Endpoints

#### 1. Root Endpoint

```http
GET /
```

**Response:**

```json
{
  "message": "Welcome to CurrencyPal! Try /convert?from=USD&to=NGN&amount=50"
}
```

---

#### 2. Currency Conversion

```http
GET /convert?from_currency={FROM}&to_currency={TO}&amount={AMOUNT}
```

**Parameters:**

- `from_currency` (required): Source currency code (3 letters, e.g., USD, EUR)
- `to_currency` (required): Target currency code (3 letters, e.g., NGN, GBP)
- `amount` (optional): Amount to convert (default: 1.0, must be > 0)

**Example:**

```bash
curl "http://127.0.0.1:8000/convert?from_currency=EUR&to_currency=NGN&amount=50"
```

**Response:**

```json
{
  "from": "EUR",
  "to": "NGN",
  "amount": 50.0,
  "rate": 1659.38,
  "converted": 82969.0,
  "formatted_amount": "€50.00",
  "formatted_converted": "₦82,969.00",
  "message": "€50.00 = ₦82,969.00 💱 (Rate: 1 EUR = 1,659.38 NGN)"
}
```

---

#### 3. Exchange Rates

```http
GET /rates?currencies={CURRENCY_LIST}
```

**Parameters:**

- `currencies` (optional): Comma-separated currency codes (default: USD,EUR,GBP,JPY,CAD)

**Example:**

```bash
curl "http://127.0.0.1:8000/rates?currencies=USD,EUR,GBP"
```

**Response:**

```json
{
  "base": "NGN",
  "rates": {
    "USD": 1765.0,
    "EUR": 1659.38,
    "GBP": 2112.45
  },
  "formatted_rates": ["$1 = ₦1,765.00", "€1 = ₦1,659.38", "£1 = ₦2,112.45"],
  "message": "$1 = ₦1,765.00 | €1 = ₦1,659.38 | £1 = ₦2,112.45"
}
```

---

#### 4. Chat Interface

```http
POST /chat
Content-Type: application/json
```

**Request:**

```json
{
  "text": "your message here"
}
```

**Supported Commands:**

| Command        | Example                        | Description                |
| -------------- | ------------------------------ | -------------------------- |
| Greetings      | `"hi"`, `"hello"`              | Get welcome message        |
| Help           | `"help"`                       | See available commands     |
| Convert        | `"convert 50 USD to NGN"`      | Convert currency           |
| Convert (alt)  | `"how much is 100 EUR in NGN"` | Alternative syntax         |
| Single Rate    | `"USD rate"`                   | Check single currency rate |
| Multiple Rates | `"show rates to NGN"`          | Display multiple rates     |
| Thanks         | `"thanks"`                     | Acknowledgment             |

**Example:**

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "convert 100 USD to NGN"}'
```

**Response:**

```json
{
  "response": "✅ $100.00 = ₦176,500.00 💱 (Rate: 1 USD = 1,765 NGN)"
}
```

## 🧪 Testing the API

### 1. Browser Testing

Visit these URLs in your browser:

- Interactive Docs: http://127.0.0.1:8000/docs
- Alternative Docs: http://127.0.0.1:8000/redoc
- API Root: http://127.0.0.1:8000/

### 2. Command Line (curl)

```bash
# Convert currency
curl "http://127.0.0.1:8000/convert?from_currency=USD&to_currency=NGN&amount=100"

# Get rates
curl "http://127.0.0.1:8000/rates?currencies=USD,EUR,GBP"

# Chat
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "convert 50 EUR to NGN"}'
```

### 3. Python

```python
import requests

# Convert currency
response = requests.get(
    "http://127.0.0.1:8000/convert",
    params={"from_currency": "USD", "to_currency": "NGN", "amount": 100}
)
print(response.json())

# Chat
response = requests.post(
    "http://127.0.0.1:8000/chat",
    json={"text": "convert 50 EUR to NGN"}
)
print(response.json())
```

### 4. JavaScript (Browser Console)

```javascript
// Test conversion
fetch(
  "http://127.0.0.1:8000/convert?from_currency=USD&to_currency=NGN&amount=100"
)
  .then((r) => r.json())
  .then((data) => console.log(data));

// Test chat
fetch("http://127.0.0.1:8000/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ text: "convert 50 USD to NGN" }),
})
  .then((r) => r.json())
  .then((data) => console.log(data.response));
```

### 5. Example Client Script

```bash
# Run the included example client
python example_client.py

# For interactive chat mode
python example_client.py
# Then choose 'y' when prompted
```

## 🌍 Supported Currencies

CurrencyPal supports 160+ currencies with proper symbols and formatting:

**Major Currencies:** USD ($), EUR (€), GBP (£), JPY (¥), CAD (C$), AUD (A$), CHF (Fr)

**African:** NGN (₦), ZAR (R), EGP (E£), KES, GHS

**Asian:** INR (₹), CNY (¥), KRW (₩), SGD (S$), HKD (HK$), THB (฿), IDR (Rp), PHP (₱)

**Latin American:** BRL (R$), MXN ($), ARS, COP

**Middle Eastern:** AED (د.إ), SAR (﷼), ILS (₪), TRY (₺)

...and many more! See the full list in [currency_api.py](utils/currency_api.py).

## ⚠️ Common Issues

### Issue: "ModuleNotFoundError: No module named 'fastapi'"

**Solution:**

```bash
# Make sure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Address already in use"

**Solution:**

```bash
# Find and kill process on port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Or use a different port
uvicorn main:app --reload --port 8001
```

### Issue: "Connection timed out" in API responses

**Solution:**

- Check your internet connection
- External API might be temporarily down
- Timeout is configurable in `utils/currency_api.py` (default: 10 seconds)

### Issue: Virtual environment won't activate

**Solution:**

```bash
# Linux/Mac
chmod +x venv/bin/activate

# Windows - enable scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: "pip: command not found"

**Solution:**

```bash
# Use python module instead
python -m pip install -r requirements.txt

# Or ensure pip is installed
python -m ensurepip --upgrade
```

## 🚀 Deployment

### Running in Production

#### Basic Production Server

```bash
# With multiple workers for better performance
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### With Gunicorn (Recommended for Production)

```bash
# Install gunicorn
pip install gunicorn

# Run with uvicorn workers
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Deployment

**Create `Dockerfile`:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and run:**

```bash
docker build -t currencypal .
docker run -d -p 8000:8000 currencypal
```

### Cloud Platforms

#### Heroku

```bash
# Create Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
heroku create currencypal-api
git push heroku main
```

#### Railway / Render

1. Connect your GitHub repository
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Deploy!

#### VPS (DigitalOcean, Linode, AWS EC2)

**Create systemd service** (`/etc/systemd/system/currencypal.service`):

```ini
[Unit]
Description=CurrencyPal API
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/currencypal
Environment="PATH=/path/to/currencypal/venv/bin"
ExecStart=/path/to/currencypal/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

[Install]
WantedBy=multi-user.target
```

**Enable and start:**

```bash
sudo systemctl enable currencypal
sudo systemctl start currencypal
sudo systemctl status currencypal
```

### Performance Tips

**1. Enable CORS (if needed):**

```python
# Add to main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**2. Add Nginx reverse proxy:**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🛠️ Technology Stack

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[Uvicorn](https://www.uvicorn.org/)** - ASGI server
- **[httpx](https://www.python-httpx.org/)** - Async HTTP client
- **[Pydantic](https://docs.pydantic.dev/)** - Data validation
- **[exchangerate-api.com](https://exchangerate-api.com/)** - Currency rate API (free tier)

## 📁 Project Structure

```
currencypal/
├── main.py                 # FastAPI app & endpoints
├── utils/
│   └── currency_api.py     # Currency logic & API calls
├── requirements.txt        # Dependencies
├── example_client.py       # Usage examples
├── .gitignore             # Git ignore rules
├── CONTRIBUTING.md        # Contribution guidelines
└── README.md              # This file
```

## ⚙️ Configuration

### Adjust Timeout

Edit `utils/currency_api.py`:

```python
async with httpx.AsyncClient(timeout=10.0) as client:  # Change 10.0 to your value
```

### Change Default Currencies

Edit `utils/currency_api.py`:

```python
if currencies is None:
    currencies = ["USD", "EUR", "GBP", "JPY", "CAD"]  # Customize this list
```

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 👨‍💻 Author

Created with ❤️ for the HNGi13 Project

## 🙏 Acknowledgments

- [exchangerate-api.com](https://exchangerate-api.com/) for providing free currency exchange rates
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent framework
- The Python community for amazing tools and libraries

## 📞 Support

If you have any questions or run into issues:

1. Check the [API Documentation](#api-documentation)
2. Use the chat endpoint with `"help"` to see available commands
3. Open an issue on GitHub
4. Review the error messages - they're designed to be helpful!

**Made with 💱 CurrencyPal - Your friendly currency conversion assistant!**
