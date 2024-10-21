npm install svgexport -g

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

echo '{"discord": DISCORD_TOKEN, "teamup": TEAMUP_TOKEN}' >> tokens.json
