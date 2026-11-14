# Setup: Claude Code prompt

**Owner:** 01 · Lead and story (Mario)

## How to use this

Every team member does this once, on their own laptop, at the start of the event. Open a terminal in the repo folder, start Claude Code, and say: **"Read prompts/setup.md and carry it out. I am role 0N."** It works on Windows, macOS or Linux; the prompt works out where it is.

Claude Code checks Python, creates a virtual environment, installs the packages your role needs, wires your Earthdata token without ever seeing it, and runs the smoke test.

**What only you can do.** Claude stops and tells you when each one comes up.

1. **Make a free NASA Earthdata account** if you don't have one: [urs.earthdata.nasa.gov/users/new](https://urs.earthdata.nasa.gov/users/new). Then log in, open *Generate Token*, and copy a token.
2. **Paste the token into `.env`** yourself, in your editor. Claude never sees it.
3. **Log in to GitHub** if git asks.

---

## Your job

Set up this laptop so its owner can work on their role, then hand them to `prompts/build.md`. Do every step you can yourself. Hand the user only what needs a password, a token, a login or administrator rights. Give each as one command or click, with what they will see. After each handoff, wait until they say they are done, then check it worked.

## Ground rules

1. **Never see a secret.** Don't ask for a password or token in the chat, don't print `.env` or `~/.netrc`, and never put credentials in the repo or in any log. To check the token, test that `.env` has a non-empty `EARTHDATA_TOKEN=` line without printing it.
2. **Ask before** `sudo`, an administrator install, a system-wide package manager, or pushing anything.
3. **Stay in the repo folder and your user account.** The virtual environment lives in `.venv/`, which is git-ignored.
4. Keep short notes as you go (versions, anything the user did) and put them in your role's row of `STATUS.md` at the end.

## S1. Where am I?

- Find the operating system, the shell, and whether `python3` (or `py` on Windows) is 3.11 or later.
- If Python is missing or older than 3.11, stop. Tell the user to install it from python.org, or with their package manager, then continue.
- Check `git --version` and that the current folder is this repo (`git remote get-url origin` names `space-apps-dancing-with-the-SARs-PEA`).

## S2. Environment

- `python -m venv .venv`, activate it, `pip install --upgrade pip`.
- Install the requirements by role:
  - **Everyone:** `pytest`.
  - **02, 03, 04, 05:** `pip install -r requirements.txt`.
  - **06:** the same, plus whatever the page needs. Python is only for `export.py` and `mock_products.py`.
  - **01:** `pytest` is enough to start.
- If `rasterio` or `h5py` fail to install, note it and carry on. The skeleton tools need only the standard library.

## S3. Earthdata token (02, 03, 04 and 05)

- If `.env` doesn't exist, copy `.env.example` to `.env`. Then ask the user to paste their token after `EARTHDATA_TOKEN=` in their editor, and save.
- Check that the line is non-empty without printing it. For example, in Python: `bool(open('.env').read().split('EARTHDATA_TOKEN=')[1].strip())`.
- Check that `git check-ignore .env` says it is ignored.

## S4. Smoke test

- `pytest -q` must pass.
- `python mock_products.py --out <a temp folder>` then `python checkpoint.py mock --products <that folder>` must say "contract OK".
- Run your role's script with `--help`, and once on the `demo` site. A stub stops with exit code 3 and a line naming its owner, which is expected.

## S5. Branch and hand-off

- Create the role branch: `git switch -c r0N/start`.
- Add your role's line in `STATUS.md` under "Early tests" for T0: PASS or what failed, with the Python version.
- Tell the user: "Setup done. Next: say **Read prompts/build.md. I am role 0N.**"
