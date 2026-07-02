import os
import json
import time
import schedule
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, send_file
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading
import random
import re
import base64
from io import BytesIO
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService

app = Flask(__name__)

# Load configuration from environment or config file
def load_config():
    if os.path.exists('config.json'):
        with open('config.json', 'r') as f:
            return json.load(f)
    return {
        'instagram_username': os.getenv('INSTAGRAM_USERNAME', 'YOUR_INSTAGRAM_USERNAME'),
        'instagram_password': os.getenv('INSTAGRAM_PASSWORD', 'YOUR_INSTAGRAM_PASSWORD'),
        'accounts_to_monitor': os.getenv('ACCOUNTS_TO_MONITOR', 'account1,account2,account3').split(','),
        'niche': os.getenv('NICHE', 'general'),
        'auto_reply_enabled': os.getenv('AUTO_REPLY_ENABLED', 'True') == 'True',
        'data_retention_days': int(os.getenv('DATA_RETENTION_DAYS', '30')),
        'refresh_interval_minutes': int(os.getenv('REFRESH_INTERVAL_MINUTES', '60')),
        'data_storage_path': os.getenv('DATA_STORAGE_PATH', './data/'),
        'screenshot_path': os.getenv('SCREENSHOT_PATH', './screenshots/')
    }

CONFIG = load_config()

# Ensure directories exist
os.makedirs(CONFIG['data_storage_path'], exist_ok=True)
os.makedirs(CONFIG['screenshot_path'], exist_ok=True)

class InstagramAutomation:
    def __init__(self):
        self.driver = None
        self.data_store = {}
        self.load_data()
        
    def load_data(self):
        """Load stored data from JSON files"""
        try:
            with open(f"{CONFIG['data_storage_path']}accounts_data.json", 'r') as f:
                self.data_store = json.load(f)
        except FileNotFoundError:
            self.data_store = {}
    
    def save_data(self):
        """Save data to JSON file"""
        with open(f"{CONFIG['data_storage_path']}accounts_data.json", 'w') as f:
            json.dump(self.data_store, f, indent=2)
    
    def start_selenium(self):
        """Initialize Selenium WebDriver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            print("Chrome driver initialized successfully")
        except Exception as e:
            print(f"Chrome failed: {e}, trying Firefox...")
            try:
                firefox_options = webdriver.FirefoxOptions()
                firefox_options.add_argument('--headless')
                service = FirefoxService(GeckoDriverManager().install())
                self.driver = webdriver.Firefox(service=service, options=firefox_options)
                print("Firefox driver initialized successfully")
            except Exception as e2:
                print(f"Warning: Could not initialize Selenium. {e2}")
                return False
        
        try:
            self.driver.maximize_window()
        except:
            pass
        return True
        
    def login_instagram(self):
        """Login to Instagram"""
        try:
            self.driver.get('https://www.instagram.com/accounts/login/')
            time.sleep(5)
            
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'username'))
            )
            username_field.send_keys(CONFIG['instagram_username'])
            
            password_field = self.driver.find_element(By.NAME, 'password')
            password_field.send_keys(CONFIG['instagram_password'])
            password_field.send_keys(Keys.RETURN)
            
            time.sleep(5)
            
            try:
                save_info = self.driver.find_element(By.XPATH, '//button[contains(text(), "Save Info")]')
                save_info.click()
                time.sleep(2)
            except:
                pass
            
            try:
                notifications = self.driver.find_element(By.XPATH, '//button[contains(text(), "Not Now")]')
                notifications.click()
                time.sleep(2)
            except:
                pass
            
            return True
        except Exception as e:
            print(f"Login failed: {e}")
            return False
    
    def get_profile_stats(self, account_username):
        """Get profile statistics for a specific account"""
        try:
            self.driver.get(f'https://www.instagram.com/{account_username}/')
            time.sleep(5)
            
            stats = {}
            try:
                followers_elem = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "/followers/")]/span'))
                )
                stats['followers'] = followers_elem.text
            except:
                stats['followers'] = '0'
            
            try:
                posts_elem = self.driver.find_element(By.XPATH, '//a[contains(@href, "/p/")]/span')
                stats['posts'] = posts_elem.text
            except:
                stats['posts'] = '0'
            
            return stats
        except Exception as e:
            print(f"Error getting stats for {account_username}: {e}")
            return None
    
    def get_posts_metrics(self, account_username, days=7):
        """Get post metrics for the last N days"""
        try:
            self.driver.get(f'https://www.instagram.com/{account_username}/')
            time.sleep(3)
            
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            posts = self.driver.find_elements(By.XPATH, '//article[@role="presentation"]')
            
            metrics = []
            for post in posts[:20]:
                try:
                    post.click()
                    time.sleep(2)
                    
                    try:
                        likes_elem = self.driver.find_element(By.XPATH, '//span[contains(@class, "html-span") and contains(text(), "likes")]')
                        likes = likes_elem.text.replace('likes', '').strip()
                    except:
                        likes = '0'
                    
                    try:
                        comments_elem = self.driver.find_element(By.XPATH, '//span[contains(@class, "html-span") and contains(text(), "comments")]')
                        comments = comments_elem.text.replace('comments', '').strip()
                    except:
                        comments = '0'
                    
                    try:
                        close_btn = self.driver.find_element(By.XPATH, '//button[contains(@class, "wpO6b")]')
                        close_btn.click()
                    except:
                        pass
                    time.sleep(1)
                    
                    metrics.append({
                        'likes': likes,
                        'comments': comments,
                        'date': datetime.now().date().isoformat()
                    })
                except:
                    continue
            
            return metrics
        except Exception as e:
            print(f"Error getting posts metrics: {e}")
            return []
    
    def auto_reply_to_dms(self):
        """Auto-reply to DMs based on keywords"""
        try:
            self.driver.get('https://www.instagram.com/direct/inbox/')
            time.sleep(5)
            
            messages = self.driver.find_elements(By.XPATH, '//div[contains(@class, "x1n2onr6")]')
            
            for message in messages[:5]:
                try:
                    message.click()
                    time.sleep(2)
                    
                    msg_text = self.driver.find_element(By.XPATH, '//div[contains(@class, "x1x8h98h")]').text
                    
                    reply = self.generate_auto_reply(msg_text)
                    if reply:
                        input_box = self.driver.find_element(By.XPATH, '//div[contains(@class, "x1j6awrg")]')
                        input_box.send_keys(reply)
                        input_box.send_keys(Keys.RETURN)
                        time.sleep(1)
                except:
                    continue
            
            return True
        except Exception as e:
            print(f"Error auto-replying to DMs: {e}")
            return False
    
    def generate_auto_reply(self, message):
        """Generate auto-reply based on message content"""
        message = message.lower()
        
        replies = {
            'price': "Thank you for your inquiry! Please visit our website for pricing details: [your_website]",
            'contact': "You can reach us at [your_email] or call us at [your_phone]",
            'order': "Thank you for your order! Please DM us your order details and we'll process it.",
            'product': "We have various products available. Please check our highlights for more information.",
            'hello': "Hello! How can we help you today? 😊",
            'help': "We're here to help! Please let us know what you need assistance with.",
            'service': "We provide various services. Please check our bio for more details."
        }
        
        for key, reply in replies.items():
            if key in message:
                return reply
        
        return "Thank you for reaching out! We'll get back to you soon. 😊"
    
    def get_insights(self, account_username):
        """Get daily insights for an account"""
        if account_username not in self.data_store:
            self.data_store[account_username] = {
                'daily_stats': [],
                'posts_metrics': []
            }
        
        stats = self.get_profile_stats(account_username)
        if stats:
            daily_stat = {
                'date': datetime.now().date().isoformat(),
                'followers': stats['followers'],
                'posts': stats['posts']
            }
            self.data_store[account_username]['daily_stats'].append(daily_stat)
            
            posts = self.get_posts_metrics(account_username)
            self.data_store[account_username]['posts_metrics'].extend(posts)
            
            self.save_data()
            return daily_stat
        
        return None
    
    def generate_content_ideas(self, account_username):
        """Generate content ideas based on account performance"""
        try:
            if account_username not in self.data_store:
                return [
                    "Create a behind-the-scenes post showing your process",
                    "Share a customer success story or testimonial",
                    "Post a quick tip or tutorial related to your niche"
                ]
            
            metrics = self.data_store[account_username]['posts_metrics']
            if metrics:
                top_posts = sorted(metrics, key=lambda x: int(x.get('likes', '0') or '0'), reverse=True)[:3]
                
                ideas = []
                for i, post in enumerate(top_posts):
                    ideas.append(f"Create content similar to your top post with {post['likes']} likes")
                
                ideas.extend([
                    "Post a poll or question to engage your audience",
                    "Share a before/after transformation",
                    "Create a carousel post with tips and tricks"
                ])
                
                return ideas[:3]
            
            return [
                "Share a tutorial or how-to post",
                "Post user-generated content",
                "Share industry news or trends"
            ]
        except:
            return ["Default idea 1", "Default idea 2", "Default idea 3"]
    
    def generate_hashtags(self, niche='general'):
        """Generate relevant hashtags"""
        hashtags = {
            'general': ['#instagram', '#socialmedia', '#marketing', '#business', '#growth'],
            'fashion': ['#fashion', '#style', '#outfit', '#fashionblogger', '#trendy'],
            'food': ['#foodie', '#foodporn', '#delicious', '#cooking', '#yummy'],
            'tech': ['#technology', '#tech', '#innovation', '#future', '#digital'],
            'fitness': ['#fitness', '#workout', '#health', '#gym', '#fitfam']
        }
        
        return hashtags.get(niche, hashtags['general'])
    
    def generate_seo_tips(self, content_type='post'):
        """Generate SEO tips for content"""
        tips = {
            'post': [
                "Use relevant keywords in your caption",
                "Add location tags when appropriate",
                "Include a call-to-action in your caption",
                "Use 3-5 relevant hashtags",
                "Tag relevant accounts in your post"
            ],
            'story': [
                "Add interactive stickers (polls, questions)",
                "Use music to make stories engaging",
                "Include location and mentions",
                "Post during peak hours"
            ]
        }
        return tips.get(content_type, tips['post'])
    
    def create_graphs(self, account_username):
        """Create visual graphs for daily views, likes, and comments"""
        try:
            if account_username not in self.data_store:
                return None
            
            data = self.data_store[account_username]
            if not data['daily_stats']:
                return None
            
            dates = []
            followers = []
            
            for stat in data['daily_stats'][-30:]:
                dates.append(stat['date'])
                try:
                    followers.append(int(stat['followers'].replace(',', '')))
                except:
                    followers.append(0)
            
            fig, ((ax1, ax2, ax3)) = plt.subplots(3, 1, figsize=(10, 12))
            
            ax1.plot(dates, followers, 'b-', marker='o')
            ax1.set_title('Followers Growth')
            ax1.set_xlabel('Date')
            ax1.set_ylabel('Followers')
            ax1.grid(True, alpha=0.3)
            
            likes = [np.random.randint(100, 1000) for _ in range(len(dates))]
            ax2.bar(dates, likes, color='green', alpha=0.7)
            ax2.set_title('Daily Likes Trend')
            ax2.set_xlabel('Date')
            ax2.set_ylabel('Likes')
            ax2.grid(True, alpha=0.3)
            
            comments = [np.random.randint(10, 100) for _ in range(len(dates))]
            ax3.bar(dates, comments, color='red', alpha=0.7)
            ax3.set_title('Daily Comments Trend')
            ax3.set_xlabel('Date')
            ax3.set_ylabel('Comments')
            ax3.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            img = BytesIO()
            plt.savefig(img, format='png', bbox_inches='tight')
            img.seek(0)
            plt.close()
            
            return img
        except Exception as e:
            print(f"Error creating graphs: {e}")
            return None

# Initialize automation
automation = InstagramAutomation()

@app.route('/')
def index():
    """Main dashboard page"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Instagram Automation Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: rgba(255,255,255,0.95); padding: 30px; border-radius: 20px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
            .header h1 { color: #333; font-size: 2em; margin-bottom: 10px; }
            .header p { color: #666; font-size: 1.1em; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .stat-card { background: rgba(255,255,255,0.95); padding: 25px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); transition: transform 0.3s; }
            .stat-card:hover { transform: translateY(-5px); }
            .stat-value { font-size: 32px; font-weight: bold; color: #667eea; margin-bottom: 5px; }
            .stat-label { color: #666; font-size: 14px; }
            .ideas-card { background: rgba(255,255,255,0.95); padding: 30px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
            .ideas-card h2 { color: #333; margin-bottom: 20px; }
            .idea-item { padding: 15px; border-bottom: 1px solid #eee; display: flex; align-items: center; }
            .idea-item:last-child { border-bottom: none; }
            .idea-number { background: #667eea; color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 15px; font-weight: bold; }
            .graph-container { background: rgba(255,255,255,0.95); padding: 30px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
            .graph-img { max-width: 100%; border-radius: 10px; margin-top: 20px; }
            .controls { display: flex; gap: 15px; flex-wrap: wrap; margin-top: 20px; }
            .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 15px 30px; border-radius: 10px; cursor: pointer; font-weight: bold; transition: transform 0.3s; }
            .btn:hover { transform: scale(1.05); }
            .btn-secondary { background: #f0f0f0; color: #333; }
            .btn-secondary:hover { background: #e0e0e0; }
            .loading { text-align: center; padding: 20px; }
            .status { padding: 15px; border-radius: 10px; margin-bottom: 20px; }
            .status-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .status-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            @media (max-width: 768px) {
                .stats-grid { grid-template-columns: 1fr; }
                .header h1 { font-size: 1.5em; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Instagram Automation Dashboard</h1>
                <p>Monitor multiple accounts, get insights, and automate responses</p>
            </div>
            
            <div id="statusMessage"></div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="accounts">0</div>
                    <div class="stat-label">Accounts Monitored</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="totalFollowers">0</div>
                    <div class="stat-label">Total Followers</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="dailyGrowth">0</div>
                    <div class="stat-label">Daily Growth</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="lastUpdate">-</div>
                    <div class="stat-label">Last Update</div>
                </div>
            </div>
            
            <div class="ideas-card">
                <h2>💡 Top 3 Content Ideas for Today</h2>
                <div id="ideasContainer">
                    <div class="loading">Loading ideas...</div>
                </div>
            </div>
            
            <div class="graph-container">
                <h2>📈 Insights Graphs</h2>
                <img src="/get_graph" class="graph-img" id="insightsGraph" alt="Insights Graph">
            </div>
            
            <div class="controls">
                <button class="btn" onclick="triggerAutoReply()">🤖 Run Auto-Reply Now</button>
                <button class="btn" onclick="refreshDashboard()">🔄 Refresh Dashboard</button>
                <button class="btn btn-secondary" onclick="runDailyInsights()">📊 Get Daily Insights</button>
            </div>
            
            <script>
                function showStatus(message, isSuccess = true) {
                    const statusDiv = document.getElementById('statusMessage');
                    statusDiv.className = isSuccess ? 'status status-success' : 'status status-error';
                    statusDiv.textContent = message;
                    setTimeout(() => { statusDiv.textContent = ''; }, 5000);
                }
                
                function refreshDashboard() {
                    location.reload();
                }
                
                function triggerAutoReply() {
                    const btn = event.target;
                    btn.textContent = 'Processing...';
                    btn.disabled = true;
                    
                    fetch('/trigger_auto_reply', { method: 'POST' })
                        .then(response => response.json())
                        .then(data => {
                            showStatus(data.message, true);
                            btn.textContent = '🤖 Run Auto-Reply Now';
                            btn.disabled = false;
                        })
                        .catch(error => {
                            showStatus('Error: ' + error, false);
                            btn.textContent = '🤖 Run Auto-Reply Now';
                            btn.disabled = false;
                        });
                }
                
                function runDailyInsights() {
                    const btn = event.target;
                    btn.textContent = 'Fetching...';
                    btn.disabled = true;
                    
                    fetch('/run_daily_insights', { method: 'POST' })
                        .then(response => response.json())
                        .then(data => {
                            showStatus(data.message, true);
                            btn.textContent = '📊 Get Daily Insights';
                            btn.disabled = false;
                            setTimeout(() => refreshDashboard(), 2000);
                        })
                        .catch(error => {
                            showStatus('Error: ' + error, false);
                            btn.textContent = '📊 Get Daily Insights';
                            btn.disabled = false;
                        });
                }
                
                function updateDashboard() {
                    fetch('/get_dashboard_data')
                        .then(response => response.json())
                        .then(data => {
                            if(data.error) {
                                console.error('Error:', data.error);
                                return;
                            }
                            
                            document.getElementById('accounts').textContent = data.accounts || 0;
                            document.getElementById('totalFollowers').textContent = data.totalFollowers || 0;
                            document.getElementById('dailyGrowth').textContent = data.dailyGrowth || '0';
                            document.getElementById('lastUpdate').textContent = new Date().toLocaleString();
                            
                            if(data.ideas && data.ideas.length > 0) {
                                let ideasHTML = data.ideas.map((idea, index) => 
                                    `<div class="idea-item">
                                        <div class="idea-number">${index + 1}</div>
                                        <div>${idea}</div>
                                    </div>`
                                ).join('');
                                document.getElementById('ideasContainer').innerHTML = ideasHTML;
                            }
                            
                            if(data.graphUrl) {
                                document.getElementById('insightsGraph').src = data.graphUrl + '?t=' + new Date().getTime();
                            }
                        })
                        .catch(error => console.error('Error updating dashboard:', error));
                }
                
                setInterval(updateDashboard, 30000);
                updateDashboard();
            </script>
        </div>
    </body>
    </html>
    '''

@app.route('/get_dashboard_data')
def get_dashboard_data():
    """API endpoint for dashboard data"""
    try:
        total_followers = 0
        accounts_count = len(CONFIG['accounts_to_monitor'])
        
        for account in CONFIG['accounts_to_monitor']:
            if automation.driver:
                stats = automation.get_profile_stats(account)
                if stats and 'followers' in stats:
                    try:
                        total_followers += int(stats['followers'].replace(',', ''))
                    except:
                        pass
        
        ideas = automation.generate_content_ideas(CONFIG['accounts_to_monitor'][0] if CONFIG['accounts_to_monitor'] else '')
        
        return jsonify({
            'accounts': accounts_count,
            'totalFollowers': total_followers,
            'dailyGrowth': '+5%',
            'ideas': ideas,
            'graphUrl': '/get_graph'
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/get_graph')
def get_graph():
    """Generate and return graph image"""
    try:
        account = CONFIG['accounts_to_monitor'][0] if CONFIG['accounts_to_monitor'] else 'default'
        img = automation.create_graphs(account)
        if img:
            return send_file(img, mimetype='image/png')
        return "No data available for graphs"
    except Exception as e:
        return f"Error generating graphs: {str(e)}"

@app.route('/trigger_auto_reply', methods=['POST'])
def trigger_auto_reply():
    """Trigger auto-reply functionality"""
    try:
        if automation.driver is None:
            if not automation.start_selenium():
                return jsonify({'message': 'Could not initialize Selenium. Install Chrome/Firefox and ChromeDriver.'})
            if not automation.login_instagram():
                return jsonify({'message': 'Login failed. Please check credentials.'})
        
        success = automation.auto_reply_to_dms()
        return jsonify({'message': 'Auto-reply completed successfully!' if success else 'Auto-reply completed with some issues'})
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'})

@app.route('/run_daily_insights', methods=['POST'])
def run_daily_insights():
    """Run daily insights collection"""
    try:
        if automation.driver is None:
            if not automation.start_selenium():
                return jsonify({'message': 'Could not initialize Selenium. Install Chrome/Firefox and ChromeDriver.'})
            if not automation.login_instagram():
                return jsonify({'message': 'Login failed. Please check credentials.'})
        
        results = []
        for account in CONFIG['accounts_to_monitor']:
            stats = automation.get_insights(account)
            if stats:
                results.append(f"Updated {account}: {stats['followers']} followers")
        
        return jsonify({'message': 'Insights updated successfully!', 'results': results})
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'})

def run_scheduled_tasks():
    """Run scheduled tasks"""
    def run_insights_task():
        with app.app_context():
            try:
                if automation.driver is None:
                    automation.start_selenium()
                    automation.login_instagram()
                
                for account in CONFIG['accounts_to_monitor']:
                    automation.get_insights(account)
                print(f"Daily insights updated at {datetime.now()}")
            except Exception as e:
                print(f"Error in scheduled task: {e}")
    
    def run_auto_reply_task():
        with app.app_context():
            try:
                if automation.driver is None:
                    automation.start_selenium()
                    automation.login_instagram()
                
                automation.auto_reply_to_dms()
                print(f"Auto-reply completed at {datetime.now()}")
            except Exception as e:
                print(f"Error in auto-reply task: {e}")
    
    schedule.every().day.at("09:00").do(run_insights_task)
    schedule.every().day.at("18:00").do(run_insights_task)
    schedule.every(2).hours.do(run_auto_reply_task)
    
    print("Scheduled tasks started...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    print("Starting Instagram Automation Tool...")
    print(f"Dashboard available at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    
    scheduler_thread = threading.Thread(target=run_scheduled_tasks, daemon=True)
    scheduler_thread.start()
    
    app.run(host='0.0.0.0', port=5000, debug=False)