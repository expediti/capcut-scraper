#!/usr/bin/env python3
"""
Manual CapCut Template Processor
Input template URLs manually, get Catbox links automatically
"""

import requests
import re
import os
import cv2
import tempfile
import json
import csv
from urllib.parse import urlparse

class ManualTemplateProcessor:
    def __init__(self):
        self.templates = []
        os.makedirs('output', exist_ok=True)
        os.makedirs('temp', exist_ok=True)
    
    def upload_to_catbox(self, file_path):
        """Upload file to Catbox"""
        try:
            print(f"📤 Uploading to Catbox: {os.path.basename(file_path)}")
            
            with open(file_path, 'rb') as f:
                files = {'fileToUpload': f}
                data = {'reqtype': 'fileupload'}
                
                response = requests.post(
                    'https://catbox.moe/user/api.php',
                    files=files,
                    data=data,
                    timeout=30
                )
            
            if response.status_code == 200 and response.text.startswith('https://'):
                url = response.text.strip()
                print(f"✅ Uploaded: {url}")
                return url
            else:
                print(f"❌ Upload failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return None
    
    def extract_template_id(self, url):
        """Extract template ID from CapCut URL"""
        patterns = [
            r'template_id=(\d+)',
            r'template-detail/[^/]+/(\d+)',
            r'/(\d{16,20})/?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def generate_capcut_link(self, template_id):
        """Generate CapCut app link"""
        if not template_id:
            return None
        
        return f"https://capcut-yt.onelink.me/W3Oy/cw7bmax3?af_dp=capcut%3A%2F%2Ftemplate%2Fdetail%3Fenter_app%3Dother%26enter_from%3DSEO_detail_page%26template_id%3D{template_id}%26template_language%3DNone&af_xp=social&deep_link_sub1=%7B%22share_token%22%3A%22None%22%7D&deep_link_value=capcut%253A%252F%252Ftemplate%252Fdetail%253Fenter_app%253Dother%2526enter_from%253DSEO_detail_page%2526template_id%253D{template_id}%2526template_language%253DNone&is_retargeting=true&pid=SEO_detail"
    
    def download_video(self, video_url, filename):
        """Download video from URL"""
        try:
            print(f"📥 Downloading video...")
            
            response = requests.get(video_url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ Downloaded: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
    
    def extract_thumbnail(self, video_path, thumbnail_path):
        """Extract thumbnail from video"""
        try:
            print(f"📸 Extracting thumbnail...")
            
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 30)  # Frame at 1 second
            
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                cv2.imwrite(thumbnail_path, frame)
                print(f"✅ Thumbnail created: {thumbnail_path}")
                return thumbnail_path
            else:
                print("❌ Could not extract thumbnail")
                return None
                
        except Exception as e:
            print(f"❌ Thumbnail error: {e}")
            return None
    
    def process_template(self, title, video_url, template_url=None):
        """Process a single template"""
        print(f"\n🔄 Processing: {title}")
        
        # Extract template ID
        template_id = None
        if template_url:
            template_id = self.extract_template_id(template_url)
        
        # Generate filenames
        safe_title = re.sub(r'[^\w\s-]', '', title).strip()[:50]
        video_file = f"temp/{safe_title}_{template_id or 'manual'}.mp4"
        thumb_file = f"temp/{safe_title}_{template_id or 'manual'}.jpg"
        
        # Download video
        if not self.download_video(video_url, video_file):
            return None
        
        # Extract thumbnail
        if not self.extract_thumbnail(video_file, thumb_file):
            return None
        
        # Upload to Catbox
        print("📤 Uploading video to Catbox...")
        video_catbox_url = self.upload_to_catbox(video_file)
        
        print("📤 Uploading thumbnail to Catbox...")
        thumb_catbox_url = self.upload_to_catbox(thumb_file)
        
        # Clean up
        try:
            os.remove(video_file)
            os.remove(thumb_file)
        except:
            pass
        
        if video_catbox_url and thumb_catbox_url:
            template_data = {
                'title': title,
                'template_id': template_id,
                'capcut_link': self.generate_capcut_link(template_id) if template_id else '',
                'video_url': video_catbox_url,
                'thumbnail_url': thumb_catbox_url,
                'original_url': template_url or '',
                'video_source': video_url
            }
            
            self.templates.append(template_data)
            print(f"✅ Successfully processed: {title}")
            return template_data
        else:
            print(f"❌ Failed to upload: {title}")
            return None
    
    def export_csv(self, filename='manual_templates.csv'):
        """Export to CSV"""
        filepath = os.path.join('output', filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['title', 'template_id', 'capcut_link', 'video_url', 'thumbnail_url', 'original_url']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for template in self.templates:
                writer.writerow({
                    'title': template['title'],
                    'template_id': template['template_id'] or '',
                    'capcut_link': template['capcut_link'],
                    'video_url': template['video_url'],
                    'thumbnail_url': template['thumbnail_url'],
                    'original_url': template['original_url']
                })
        
        print(f"✅ Exported to {filepath}")
        return filepath

def main():
    """Manual template processing"""
    processor = ManualTemplateProcessor()
    
    print("🎬 Manual CapCut Template Processor")
    print("=" * 40)
    print("Enter template details (press Enter on empty title to finish)")
    
    while True:
        print("\n" + "─" * 40)
        title = input("📝 Template title: ").strip()
        
        if not title:
            break
        
        video_url = input("🎥 Video URL (direct .mp4 link): ").strip()
        template_url = input("🔗 CapCut template URL (optional): ").strip()
        
        if video_url:
            processor.process_template(title, video_url, template_url or None)
        else:
            print("❌ Video URL required!")
    
    if processor.templates:
        processor.export_csv()
        print(f"\n🎉 Processed {len(processor.templates)} templates!")
        print("📁 Check output/manual_templates.csv")
    else:
        print("⚠️ No templates processed")

if __name__ == "__main__":
    main()
