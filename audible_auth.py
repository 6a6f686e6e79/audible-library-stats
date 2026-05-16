"""
audible_auth.py
Run this ONCE to authenticate with Audible.
Saves an auth file locally for use by audible_stats.py
"""

import audible
import getpass

AUTH_FILE = 'audible_auth.json'

print("=" * 50)
print("AUDIBLE AUTHENTICATION")
print("=" * 50)
print("This will log you into Audible and save an auth token.")
print("You only need to do this once.\n")

auth = audible.Authenticator.from_login(
    username=input("Audible/Amazon email: "),
    password=getpass.getpass("Password: "),
    locale="us",
    with_username=False
)

auth.to_file(AUTH_FILE)
print(f"\nAuth saved to: {AUTH_FILE}")
print("You can now run audible_stats.py")
