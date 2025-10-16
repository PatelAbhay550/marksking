from flask import url_for, make_response
import xml.etree.ElementTree as ET
from datetime import datetime

def generate_sitemap():
    """Generate XML sitemap for SEO"""
    
    # Root element
    urlset = ET.Element('urlset')
    urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    
    # Current date
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # URLs to include in sitemap
    urls = [
        {
            'loc': '/',
            'changefreq': 'weekly',
            'priority': '1.0',
            'lastmod': current_date
        },
        {
            'loc': '/mts',
            'changefreq': 'monthly', 
            'priority': '0.8',
            'lastmod': current_date
        },
        {
            'loc': '/ssc-je',
            'changefreq': 'monthly',
            'priority': '0.8', 
            'lastmod': current_date
        },
        {
            'loc': '/chsl',
            'changefreq': 'monthly',
            'priority': '0.8',
            'lastmod': current_date
        }
    ]
    
    # Create URL elements
    for url_data in urls:
        url_elem = ET.SubElement(urlset, 'url')
        
        loc_elem = ET.SubElement(url_elem, 'loc')
        loc_elem.text = f"https://marksking.vercel.app{url_data['loc']}"
        
        lastmod_elem = ET.SubElement(url_elem, 'lastmod')
        lastmod_elem.text = url_data['lastmod']
        
        changefreq_elem = ET.SubElement(url_elem, 'changefreq')
        changefreq_elem.text = url_data['changefreq']
        
        priority_elem = ET.SubElement(url_elem, 'priority')
        priority_elem.text = url_data['priority']
    
    # Convert to string
    xml_str = ET.tostring(urlset, encoding='unicode', method='xml')
    xml_formatted = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
    
    return xml_formatted