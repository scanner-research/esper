#!/bin/bash

RUN_TESTS=${RUN_TESTS:=0}
NPM_COMMAND="npm install --unsafe-perm"
PIP_COMMAND="pip3 install --force-reinstall --user -e ."

# Fail fast
set -e

DEPS_DIR=/app/deps

pushd .

# Rekall
cd $DEPS_DIR
echo "Installing Rekall"
cd rekall/rekallpy
$PIP_COMMAND
if [ $RUN_TESTS == 1 ]; then
        python3 setup.py test
fi
cd $DEPS_DIR
cd rekall/rekalljs
$NPM_COMMAND
npm run build
npm link

# Model server
cd $DEPS_DIR
echo "Installing Model-Server"
cd esper-model-server
./extract_data.sh
pip3 install --user -r requirements.txt
if [ $RUN_TESTS == 1 ]; then
        pytest -v tests
fi

# Caption-Index
cd $DEPS_DIR
echo "Installing Caption-Index"
cd caption-index
rustup update
rustup override set nightly
$PIP_COMMAND
./get_models.sh
if [ $RUN_TESTS == 1 ]; then
        python3 setup.py test
fi

# Rs-Embed
cd $DEPS_DIR
echo "Installing Rs-Embed"
cd rs-embed
rustup update
rustup override set nightly
$PIP_COMMAND
if [ $RUN_TESTS == 1 ]; then
        python3 setup.py test
fi

cd $DEPS_DIR
echo "Installing vgrid"
cd vgrid/vgridjs
$NPM_COMMAND
npm link @wcrichto/rekall
npm run build
npm link
cd ../vgridpy
$PIP_COMMAND

cd $DEPS_DIR
echo "Installing vgrid_jupyter"
cd vgrid_jupyter
$NPM_COMMAND
npm link @wcrichto/vgrid
npm run build
$PIP_COMMAND

jupyter nbextension enable --py --user widgetsnbextension
jupyter contrib nbextension install --user --skip-running-check
jupyter nbextensions_configurator enable --user
jupyter nbextension enable --user hide_input/main
jupyter nbextension enable --user toc2/main
jupyter nbextension enable --user code_prettify/autopep8
jupyter nbextension enable --user execute_time/ExecuteTime
jupyter nbextension enable --py --user qgrid

jupyter nbextension install vgrid_jupyter --py --symlink --user --overwrite
jupyter nbextension enable vgrid_jupyter --py --user

cd /app/ui
$NPM_COMMAND
npm link @wcrichto/vgrid
npm run prepublishOnly

popd

echo "SUCCESS! All dependencies installed"
