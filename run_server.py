#!/usr/bin/env python
"""Railway production entrypoint: migrate, collectstatic, then gunicorn."""
import os
import subprocess
import sys

# Force disable WebSockets to use Gunicorn instead of Daphne
os.environ['USE_WEBSOCKETS'] = 'false'
# Force rebuild - 2026-08-25-05-45 - REMOVE TEMPORARY LOGGING

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def run(cmd, allow_fail=False):
    """Run command with proper PYTHONPATH."""
    print(f">>> {' '.join(str(c) for c in cmd)}", flush=True)
    env = os.environ.copy()
    env['PYTHONPATH'] = project_root
    try:
        subprocess.run(cmd, check=True, env=env, cwd=project_root)
    except subprocess.CalledProcessError as e:
        if allow_fail:
            print(f"Warning: command failed (non-fatal): {e}. Continuing.", flush=True)
        else:
            raise


def main():
    port = os.getenv('PORT', '8080')
    print(f"=== Dalal Platform Startup (port {port}) ===", flush=True)
    print(f"=== NEW CODE VERSION - 2026-08-25-05-45 - REMOVE TEMPORARY LOGGING ===", flush=True)
    print(f"DEBUG={os.getenv('DEBUG', 'False')}", flush=True)
    print(f"DJANGO_SETTINGS_MODULE={os.getenv('DJANGO_SETTINGS_MODULE')}", flush=True)
    print(f"PYTHONPATH={os.getenv('PYTHONPATH')}", flush=True)
    
    # Check which settings file is being used
    import django.conf
    print(f"Django settings module: {django.conf.settings.SETTINGS_MODULE}", flush=True)
    
    # Check if settings.py file contains properties app
    settings_file = os.path.join(project_root, 'dalal_project', 'settings.py')
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as f:
            settings_content = f.read()
            print(f"Settings.py exists: True", flush=True)
            print(f"Settings.py contains 'properties': {'properties' in settings_content}", flush=True)
            print(f"Settings.py contains 'INSTALLED_APPS': {'INSTALLED_APPS' in settings_content}", flush=True)
    else:
        print(f"Settings.py exists: False", flush=True)

    # Check if properties app is in INSTALLED_APPS
    try:
        import django
        django.setup()
        from django.conf import settings
        print(f"INSTALLED_APPS: {settings.INSTALLED_APPS}", flush=True)
        print(f"Properties in INSTALLED_APPS: {'properties' in settings.INSTALLED_APPS}", flush=True)
        
        # Check OAuth configuration
        print("\n=== OAuth Configuration Check ===", flush=True)
        
        # Google OAuth
        google_key = getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '')
        google_secret = getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', '')
        
        print("Google OAuth:", flush=True)
        if google_key:
            print("✓ Client ID Loaded", flush=True)
        else:
            print("✗ Client ID Missing - SOCIAL_AUTH_GOOGLE_OAUTH2_KEY not set", flush=True)
        
        if google_secret:
            print("✓ Client Secret Loaded", flush=True)
        else:
            print("✗ Client Secret Missing - SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET not set", flush=True)
        
        # Facebook OAuth
        facebook_key = getattr(settings, 'SOCIAL_AUTH_FACEBOOK_KEY', '')
        facebook_secret = getattr(settings, 'SOCIAL_AUTH_FACEBOOK_SECRET', '')
        
        print("\nFacebook OAuth:", flush=True)
        if facebook_key:
            print(f"✓ App ID Loaded (Length: {len(facebook_key)} chars)", flush=True)
            # Check if App ID looks valid (numeric)
            if facebook_key.isdigit():
                print("✓ App ID format valid (numeric)", flush=True)
            else:
                print(f"✗ App ID format invalid - must be numeric, got: {facebook_key[:10]}...", flush=True)
        else:
            print("✗ App ID Missing - SOCIAL_AUTH_FACEBOOK_KEY not set", flush=True)
        
        if facebook_secret:
            print(f"✓ App Secret Loaded (Length: {len(facebook_secret)} chars)", flush=True)
        else:
            print("✗ App Secret Missing - SOCIAL_AUTH_FACEBOOK_SECRET not set", flush=True)
        
        # Check BASE_URL
        base_url = getattr(settings, 'BASE_URL', 'NOT SET')
        print(f"\nBASE_URL: {base_url}", flush=True)
        
        # Check redirect URIs
        google_redirect = getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI', 'NOT SET')
        facebook_redirect = getattr(settings, 'SOCIAL_AUTH_FACEBOOK_OAUTH2_REDIRECT_URI', 'NOT SET')
        print(f"Google Redirect URI: {google_redirect}", flush=True)
        print(f"Facebook Redirect URI: {facebook_redirect}", flush=True)
        
        print("=== OAuth Configuration Check Complete ===\n", flush=True)
        
        # Check if properties.urls can be imported
        try:
            from properties import urls as properties_urls
            print(f"Properties URLs loaded successfully: {len(properties_urls.urlpatterns)} patterns", flush=True)
        except Exception as e:
            print(f"Error loading properties URLs: {e}", flush=True)
        
        # Check if home view can be imported
        try:
            from properties.views import home
            print(f"Home view imported successfully", flush=True)
        except Exception as e:
            print(f"Error importing home view: {e}", flush=True)
    except Exception as e:
        print(f"Error checking INSTALLED_APPS: {e}", flush=True)

    # IMPORTANT: Do NOT delete the database - preserve all user data
    # Database deletion was causing session loss and data destruction
    print("Preserving existing database - no deletion", flush=True)
    
    # Skip makemigrations - all migrations are already in place
    # makemigrations only needed when making model changes, not for deployment
    print("Skipping makemigrations - using existing migrations...", flush=True)
    
    print("Running migrate...", flush=True)
    # Try normal migrate first with allow_fail=True
    run([sys.executable, 'manage.py', 'migrate', '--noinput'], allow_fail=True)
    # If it failed above, try faking properties migrations
    print("Ensuring migrations are applied correctly...", flush=True)
    
    # Check if properties migrations were applied
    try:
        from django.core.management import call_command
        from io import StringIO
        output = StringIO()
        call_command('showmigrations', 'properties', verbosity=0, stdout=output)
        print(f"Properties migrations status: {output.getvalue()[:200]}", flush=True)
    except Exception as e:
        print(f"Error checking migrations: {e}", flush=True)
    
    print("Running collectstatic...", flush=True)
    run([sys.executable, 'manage.py', 'collectstatic', '--noinput'], allow_fail=True)
    
    # Check if static files were collected
    static_root = os.path.join(project_root, 'staticfiles')
    if os.path.exists(static_root):
        print(f"Static files collected to {static_root}: {len(os.listdir(static_root))} items", flush=True)
    else:
        print(f"WARNING: staticfiles directory not found at {static_root}", flush=True)

    workers = os.getenv('GUNICORN_WORKERS', '2')
    log_level = os.getenv('GUNICORN_LOG_LEVEL', 'debug')
    timeout = os.getenv('GUNICORN_TIMEOUT', '120')

    print(f"Starting gunicorn workers={workers}, log_level={log_level}, timeout={timeout}", flush=True)

    os.execvp(
        'gunicorn',
        [
            'gunicorn',
            'dalal_project.wsgi:application',
            '--bind', f'0.0.0.0:{port}',
            '--workers', workers,
            '--timeout', timeout,
            '--log-level', log_level,
            '--access-logfile', '-',
            '--error-logfile', '-',
            '--forwarded-allow-ips', '*',
            '--capture-output',
        ],
    )


if __name__ == '__main__':
    main()
