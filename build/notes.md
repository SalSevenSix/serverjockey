# Build Notes

## Release Process
* Complete remaining feature testing
* Do pre-build release testing
* Commit final changes, including updated release notes in;
  * debian/changelog
  * specs/sjgms.spec
* If needed, delete the `rpmbuilder` and `pacbuilder` docker images to get fresh bun
* Run or wait for CI build, confirm successful
* Build new ZomBox as per Release Process in virtualbox/notes.md
* Import new ZomBox and do post-build release testing
* Upload exported ZomBox to CI machine
* Login to CI machine and `sudo su`
  * Move ZomBox file to `/var/www/downloads`
  * run `/home/ubuntu/build/release.sh`
* Confirm and cleanup release
  * check artifacts [dl.serverjockey.net](https://dl.serverjockey.net/)
  * check images [hub.docker.com](https://hub.docker.com/r/salsevensix/serverjockey/tags)
  * Delete old artifacts and docker images as needed
* Git merge develop branch into master, push to GitHub, switch back to develop branch
* Create a release for master on GitHub
* Bump versioned files and push (see Versioned Files list below)
* Post new release on Ko-fi
* Post link to Ko-fi release post on discord

## Versioned Files
* deb/control
* deb/changelog
* rpm/sjgms.spec (2 places)
* pac/pkgbuild
* common/package.json
* discord/package.json
* discord/src/system/bootstrap.js
* extension/package.json
* extension/static/manifest.json
* statapp/package.json
* web/package.json
* core/util/sysutil.py

## Dev and CI environment setup

### Common

**Python**
* Match Pipfile `python_version` to default `python3` version
* Install latest pip and pipenv
* Install SteamCMD

**Tools**
* wget
* zip
* unzip
* jq

**Other**
* Install git and connnect to github
* Install bun

### CI Only
* Install and login docker
* Install and login gh
* Install and configure nginx
