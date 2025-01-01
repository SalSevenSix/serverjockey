# Build Notes

## Release Process
* Complete remaining feature testing
* Do pre-build release testing
* Commit final changes, including updated release notes in;
  * debian/changelog
  * specs/sjgms.spec
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
* Post link to Ko-fi relase post on discord

## Versioned Files
* debian/control
* debian/changelog
* specs/sjgms.spec
* discord/package.json
* discord/src/main.js
* extension/package.json
* extension/static/manifest.json
* web/package.json
* core/util/sysutil.py
