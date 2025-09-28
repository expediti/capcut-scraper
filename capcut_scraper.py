#!/usr/bin/env python3
"""
CapCut Template Scraper with Catbox Integration
Scrapes CapCut templates, uploads videos/thumbnails to Catbox, generates CSV
"""

import requests
import json
import time
import re
import os
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin, quote
import subprocess
from PIL import Image
import cv2
import tempfile

class CapCutCatboxScraper:
    def __init__(self):
        self.session = requests.Session()
        self.templates = []
        self.setup_session()
        self.setup_driver()
        
        # Create output directories
        os.makedirs('downloads/videos', exist_ok=True)
        os.makedirs('downloads/thumbnails', exist_ok=True)
        os.makedirs('output', exist_ok=True)
    
    def setup_session(self):
        """Setup requests session with headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Chrome WebDriver initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Chrome WebDriver: {e}")
            print("💡 Please install ChromeDriver: https://chromedriver.chromium.org/")
            raise
    
    def upload_to_catbox(self, file_path):
        """Upload file to Catbox.moe and return URL"""
        try:
            print(f"📤 Uploading to Catbox: {os.path.basename(file_path)}")
            
            with open(file_path, 'rb') as f:
                files = {'fileToUpload': f}
                data = {'reqtype': 'fileupload'}
                
                # Upload to Catbox
                response = requests.post(
                    'https://catbox.moe/user/api.php',
                    files=files,
                    data=data,
                    timeout=60
                )
            
            if response.status_code == 200:
                catbox_url = response.text.strip()
                if catbox_url.startswith('https://'):
                    print(f"✅ Uploaded: {catbox_url}")
                    return catbox_url
                else:
                    print(f"❌ Upload failed: {catbox_url}")
                    return None
            else:
                print(f"❌ Upload failed: Status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Catbox upload error: {e}")
            return None
    
    def extract_video_thumbnail(self, video_path, output_path, timestamp=2.0):
        """Extract thumbnail from video using OpenCV"""
        try:
            print(f"📸 Extracting thumbnail from {os.path.basename(video_path)}")
            
            # Open video file
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                print("❌ Could not open video file")
                return None
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = total_frames / fps if fps > 0 else 0
            
            # Calculate frame number (use middle of video if timestamp is too high)
            if timestamp > duration:
                timestamp = duration / 2
            
            frame_number = int(timestamp * fps)
            
            # Seek to the frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            # Read the frame
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Save the frame as thumbnail
                cv2.imwrite(output_path, frame)
                print(f"✅ Thumbnail saved: {os.path.basename(output_path)}")
                return output_path
            else:
                print("❌ Could not read frame from video")
                return None
                
        except Exception as e:
            print(f"❌ Thumbnail extraction error: {e}")
            return None
    
    def download_video(self, video_url, output_path):
        """Download video from URL"""
        try:
            print(f"📥 Downloading video: {os.path.basename(output_path)}")
            
            response = self.session.get(video_url, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Show progress
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r📥 Progress: {progress:.1f}%", end='', flush=True)
            
            print(f"\n✅ Downloaded: {os.path.basename(output_path)}")
            return output_path
            
        except Exception as e:
            print(f"\n❌ Video download error: {e}")
            return None
    
    def extract_template_id(self, url):
        """Extract CapCut template ID from URL"""
        patterns = [
            r'template_id=(\d+)',
            r'template-detail/[^/]+/(\d+)',
            r'/(\d{19})/?$',
            r'template/(\d+)',
            r'/(\d{16,20})/?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def generate_capcut_link(self, template_id):
        """Generate CapCut app deep link"""
        if not template_id:
            return None
        
        # CapCut deep link format
        deep_link = f"https://capcut-yt.onelink.me/W3Oy/cw7bmax3?af_dp=capcut%3A%2F%2Ftemplate%2Fdetail%3Fenter_app%3Dother%26enter_from%3DSEO_detail_page%26template_id%3D{template_id}%26template_language%3DNone&af_xp=social&deep_link_sub1=%7B%22share_token%22%3A%22None%22%7D&deep_link_value=capcut%253A%252F%252Ftemplate%252Fdetail%253Fenter_app%253Dother%2526enter_from%253DSEO_detail_page%2526template_id%253D{template_id}%2526template_language%253DNone&is_retargeting=true&pid=SEO_detail"
        
        return deep_link
    
    def scrape_template_page(self, template_url):
        """Scrape individual template page"""
        try:
            print(f"\n🔍 Scraping: {template_url}")
            
            # Load page
            self.driver.get(template_url)
            time.sleep(3)
            
            # Wait for content to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "video"))
                )
            except:
                print("⚠️ No video element found")
            
            # Get page source
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract template data
            template_data = {
                'web_url': template_url,
                'title': self.extract_title(soup),
                'template_id': self.extract_template_id(template_url),
                'description': self.extract_description(soup),
                'tags': self.extract_tags(soup),
                'duration': self.extract_duration(soup),
                'video_url': None,
                'thumbnail_url': None,
                'capcut_link': None
            }
            
            # Extract video URL
            video_url = self.extract_video_url(soup)
            
            if not video_url:
                print("❌ No video URL found")
                return None
            
            # Generate CapCut deep link
            if template_data['template_id']:
                template_data['capcut_link'] = self.generate_capcut_link(template_data['template_id'])
            
            # Download video
            video_filename = f"{template_data['template_id'] or 'unknown'}_{int(time.time())}.mp4"
            video_path = os.path.join('downloads/videos', video_filename)
            
            if self.download_video(video_url, video_path):
                # Extract thumbnail
                thumbnail_filename = f"{template_data['template_id'] or 'unknown'}_{int(time.time())}.jpg"
                thumbnail_path = os.path.join('downloads/thumbnails', thumbnail_filename)
                
                if self.extract_video_thumbnail(video_path, thumbnail_path):
                    # Upload both to Catbox
                    print("📤 Uploading video to Catbox...")
                    template_data['video_url'] = self.upload_to_catbox(video_path)
                    
                    print("📤 Uploading thumbnail to Catbox...")
                    template_data['thumbnail_url'] = self.upload_to_catbox(thumbnail_path)
                    
                    # Clean up local files
                    try:
                        os.remove(video_path)
                        os.remove(thumbnail_path)
                        print("🗑️ Cleaned up local files")
                    except:
                        pass
            
            if template_data['video_url'] and template_data['thumbnail_url']:
                print(f"✅ Successfully processed: {template_data['title']}")
                return template_data
            else:
                print("❌ Failed to upload to Catbox")
                return None
                
        except Exception as e:
            print(f"❌ Error scraping template: {e}")
            return None
    
    def extract_title(self, soup):
        """Extract template title"""
        selectors = [
            'h1[class*="title"]',
            'h1[data-testid*="title"]',
            '.template-title',
            'h1',
            '[class*="template"] h1'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 3:
                    return title
        
        return "Untitled Template"
    
    def extract_description(self, soup):
        """Extract template description"""
        selectors = [
            'meta[name="description"]',
            'meta[property="og:description"]',
            '.description',
            '.template-description'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '')
                else:
                    return element.get_text(strip=True)
        
        return ""
    
    def extract_tags(self, soup):
        """Extract template tags"""
        tags = []
        
        # Look for keywords in meta tags
        keywords = soup.find('meta', attrs={'name': 'keywords'})
        if keywords:
            content = keywords.get('content', '')
            tags.extend([tag.strip() for tag in content.split(',') if tag.strip()])
        
        # Look for hashtags in page content
        text_content = soup.get_text()
        hashtags = re.findall(r'#(\w+)', text_content)
        tags.extend(hashtags[:5])
        
        return list(set(tags))[:5]  # Remove duplicates and limit
    
    def extract_duration(self, soup):
        """Extract video duration"""
        # Try to find duration in various formats
        duration_patterns = [
            r'(\d+):(\d+)',  # MM:SS
            r'(\d+)s',       # Xs
            r'(\d+)\s*sec',  # X sec
        ]
        
        text_content = soup.get_text()
        for pattern in duration_patterns:
            match = re.search(pattern, text_content)
            if match:
                return match.group(0)
        
        return "0:15"  # Default
    
    def extract_video_url(self, soup):
        """Extract video URL from page"""
        # Try multiple methods to find video URL
        
        # Method 1: Look for video elements
        video_elements = soup.find_all('video')
        for video in video_elements:
            src = video.get('src')
            if src and src.startswith(('http', '//')):
                if src.startswith('//'):
                    src = 'https:' + src
                return src
            
            # Check source elements
            sources = video.find_all('source')
            for source in sources:
                src = source.get('src')
                if src and src.startswith(('http', '//')):
                    if src.startswith('//'):
                        src = 'https:' + src
                    return src
        
        # Method 2: Use Selenium to get video src
        try:
            video_element = self.driver.find_element(By.TAG_NAME, "video")
            src = video_element.get_attribute('src')
            if src:
                return src
        except:
            pass
        
        # Method 3: Look for video URLs in page source
        page_source = self.driver.page_source
        video_patterns = [
            r'https://[^"\s]+\.mp4[^"\s]*',
            r'https://[^"\s]+/video/[^"\s]+',
            r'"(https://[^"]+\.mp4[^"]*)"'
        ]
        
        for pattern in video_patterns:
            matches = re.findall(pattern, page_source)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if 'mp4' in match.lower():
                    return match
        
        return None
    
    def search_templates(self, query, max_results=20):
        """Search for templates by query"""
        print(f"\n🔍 Searching for: '{query}'")
        
        # CapCut search URL
        search_url = f"https://www.capcut.com/explore?q={quote(query)}"
        
        try:
            self.driver.get(search_url)
            time.sleep(5)
            
            # Scroll to load more results
            for i in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            # Find template links
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            template_links = []
            
            # Look for template links
            link_selectors = [
                'a[href*="/template-detail/"]',
                'a[href*="/explore/"]',
                '.template-item a',
                '.template-card a'
            ]
            
            for selector in link_selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href and 'template-detail' in href:
                        full_url = urljoin('https://www.capcut.com', href)
                        if full_url not in template_links:
                            template_links.append(full_url)
            
            print(f"📋 Found {len(template_links)} template links")
            
            # Process templates
            processed = 0
            for url in template_links[:max_results]:
                template_data = self.scrape_template_page(url)
                if template_data:
                    self.templates.append(template_data)
                    processed += 1
                
                # Delay between requests
                time.sleep(3)
                
                if processed >= max_results:
                    break
            
            print(f"✅ Successfully processed {processed} templates for '{query}'")
            
        except Exception as e:
            print(f"❌ Search error for '{query}': {e}")
    
    def export_to_csv(self, filename='capcut_templates.csv'):
        """Export templates to CSV file"""
        if not self.templates:
            print("⚠️ No templates to export")
            return
        
        filepath = os.path.join('output', filename)
        
        print(f"📊 Exporting {len(self.templates)} templates to {filepath}")
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'title',
                'template_id', 
                'capcut_link',
                'video_url',
                'thumbnail_url',
                'web_url',
                'description',
                'tags',
                'duration'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for template in self.templates:
                writer.writerow({
                    'title': template.get('title', ''),
                    'template_id': template.get('template_id', ''),
                    'capcut_link': template.get('capcut_link', ''),
                    'video_url': template.get('video_url', ''),
                    'thumbnail_url': template.get('thumbnail_url', ''),
                    'web_url': template.get('web_url', ''),
                    'description': template.get('description', ''),
                    'tags': ', '.join(template.get('tags', [])),
                    'duration': template.get('duration', '')
                })
        
        print(f"✅ Exported to {filepath}")
        return filepath
    
    def export_to_json(self, filename='capcut_templates.json'):
        """Export templates to JSON file"""
        if not self.templates:
            print("⚠️ No templates to export")
            return
        
        filepath = os.path.join('output', filename)
        
        print(f"📊 Exporting {len(self.templates)} templates to {filepath}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.templates, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported to {filepath}")
        return filepath
    
    def close(self):
        """Close the browser"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            print("🔒 Browser closed")

def main():
    """Main function to run the scraper"""
    print("🚀 CapCut Template Scraper with Catbox Integration")
    print("=" * 50)
    
    scraper = CapCutCatboxScraper()
    
    try:
        # Search queries
        queries = [
            'phonk',
            'viral transition',
            'aesthetic',
            'instagram reel',
            'tiktok trending'
        ]
        
        # Scrape templates for each query
        for query in queries:
            scraper.search_templates(query, max_results=5)  # 5 templates per query
            time.sleep(10)  # Delay between searches
        
        # Export results
        if scraper.templates:
            csv_file = scraper.export_to_csv()
            json_file = scraper.export_to_json()
            
            print(f"\n🎉 Scraping Complete!")
            print(f"📊 Total templates: {len(scraper.templates)}")
            print(f"📁 Files created:")
            print(f"   - {csv_file}")
            print(f"   - {json_file}")
            print(f"\n💡 CSV contains all links ready for Supabase upload!")
        else:
            print("⚠️ No templates were successfully scraped")
    
    except KeyboardInterrupt:
        print("\n⏹️ Scraping stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
