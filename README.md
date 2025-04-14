# 🔐 HTTP Login BruteForcer

A professional and customizable HTTP login brute-force tool for penetration testers and cybersecurity professionals. This tool uses multi-threading, CSRF support, and live stats with a rich interface.

> 🚨 **LEGAL DISCLAIMER:** This tool is for authorized testing and educational purposes only. Do not use on systems you do not own or have explicit permission to test.

---

## ⚙️ Requirements

Install Python dependencies using the provided `requirements.txt`.

```bash
pip install -r requirements.txt
requirements.txt contents:
nginx
Copy
Edit
requests
rich
🚀 Installation
Clone this repository or download the script.

Install required libraries:

bash
Copy
Edit
pip install -r requirements.txt
Run the tool:

bash
Copy
Edit
python3 http_brute.py --help
🧠 How It Works
This tool sends POST requests to a login form with a list of usernames and passwords. It supports:

CSRF token extraction

Custom form field names

Extra static fields

Rich CLI output with live progress and result display

Auto-stopping on first success (unless --verbose is used)

📥 Usage
bash
Copy
Edit
python3 http_brute.py TARGET_URL --login-url LOGIN_URL -u USERNAME -P PASSWORD [options]
Required Arguments:
Argument	Description
TARGET_URL	Base URL of the target
--login-url	Full login form URL
-u, --username	Single username or path to username file
-P, --password	Single password or path to password file
💡 Example Commands
1. Single username/password
bash
Copy
Edit
python3 http_brute.py http://example.com --login-url http://example.com/login -u admin -P 123456
2. Wordlists for usernames and passwords
bash
Copy
Edit
python3 http_brute.py http://example.com --login-url http://example.com/login -u usernames.txt -P passwords.txt
3. CSRF Token + Custom Field Names
bash
Copy
Edit
python3 http_brute.py http://example.com --login-url http://example.com/login \
  -u admin -P passwords.txt \
  --username-field user --password-field pass \
  --csrf-field csrf_token
4. With Extra Fields
bash
Copy
Edit
python3 http_brute.py http://example.com --login-url http://example.com/login \
  -u admin -P passwords.txt \
  --extra-fields remember_me=on submit=Login
📁 Extra Fields via JSON File (optional)
You can create a JSON file (extra-fields.json) like this:

json
Copy
Edit
{
  "remember_me": "on",
  "submit": "Login"
}
And pass the values manually using:

bash
Copy
Edit
--extra-fields remember_me=on submit=Login
🔧 You can modify the script to support --extra-fields-file if desired.

🛠️ Optional Flags
Flag	Description
--username-field	Custom form username field (default: username)
--password-field	Custom form password field (default: password)
--csrf-field	CSRF token field name (will auto-extract token from page)
--extra-fields	Additional form fields (field=value)
-d, --delay	Delay between attempts in seconds (default: 0.5)
-t, --threads	Number of concurrent threads (default: 4, max: 10)
-v, --verbose	Keep scanning even after finding valid credentials
📄 Output
✅ Valid credentials will be shown in a styled table.

💾 Saved to credentials_found.txt

📜 Logs written to http_brute.log

🧑‍💻 Author
Built with ❤️ for ethical hacking and red teaming professionals.

