INSFOLDER=~/.essay_memo
echo "If you are mac user, please use mac port"
echo "http://www.macports.org/"
echo "And download both python and pip"
echo "And don't forget set PATH for ~/bin/sh all wrapped bash script is there"
rm -Rf $INSFOLDER
rm -vf ~/bin/sh/essay_memo
mkdir -p ~/bin/sh
mkdir -p $INSFOLDER
cp -vf *.py $INSFOLDER
cp -vf essay_memo ~/bin/sh
cp -vf *.db $INSFOLDER

sudo apt install python3-pip
pip install lxml
#I should seperate this to python deploy
#sudo pip install re #for wikipedia
pip install BeautifulSoup4 #for wikipedia
pip install requests
sudo apt install python3-lxml
chmod -R 755 $INSFOLDER
chmod -R 755 ~/bin/sh

