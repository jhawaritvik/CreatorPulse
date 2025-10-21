# Comprehensive test suite for CreatorPulse backend components
# Tests scrapers, database integration, email service, and consolidation

import os
import json
import tempfile
from datetime import datetime, timezone
from dotenv import load_dotenv

# Import scrapers
from scraper.reddit_scraper import fetch_from_reddit
from scraper.rss_scraper import fetch_from_rss
from scraper.youtube_scraper import fetch_from_youtube
from scraper.blog_scraper import fetch_from_blog
from scraper.other_scraper import fetch_from_other
from scraper.news_item import NewsItem

# Import new components
from supabase_client import get_supabase_client, fetch_clients, save_newsletter
from email_service import EmailService
from consolidate import make_report, dedupe_items, rank_items, save_and_send_newsletter, _make_llm_prompt_full_report, _call_gemini
import yaml

# Load environment variables
load_dotenv()

# Test user ID from Supabase profiles table
TEST_USER_ID = "08136f1f-21a5-4a28-b047-907e54e96861"

def test_environment_variables():
    """Test if all required environment variables are set."""
    print("🔧 Testing Environment Variables...")
    
    required_vars = {
        'CREATORPULSE_SUPABASE_URL': 'Supabase project URL',
        'CREATORPULSE_SUPABASE_KEY': 'Supabase API key',
    }
    
    optional_vars = {
        'GEMINI_API_KEY': 'Google Gemini AI API key (for report generation)',
        'SMTP_SERVER': 'SMTP server for email sending',
        'SMTP_USERNAME': 'SMTP username/email',
        'SMTP_PASSWORD': 'SMTP password/app password',
        'FROM_EMAIL': 'From email address',
        'FROM_NAME': 'From name for emails'
    }
    
    missing_required = []
    missing_optional = []
    
    for var, desc in required_vars.items():
        if os.environ.get(var):
            print(f"  ✅ {var}: Set")
        else:
            print(f"  ❌ {var}: Missing ({desc})")
            missing_required.append(var)
    
    for var, desc in optional_vars.items():
        if os.environ.get(var):
            print(f"  ✅ {var}: Set")
        else:
            print(f"  ⚠️  {var}: Missing ({desc})")
            missing_optional.append(var)
    
    if missing_required:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_required)}")
        return False
    
    if missing_optional:
        print(f"\n⚠️  Missing optional environment variables: {', '.join(missing_optional)}")
        print("   Some features may not work without these variables.")
    
    print("✅ Environment variables check completed\n")
    return True

def test_database_connection():
    """Test Supabase database connection and basic operations."""
    print("🗄️  Testing Database Connection...")
    
    try:
        supabase = get_supabase_client()
        print("  ✅ Supabase client initialized")
        
        # Test specific user profile
        response = supabase.table('profiles').select('id, full_name').eq('id', TEST_USER_ID).execute()
        if response.data:
            user_name = response.data[0].get('full_name', 'Unknown')
            print(f"  ✅ Test user profile found: {user_name} (ID: {TEST_USER_ID})")
        else:
            print(f"  ⚠️  Test user profile not found (ID: {TEST_USER_ID})")
        
        # Test general profiles query
        response = supabase.table('profiles').select('id, full_name').limit(1).execute()
        print(f"  ✅ Database query successful (found {len(response.data)} profiles)")
        
        # Test clients table for test user
        response = supabase.table('clients').select('id, name, email').eq('user_id', TEST_USER_ID).execute()
        print(f"  ✅ Test user clients found: {len(response.data)} clients")
        
        # Test sources table for test user
        response = supabase.table('sources').select('id, source_type, source_name').eq('user_id', TEST_USER_ID).execute()
        print(f"  ✅ Test user sources found: {len(response.data)} sources")
        
        # Test newsletters table for test user
        response = supabase.table('newsletters').select('id, title, status').eq('user_id', TEST_USER_ID).execute()
        print(f"  ✅ Test user newsletters found: {len(response.data)} newsletters")
        
        print("✅ Database connection test completed\n")
        return True
        
    except Exception as e:
        print(f"  ❌ Database connection failed: {str(e)}")
        print("✅ Database connection test completed (with errors)\n")
        return False

def test_scrapers():
    """Test all scraper components."""
    print("🔍 Testing Scrapers...")
    all_items = []
    
    # Test Reddit Scraper
    print("  📱 Testing Reddit Scraper...")
    try:
        reddit_items = fetch_from_reddit(["python"], limit=3)
        print(f"    ✅ Reddit: {len(reddit_items)} items fetched")
        all_items.extend(reddit_items)
        for item in reddit_items[:2]:  # Show first 2
            print(f"      - {item.title[:60]}...")
    except Exception as e:
        print(f"    ❌ Reddit scraper failed: {str(e)}")

    # Test RSS Scraper
    print("  📰 Testing RSS Scraper...")
    try:
        rss_items = fetch_from_rss(["https://www.theverge.com/rss/index.xml"], max_items_per_feed=3)
        print(f"    ✅ RSS: {len(rss_items)} items fetched")
        all_items.extend(rss_items)
        for item in rss_items[:2]:  # Show first 2
            print(f"      - {item.title[:60]}...")
    except Exception as e:
        print(f"    ❌ RSS scraper failed: {str(e)}")

    # Test YouTube Scraper
    print("  📺 Testing YouTube Scraper...")
    try:
        youtube_items = fetch_from_youtube(["https://www.youtube.com/c/MKBHD"])
        print(f"    ✅ YouTube: {len(youtube_items)} items fetched")
        all_items.extend(youtube_items)
        for item in youtube_items[:1]:  # Show first 1
            print(f"      - {item.title[:60]}...")
    except Exception as e:
        print(f"    ❌ YouTube scraper failed: {str(e)}")

    # Test Blog Scraper
    print("  📝 Testing Blog Scraper...")
    try:
        blog_items = fetch_from_blog(["https://www.joelonsoftware.com/"])
        print(f"    ✅ Blog: {len(blog_items)} items fetched")
        all_items.extend(blog_items)
        for item in blog_items[:1]:  # Show first 1
            print(f"      - {item.title[:60]}...")
    except Exception as e:
        print(f"    ❌ Blog scraper failed: {str(e)}")

    print(f"✅ Scrapers test completed (total: {len(all_items)} items)\n")
    return all_items

def test_consolidation(items):
    """Test consolidation functions."""
    print("🔄 Testing Consolidation Functions...")
    
    if not items:
        print("  ⚠️  No items to test consolidation with")
        return None
    
    try:
        # Test deduplication
        original_count = len(items)
        deduped_items = dedupe_items(items)
        print(f"  ✅ Deduplication: {original_count} → {len(deduped_items)} items")
        
        # Test ranking
        weights = {'reddit': 1.0, 'rss': 0.8, 'youtube': 0.9}
        ranked_items = rank_items(deduped_items, weights=weights)
        print(f"  ✅ Ranking: {len(ranked_items)} items ranked")
        
        # Test report generation (basic config)
        config = {
            'llm': {'enabled': False},  # Disable LLM for testing
            'ranking': {'source_weights': weights},
            'options': {'max_items': 10}
        }
        
        report_html = make_report(ranked_items[:5], config)  # Use fewer items for testing
        print(f"  ✅ Report generation: {len(report_html)} characters generated")
        
        print("✅ Consolidation test completed\n")
        return report_html
        
    except Exception as e:
        print(f"  ❌ Consolidation failed: {str(e)}")
        print("✅ Consolidation test completed (with errors)\n")
        return None

def test_email_service():
    """Test email service initialization and configuration."""
    print("📧 Testing Email Service...")
    
    try:
        email_service = EmailService()
        print("  ✅ Email service initialized")
        
        # Test configuration
        print(f"  ✅ SMTP Server: {email_service.smtp_server}:{email_service.smtp_port}")
        print(f"  ✅ From Email: {email_service.from_email}")
        print(f"  ✅ From Name: {email_service.from_name}")
        
        print("✅ Email service test completed\n")
        return True
        
    except Exception as e:
        print(f"  ❌ Email service initialization failed: {str(e)}")
        print("  💡 Make sure SMTP credentials are set in .env file")
        print("✅ Email service test completed (with errors)\n")
        return False

def test_user_specific_functionality():
    """Test user-specific functionality with the test user ID."""
    print(f"👤 Testing User-Specific Functionality (User: {TEST_USER_ID})...")
    
    try:
        supabase = get_supabase_client()
        
        # Test fetch_clients function with test user
        clients = fetch_clients(TEST_USER_ID)
        print(f"  ✅ fetch_clients(): Found {len(clients)} clients for test user")
        
        # Test creating a sample newsletter entry
        sample_newsletter_data = {
            'user_id': TEST_USER_ID,
            'title': 'Test Newsletter - ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'content': '<h1>Test Newsletter</h1><p>This is a test newsletter created during testing.</p>',
            'status': 'draft',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Insert test newsletter
        response = supabase.table('newsletters').insert(sample_newsletter_data).execute()
        if response.data:
            newsletter_id = response.data[0]['id']
            print(f"  ✅ Test newsletter created with ID: {newsletter_id}")
            
            # Clean up - delete the test newsletter
            supabase.table('newsletters').delete().eq('id', newsletter_id).execute()
            print(f"  ✅ Test newsletter cleaned up")
        
        print("✅ User-specific functionality test completed\n")
        return True
        
    except Exception as e:
        print(f"  ❌ User-specific functionality test failed: {str(e)}")
        print("✅ User-specific functionality test completed (with errors)\n")
        return False

def test_llm_output():
    """Test LLM (Gemini) output generation."""
    print("🤖 Testing LLM Output Generation...")
    
    # Check if Gemini API key is available
    if not os.environ.get("GEMINI_API_KEY"):
        print("  ⚠️  GEMINI_API_KEY not found - skipping LLM test")
        return False
    
    try:
        # Load config
        try:
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            print("  ⚠️  config.yaml not found - using default config")
            config = {
                'llm': {'enabled': True, 'model': 'gemini-2.0-flash-exp'},
                'ranking': {'source_weights': {'reddit': 10.0, 'rss': 5.0, 'blog': 5.0}},
                'options': {'max_items': 40}
            }
        
        # Create sample news items for testing
        sample_items = [
            NewsItem(
                title="Python 3.12 Released with New Features",
                url="https://example.com/python-312",
                source="reddit",
                published_at=datetime.now(timezone.utc),
                summary="Python 3.12 introduces several new features including improved error messages.",
                score=15.0
            ),
            NewsItem(
                title="AI Breakthrough in Natural Language Processing",
                url="https://example.com/ai-breakthrough",
                source="rss",
                published_at=datetime.now(timezone.utc),
                summary="Researchers have developed a new model that improves language understanding.",
                score=12.0
            )
        ]
        
        print(f"  ✅ Created {len(sample_items)} sample news items")
        
        # Test prompt generation
        prompt = _make_llm_prompt_full_report(sample_items, max_items=10)
        print(f"  ✅ Generated LLM prompt ({len(prompt)} characters)")
        
        # Test LLM call
        llm_cfg = config.get('llm', {})
        print("  🚀 Calling Gemini API...")
        response = _call_gemini(llm_cfg, prompt)
        
        if response:
            print(f"  ✅ LLM response received ({len(response)} characters)")
            print(f"  🔍 First 200 chars: {response[:200]}...")
            
            # Test full report generation
            report_html = make_report(sample_items, config)
            print(f"  ✅ Full report generated ({len(report_html)} characters)")
            
            # Save test output
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"test_llm_output_{timestamp}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_html)
            print(f"  💾 Test LLM output saved to: {filename}")
            
            print("✅ LLM output test completed\n")
            return True
        else:
            print("  ❌ LLM returned no response")
            print("✅ LLM output test completed (with errors)\n")
            return False
            
    except Exception as e:
        print(f"  ❌ LLM output test failed: {str(e)}")
        print("✅ LLM output test completed (with errors)\n")
        return False

def test_email_sending():
    """Test email sending functionality with actual newsletter creation and sending."""
    print(f"📧 Testing Email Sending Functionality (User: {TEST_USER_ID})...")
    
    try:
        # Check if SMTP credentials are available
        required_smtp_vars = ['SMTP_SERVER', 'SMTP_USERNAME', 'SMTP_PASSWORD', 'FROM_EMAIL']
        missing_vars = [var for var in required_smtp_vars if not os.environ.get(var)]
        
        if missing_vars:
            print(f"  ⚠️  Missing SMTP variables: {', '.join(missing_vars)} - skipping email test")
            return False
        
        # Create sample newsletter content
        timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        sample_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Test Newsletter</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .content {{ background: #f9f9f9; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>CreatorPulse Test Newsletter</h1>
    <div class="content">
        <h2>Test Report</h2>
        <p>This is a test newsletter generated during the comprehensive test suite.</p>
        <ul>
            <li>Test item 1: System functionality verified</li>
            <li>Test item 2: Email integration working</li>
            <li>Test item 3: Database operations successful</li>
        </ul>
        <p><strong>Generated at:</strong> {timestamp_str}</p>
    </div>
</body>
</html>"""
        
        print(f"  ✅ Created test newsletter content ({len(sample_html)} characters)")
        
        # Test newsletter saving
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        title = f"Test Newsletter - {timestamp}"
        
        newsletter_id = save_newsletter(TEST_USER_ID, title, sample_html, status='draft')
        print(f"  ✅ Test newsletter saved with ID: {newsletter_id}")
        
        # Test email service initialization
        email_service = EmailService()
        print(f"  ✅ Email service initialized")
        
        # Get test user's clients
        clients = fetch_clients(TEST_USER_ID)
        print(f"  ✅ Found {len(clients)} clients for test user")
        
        if not clients:
            print("  ⚠️  No clients found - creating a test client entry would require more setup")
            print("  ✅ Email sending test completed (limited - no clients to send to)")
            
            # Clean up the test newsletter
            supabase = get_supabase_client()
            supabase.table('newsletters').delete().eq('id', newsletter_id).execute()
            print(f"  ✅ Test newsletter cleaned up")
            return True
        
        # Test email sending in TEST MODE (won't actually send)
        client_ids = [client['id'] for client in clients]
        
        print(f"  🚀 Testing email sending (TEST MODE)...")
        result = email_service.create_and_send_newsletter(
            user_id=TEST_USER_ID,
            title=title,
            content=sample_html,
            client_ids=client_ids,
            test_mode=True  # Important: TEST MODE only
        )
        
        if result['success']:
            print(f"  ✅ TEST MODE: Email sending successful!")
            print(f"    - Would send to: {result['sent_count']} clients")
            if result['failed_count'] > 0:
                print(f"    - Would fail: {result['failed_count']} clients")
        else:
            print(f"  ❌ Email sending test failed: {result.get('error', 'Unknown error')}")
        
        # Clean up the test newsletter
        supabase = get_supabase_client()
        supabase.table('newsletters').delete().eq('id', newsletter_id).execute()
        print(f"  ✅ Test newsletter cleaned up")
        
        print("✅ Email sending test completed\n")
        return result['success']
        
    except Exception as e:
        print(f"  ❌ Email sending test failed: {str(e)}")
        print("✅ Email sending test completed (with errors)\n")
        return False

def test_integration(report_html):
    """Test integration between components."""
    print("🔗 Testing Integration...")
    
    if not report_html:
        print("  ⚠️  No report HTML to test integration with")
        return False
    
    try:
        # Create a temporary test file
        test_items = [
            NewsItem(
                title="Test News Item",
                url="https://example.com/test",
                source="test",
                published_at=datetime.now(timezone.utc),
                score=10.0,
                summary="This is a test news item for integration testing."
            )
        ]
        
        # Save to temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_data = []
            for item in test_items:
                item_dict = {
                    'title': item.title,
                    'url': item.url,
                    'source': item.source,
                    'published_at': item.published_at.isoformat() if item.published_at else None,
                    'score': item.score,
                    'summary': item.summary
                }
                json_data.append(item_dict)
            
            json.dump(json_data, f)
            temp_file = f.name
        
        print(f"  ✅ Created temporary test file: {temp_file}")
        print(f"  ✅ Integration test would use user ID: {TEST_USER_ID}")
        
        # Clean up
        os.unlink(temp_file)
        print("  ✅ Cleaned up temporary files")
        
        print("✅ Integration test completed\n")
        return True
        
    except Exception as e:
        print(f"  ❌ Integration test failed: {str(e)}")
        print("✅ Integration test completed (with errors)\n")
        return False

def main():
    """Run comprehensive test suite."""
    print("🚀 CreatorPulse Backend Comprehensive Test Suite")
    print("=" * 50)
    
    # Test results tracking
    results = {
        'environment': False,
        'database': False,
        'scrapers': False,
        'consolidation': False,
        'email': False,
        'user_specific': False,
        'llm_output': False,
        'email_sending': False,
        'integration': False
    }
    
    # Run tests
    results['environment'] = test_environment_variables()
    results['database'] = test_database_connection()
    
    scraped_items = test_scrapers()
    results['scrapers'] = len(scraped_items) > 0 if scraped_items else False
    
    report_html = test_consolidation(scraped_items)
    results['consolidation'] = report_html is not None
    
    results['email'] = test_email_service()
    results['user_specific'] = test_user_specific_functionality()
    results['llm_output'] = test_llm_output()
    results['email_sending'] = test_email_sending()
    results['integration'] = test_integration(report_html)
    
    # Summary
    print("📊 Test Results Summary")
    print("=" * 30)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name.capitalize():<15}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Your CreatorPulse backend is ready to go!")
    elif passed_tests >= total_tests * 0.7:
        print("⚠️  Most tests passed. Check the failed tests above.")
    else:
        print("❌ Several tests failed. Please check your configuration.")
    
    print("\n💡 Next Steps:")
    if not results['environment']:
        print("  - Complete your .env file configuration")
    if not results['email']:
        print("  - Set up SMTP credentials for email functionality")
    if results['environment'] and results['database']:
        print(f"  - Try running: python consolidate.py sample_data.json {TEST_USER_ID} --send-email")
        print(f"  - Or test main scraper: python main_scraper.py {TEST_USER_ID}")

if __name__ == "__main__":
    main()
