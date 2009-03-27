#! /bin/bash
#

./bin/increase_release
make deb_sign && sudo dpkg --purge intex && sudo dpkg --install $(ls -1 dist/*.deb |tail -1)
