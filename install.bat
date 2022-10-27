@REM install npm
npm -v
if %errorlevel% NEQ 0 goto npm_install
npm install svgexport -g
goto npm_installed
:npm_install
echo "npm not found"
start https://nodejs.org/en/
:npm_installed

pip3 install nextcord
pip3 install bs4
pip3 install colorama

mkdir tmp
mkdir data
mkdir log

cd data
mkdir guilds
mkdir pgp
mkdir users
cd ..

echo "add your tokens in 'tokens.json'"
echo '{"discord": DISCORD_TOKEN, "teamup": TEAMUP_TOKEN}' >> tokens.json