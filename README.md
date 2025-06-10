# Glitch bulk-downloader

# How to bulk-download all your pojects

With the [project hosting shutdown](https://support.glitch.com/t/discussion-thread-project-hosting-ending-july-8/75660) in July, many of you have asked for a way to bulk-download your projects: this thread is for you.

We've created a python script that you can run that will download all your projects, and also download all your assets from the asset manager into a `glitch-assets` folder for each project.

---

## How long do I have?!

Project hosting will shut down in July, but you will continue to be able to download your projects for the entirety of 2025. So you have some time yet.

## Where to get it

[Right here!](https://raw.githubusercontent.com/Pomax/glitch-bulk-downloader/refs/heads/main/download.py) It's the `download.py` file.

## What do I need to run this?

### 1. You need Python 3.x

You will need Python 3 installed. If you're on linux or macos, this will almost certainly already be the case, and you should be able to use `python3` without installing anything. On Windows, you may need to go to the Windows Store, find Python, and install it first. This will add the `python` command (note that on Windows there is no "3" at the end). Alternatively, you can visit https://www.python.org/downloads/windows/ and download the installer for the current version of Python 3 that's appropriate to your Windows version.

### 2. You will also want `tar`

In order to unpack your projects and put them in properly named subfolders, you will need the `tar` command to be available. If you're on Linux or MacOS, you're (again) already good to go, but if you're on Windows you will need to "install" `tar`.

#### installing `tar` on Windows

If you use `git`, the easiest way to install `tar` is to just run the windows git installer, and tell it to install the GNU tools. After that finishes you should be able to confirm `tar` is available by opening a command prompt or powershell and just running `tar --help`.

If you don't, you can also exclusively install `tar` by heading over to https://gnuwin32.sourceforge.net/packages/gtar.htm and clicking on the binary setup link. This will take you to a Sourceforge (the place to be for open source before GitHub showed up) download page, which should automatically download the setup program.

Run the setup, and then you'll need to update your windows PATH to include the `C:\Program Files (x86)\GnuWin32\bin` folder: you can either do this persistently (instructions are easily found on the web for that), or you can run `set PATH=%PATH%;"C:\Program Files (x86)\GnuWin32\bin"` in your command prompt or powershell before you run the download script.

---

## How to use the script

The script will download your regular projects into an `./active` folder, and will download all your archived projects into an `./archived` folder. It can do this in two "modes":

### Interactive mode

### Interactive mode

You can invoke the script by calling:

```
python3 download.py
```

(or `python download.py` on Windows)

Run in this way, the script will ask you to provide your Glitch user id and token. Both of these can be found by going to glitch.com, opening your dev tools, and typing:

```
const { id, persistentToken: token} = JSON.parse(localStorage.cachedUser);
console.log(id, token);
```

This will log something along the lines of `123456 '3a6f55bd-8206-43d3-a149-176f13f32c45'`, where the first number is your id, and the second string is your token.

### Automatic mode

You can also run the script with those values directly, e.g.

```
python3 download.py 123456 '3a6f55bd-8206-43d3-a149-176f13f32c45'
```

In which case the script won't ask for anything and will just get to downloading.

### Optional runtime flags

The script supports three runtime flags, with flags needing to come after your user id and token:

1. `--no_assets`, which will make the script download your project, but not download the associated assets.
2. `--no-skip`, which will make the script re-download any projects you already downloaded if you run it more than once.
3. `--force-assets`, which will make the script ignore invalid SSL certificates when downloading assets. Use at your own risk.

## Replacing CDN URLs in your source code

Asset URLs are not automatically replaced in any source code, mostly because that's much harder than you'd think it'd be, so you will still need to replace CDN URLs in your code with relative links to the `./glitch-assets` folder that all your project's assets were downloaded into.

---

## Known issues

While this script will download your projects _and_ their associated assets, some assets may be on a very old CDN that currently has an expired certificate, so Python will refuse to download those assets out of security concerns (note that if your project's 8 years old, that might affect you. If not, it probably won't).

We're looking into updating that certificate, but the `--force-assets` flag can be used to bypass security for those assets for folks who think that's an acceptable risk.

## Questions or comments

If you have any questions about this script, or suggestions on how to improve it, feel free to either post an issue, or a reply over on the Glitch forum thread: https://support.glitch.com/t/glitch-project-bulk-downloading/75872

## Credits

Main script by me, [Pomax](https://pomax.github.io), with help from [Chris K.Y. FUNG](https://github.com/chriskyfung) for handling archived projects
