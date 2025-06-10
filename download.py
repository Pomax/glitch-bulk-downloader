# Glitch project bulk-downloader
#
# Authors:
#  Pomax, https://github.com/Pomax
#  Chris K.Y. FUNG, https://github.com/chriskyfung
#
# License:
#  this script is in the public domain

import sys, os, shutil, json, subprocess
from http.client import InvalidURL
from urllib.request import Request, urlopen, urlretrieve, URLError
from urllib.parse import quote, unquote
import ssl
from time import time, sleep

print("\nWelcome to the Glitch.com bulk project downloader.")

# Verify that we have tar available, otherwise thing
bypass_tar = False
try:
    subprocess.run(["tar", "--help"], capture_output=True, text=True)
except:
    print("")
    print("WARNING: could not find 'tar'!")
    print("")
    print("This script works best when the 'tar' command is available,")
    print("would you like to continue in download-only mode?")
    print("")
    print("Note: you will need to unpack each download manually, and rename")
    print("the resulting 'app' dir manually. You cannot run a bulk-unpack,")
    print("every archive will unpack to the same directory name!!")
    print("")
    try:
        no_tar = input("Proceed in download-only mode? (Y/n) ").lower()
        if no_tar != "y":
            exit(1)
        bypass_tar = True
    except KeyboardInterrupt:
        exit()

args = sys.argv
no_assets = "--no-assets" in args
no_skip = "--no-skip" in args
force_assets = "--force-assets" in args

def get_values():
    """
    Ask for user credentials, unless they were already provided on the command line
    """
    if len(args) > 1:
        user_id = args[1]
    else:
        print("\nPlease enter your user id. You can find this in the browser with glitch.com open, by opening your dev tools and running:\n")
        print("  JSON.parse(localStorage.cachedUser).id\n")
        user_id = input("Your user id: ")

    if len(args) > 2:
        user_token = args[2]
    else:
        print("\nPlease enter your persisten token. You can find this in the browser with glitch.com open, by opening your dev tools and running:\n")
        print("  JSON.parse(localStorage.cachedUser).persistentToken\n")
        user_token = input("Your persistent token: ")
    user_token = user_token.replace("'",'').replace('"','')

    return (user_id, user_token,)

def get_project_list(user_id, user_token, get_archived=False):
    """
    Ask for user credentials, unless they were already provided on the command line
    If get_archived is True, fetches deleted/archived projects instead of active projects.
    """

    if get_archived:
        print("Fetching archived project list...")
    else:
        print("Fetching active project list...")

    base = "https://api.glitch.com/v1/users/by/id"
    endpoint = "deletedProjects" if get_archived else "projects"
    url = f"{base}/{endpoint}?id={user_id}&limit=1000"
    req = Request(url)
    req.add_header('Authorization', user_token)

    try:
        text = urlopen(req).read().decode("utf-8")
        try:
            return json.loads(text)
        except:
            print("could not parse JSON")
    except URLError as e:
        print(f"could not open {url}")
        print(e)
    return {}

def wait_for_dir(dir_path, timeout=10, poll_interval=1):
    """
    Waits until a directory exists or a timeout is reached.
    """
    start_time = time()
    while time() - start_time < timeout:
        if os.path.isdir(dir_path):
            return True
        sleep(poll_interval)
    return False

def download_project(user_token, project, project_type="active"):
    """
    Download a project archive from Glitch, unpack it, and rename the dir from "app" to the project domain.
    """
    project_id = project.get("id")
    project_title = project.get("domain", project_id)
    base_path = f"./{project_type}/{project_title}"
    if os.path.exists(base_path):
        if not no_skip:
            print(f"Skipping {project_title} (already downloaded)")
            return
        else:
            shutil.rmtree(base_path, ignore_errors=False, onerror=None)
    if not os.path.exists(project_type):
        os.mkdir(f"./{project_type}")
    url = f"https://api.glitch.com/project/download/?authorization={user_token}&projectId={project_id}"
    file = f"./{project_title}.tgz"
    print(f"\nDownloading '{project_title}'...")
    result = urlretrieve(url, file)
    if bypass_tar is False:
        print("Unpacking...")
        unpacked_dir = './app'
        if os.path.exists(unpacked_dir):
            shutil.rmtree(unpacked_dir, ignore_errors=False, onerror=None)
        command = f"tar -xvzf {file}"
        unpack = subprocess.run(command.split(), capture_output=True, text=True)
        wait_for_dir(unpacked_dir)
        if not os.path.isdir(unpacked_dir):
            print(f"ERROR: {project_title} did not extract to {unpacked_dir}!")
        else:
            dest = f"./{project_type}/{project_title}"
            shutil.move(unpacked_dir, dest)
            os.remove(file)
            if no_assets is False:
                download_assets(project_title, project_type)

def download_assets(project_title, project_type):
    """
    Download all assets associated with this project
    """
    # It is a major failing of Python that we can't tell
    # it to halt execution until shutils is done...
    base_path = f"./{project_type}/{project_title}"
    while not os.path.exists(base_path):
        sleep(0.1)  # Check every 100ms
    dir = f"{base_path}/glitch-assets"
    os.makedirs(dir, exist_ok=True)
    print(f"Downloading all assets into {dir}...")
    assets = {}
    try:
        with open(f"{base_path}/.glitch-assets") as asset_file:
            for line in asset_file:
                if line.isspace():
                    continue
                """
                Aggregate our asset records, keyed on uuid, invalidating
                any record that has a "deleted" record.
                """
                record = json.loads(line)
                uuid = record["uuid"]
                deleted = record.get("deleted", False)
                have_record = assets.get(uuid, None)
                if have_record is not None and deleted is not False:
                    assets[uuid] = False
                else:
                    assets[uuid] = record
    except Exception as e:
        print(f"glitch-assets error for {project_title}: {e}")
    
    if force_assets:
        # Allow invalid SSL certificates
        default_context = ssl._create_default_https_context
        ssl._create_default_https_context = ssl._create_unverified_context
    
    for entry in  [x for x in assets.values() if x is not False]:
        # Do a bit of URL hackery because there's a surprising number
        # of bad URLs in people's glitch assets files...
        name = entry["name"]
        url = entry["url"].replace("%3A", ":").replace("%2F", "/").replace(" ", "%20")
        dest = f"{dir}/{name}"
        print(f"Downloading {name} from {url}...")
        try:
            urlretrieve(url, dest)
        except URLError as e:
            print(f"error getting url: {e}")
        except ValueError as e:
            print(f"bad url: {e}")
        except InvalidURL as e:
            print(f"invalid url: {e}")
    
    if force_assets:
        # Restore original HTTPS context
        ssl._create_default_https_context = default_context


"""
Let's get this bulk download going:
"""

try:
    (user_id, user_token) = get_values()

    print("Fetching list of active projects...")
    data = get_project_list(user_id, user_token, False)
    items = data.get('items', [])
    print(f"Downloading {len(items)} projects...")
    for project in items:
        download_project(user_token, project, "active")

    print("Fetching list of archived projects...")
    data = get_project_list(user_id, user_token, True)
    items = data.get('items', [])
    print(f"Downloading {len(items)} archived projects...")
    for project in items:
        download_project(user_token, project, "archived")


except KeyboardInterrupt:
    exit(1)

print("")
print("*** Finished downloading all your projects ***")
print("")
print("NOTE: asset URLs were not automatically replaced in any source")
print("      code, so you will still need to replace CDN URLs in your")
print("      code with relative links to the ./glitch-assets directory.")
print("")
