#!/bin/sh

[ -d /tmp/xtest ] || mkdir -p /tmp/xtest
cd /tmp/xtest

echo "Downloading CCcam lines..."

####################################################################################################

curl  --limit-rate 100K  -k -Lbk -A -k -m 8000 -m 5200 -s  https://cccamsate.com/free > /tmp/xtest/CCcam

grep -o -i -E 'C: [a-z][^<]*' CCcam  > /tmp/xtest/soubor7

more /tmp/xtest/soubor7
####################################################################################################
curl --max-time 5.5  --limit-rate 100K     -s -k -Lbk -A -k -m 8 -m 52  https://cccamia.com/free-cccam/ > /tmp/xtest/CCcam 

grep -o -i -E 'C: [a-z][^<]*' CCcam  > /tmp/xtest/soubor8

more /tmp/xtest/soubor8
####################################################################################################
curl --max-time 5.5  --limit-rate 100K     -s -k -Lbk -A -k -m 8 -m 52  https://cccamhub.com/cccamfree/ > /tmp/xtest/CCcam

grep -o -i 'C: free[^<]*' CCcam  > /tmp/xtest/soubor9

more /tmp/xtest/soubor9
####################################################################################################
curl --max-time 5.5  --limit-rate 100K     -s -k -Lbk -A -k -m 8 -m 52  https://cccamiptv.club/free-cccam/#page-content > /tmp/xtest/CCcam

grep -o -i 'C: free[^<]*' CCcam > /tmp/xtest/soubor10

more /tmp/xtest/soubor10

#####################################################################################################
curl --max-time 5.5  --limit-rate 100K     -k -A -k -s  server.satunivers.tv/download.php?file=cccm.cfg > /tmp/xtest/soubor12
more /tmp/xtest/soubor12
####################################################################################################
curl --max-time 5.5  --limit-rate 100K     -s -k -Lbk -A -k -m 8 -m 52  https://cccamgalaxy.com/  > /tmp/xtest/CCcam
grep -o -i -E 'C: [a-z][^<]*' CCcam | sed -n '1p; q'  > /tmp/xtest/soubor13
more /tmp/xtest/soubor13
#####################################################################################################

curl  --limit-rate 100K  -k -Lbk -A -k -m 8000 -m 5200 -s  https://cccam-premium.pro/free-cccam/ > /tmp/xtest/CCcam

grep -o -i -E 'C: [a-z][^<]*' CCcam  > /tmp/xtest/soubor18

more /tmp/xtest/soubor18
####################################################################################################
curl  --limit-rate 100K  -k -Lbk -A -k -m 8000 -m 5200 -s  https://cccamfree48h.yolasite.com/server-2.php > /tmp/xtest/CCcam
grep -o -i 'C: free[^<]*' CCcam  > /etc/CCcam.cfg
grep -o -i 'C: free[^<]*' CCcam  > /tmp/xtest/soubor19

more /tmp/xtest/soubor19
####################################################################################################
curl  --limit-rate 100K  -k -Lbk -A -k -m 8000 -m 5200 -s  https://cccam.net/freecccam > /tmp/xtest/CCcam

grep -o -i -E 'C: [a-z][^<]*' CCcam  > /tmp/xtest/soubor20

more /tmp/xtest/soubor20
####################################################################################################

CURRENT_DATE=$(date +%Y-%m-%d)
TESTIOUS_URL="https://testious.com/old-free-cccam-servers/${CURRENT_DATE}/"
echo "Pobieranie z testious.com dla daty: ${CURRENT_DATE}"
curl --max-time 10 --limit-rate 100K -Lk -s -A "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36" "$TESTIOUS_URL" > /tmp/xtest/testious_page.html

if [ -s /tmp/xtest/testious_page.html ]; then

    cat /tmp/xtest/testious_page.html | grep -o '<div style="background-color: #EEEEEE[^>]*>.*</div>' | \
      sed 's/<div[^>]*>//g' | \
      sed 's#</div>##g' | \
      sed 's#<br>#\n#g' | \
      sed 's/^[[:space:]]*//' | \
      grep '^C:' > /tmp/xtest/testious_cccam.tmp

    cat /tmp/xtest/testious_page.html | grep -o '<div style="background-color: #EEEEEE[^>]*>.*</div>' | \
      sed 's/<div[^>]*>//g' | \
      sed 's#</div>##g' | \
      sed 's#<br>#\n#g' | \
      sed 's/^[[:space:]]*//' | \
      grep '^N:' > /tmp/xtest/testious_newcamd.tmp

    if [ ! -s /tmp/xtest/testious_cccam.tmp ]; then
        echo "Próba alternatywnej metody ekstrakcji C: z testious.com..."
        cat /tmp/xtest/testious_page.html | tr '>' '\n' | tr '<' '\n' | grep '^C:' | sed 's/^[[:space:]]*//' > /tmp/xtest/testious_cccam.tmp
    fi

    if [ ! -s /tmp/xtest/testious_newcamd.tmp ]; then
        echo "Próba alternatywnej metody ekstrakcji N: z testious.com..."
        cat /tmp/xtest/testious_page.html | tr '>' '\n' | tr '<' '\n' | grep '^N:' | sed 's/^[[:space:]]*//' > /tmp/xtest/testious_newcamd.tmp
    fi

    if [ -s /tmp/xtest/testious_cccam.tmp ]; then
        cat /tmp/xtest/testious_cccam.tmp >> /etc/CCcam.cfg
        cp /tmp/xtest/testious_cccam.tmp /tmp/xtest/soubor4
        echo "Znalezione serwery C: z testious.com:"
        more /tmp/xtest/soubor4
    else
        echo "No C: servers found on testious.com for date ${CURRENT_DATE}"
        touch /tmp/xtest/soubor4
    fi

    if [ -s /tmp/xtest/testious_newcamd.tmp ]; then
        cat /tmp/xtest/testious_newcamd.tmp >> /etc/CCcam.cfg
        cp /tmp/xtest/testious_newcamd.tmp /tmp/xtest/soubor5
        echo "Znalezione serwery N: z testious.com:"
        more /tmp/xtest/soubor5
    else
        echo "No N: servers found on testious.com for date ${CURRENT_DATE}"
        touch /tmp/xtest/soubor5
    fi

else
    echo "Error downloading page from testious.com"
    touch /tmp/xtest/soubor4
    touch /tmp/xtest/soubor5
fi

cat soubor{1..28} > /tmp/CCcam.cfg 2>/dev/null || true
sed -i "s/c:/C:/" /tmp/CCcam.cfg
while read radek; do
    pocet=$(echo $radek | wc -w)
    if [ $pocet -gt 4 ]; then
        echo $radek >> /tmp/CCcam.cfg2
    fi
done < '/tmp/CCcam.cfg'
cd /
rm -rf /etc/CCcam.cfg
cp /tmp/CCcam.cfg2 /etc/CCcam.cfg
rm -rf /tmp/CCcam.cfg2
rm -rf /tmp/CCcam.cfg
rm -rf /tmp/xtest
rm -rf /CCcam*
rm -rf /hotovo*
more /etc/CCcam.cfg
cat /etc/CCcam.cfg > /tmp/CCcam.cfg

echo "Converting CCcam and Newcamd lines to OSCam format..."

OUTPUT2='/tmp/server'
OUTPUT_N='/tmp/server_n'
FS=" "
group_number=1

cat /etc/CCcam.cfg | grep -i "^C:.*" | while read line ; do
    SERVER=$(echo $line | cut -d"$FS" -f2)
    PORT=$(echo $line | cut -d"$FS" -f3)
    USER=$(echo $line | cut -d"$FS" -f4)
    PASS=$(echo $line | cut -d"$FS" -f5)

    echo "[reader]" >> $OUTPUT2
    echo "label = $SERVER" >> $OUTPUT2
    echo "protocol = cccam" >> $OUTPUT2
    echo "device = $SERVER,$PORT" >> $OUTPUT2
    echo "user = $USER" >> $OUTPUT2
    echo "password = $PASS" >> $OUTPUT2
    echo "group = $group_number" >> $OUTPUT2
    echo "ccckeepalive = 1" >> $OUTPUT2
    echo "inactivitytimeout = 30" >> $OUTPUT2
    echo "reconnecttimeout = 5" >> $OUTPUT2
    echo "disablecrccws = 1" >> $OUTPUT2
    echo "disablecrccws_only_for = 0E00:000000,0500:030B00,050F00;098C:000000;09C4:000000" >> $OUTPUT2
    echo "group = 1" >> $OUTPUT2
    echo "audisabled = 0" >> $OUTPUT2
    echo "" >> $OUTPUT2
    echo "" >> $OUTPUT2
done

cat /etc/CCcam.cfg | grep -i "^N:.*" | while read line ; do
    set -- $line
    if [ "$1" = "N:" ]; then
        SERVER=$2
        PORT=$3
        USER=$4
        PASS=$5
        shift 5
        KEY=$(printf "%s" "$1")
        shift
        while [ $# -gt 0 ]; do
            KEY="${KEY}$1"
            shift
        done

        echo "[reader]" >> $OUTPUT_N
        echo "label = $SERVER" >> $OUTPUT_N
        echo "enable = 1" >> $OUTPUT_N
        echo "protocol = newcamd" >> $OUTPUT_N
        echo "key = $KEY" >> $OUTPUT_N
        echo "device = $SERVER,$PORT" >> $OUTPUT_N
        echo "user = $USER" >> $OUTPUT_N
        echo "password = $PASS" >> $OUTPUT_N
        echo "group = 1" >> $OUTPUT_N
        echo "inactivitytimeout = 1" >> $OUTPUT_N
        echo "reconnecttimeout = 30" >> $OUTPUT_N
        echo "lb_weight = 100" >> $OUTPUT_N
        echo "cccversion = 2.1.2" >> $OUTPUT_N
        echo "cccmaxhops = 10" >> $OUTPUT_N
        echo "cccwantemu = 1" >> $OUTPUT_N
        echo "ccckeepalive = 1" >> $OUTPUT_N
        echo "" >> $OUTPUT_N
    fi
done

cat /tmp/server_n >> /tmp/server

if [ -f /etc/OscamDATAx.cfg ]; then
    cat /etc/OscamDATAx.cfg >> /tmp/server
fi

for path in \
    /etc/tuxbox/config/oscam/oscam.server \
    /etc/tuxbox/config/oscam-emu/oscam.server \
    /etc/tuxbox/config/oscam_atv_free/oscam.server \
    /etc/tuxbox/config/oscam.server \
    /etc/tuxbox/config/oscam-stable/oscam.server \
    /var/tuxbox/config/oscam.server \
    /etc/tuxbox/config/gcam.server \
    /etc/tuxbox/config/ncam.server \
    /etc/tuxbox/config/ncam/ncam.server \
    /etc/tuxbox/config/supcam-emu/oscam.server \
    /etc/tuxbox/config/oscamicam/oscam.server \
    /etc/tuxbox/config/oscamicamnew/oscam.server
do
    cp /tmp/server "$path" 2>/dev/null || true
done

rm -rf /tmp/server /tmp/server_n

cat /etc/CCcam.cfg > /etc/oscam.cfg

echo ""
[ -x /etc/init.d/softcam ] && /etc/init.d/softcam restart || echo "Softcam init script not found or not executable"
echo ""
pocet1=$(wc -l < /etc/CCcam.cfg)
echo "SERVERS..... $pocet1"

rm -rf /tmp/cccam /tmp/cccam1 /tmp/xtest /tmp/CCcam.cfg

sleep 5

exit 0
