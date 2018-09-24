#! /bin/sh

mode='dev'

if [ $# -ge 1 ]; then
	mode=$1
fi

root=`dirname $0`
cd "$root/.."
root=`pwd`

echo "mode: $mode"

function sync {
    src=$1
    dest=$2
    if [ $mode == 'dev' ]; then
	    #host='rewardafford.corp.gq1.yahoo.com:~'
	    rsync -uravzh $src/* "/tmp/$dest/"
    else
	    host='root@47.98.176.45:~'
	    rsync -uravzh -e "ssh -i $root/deploy/aliyun.pem" $src/* "$host/$dest/"
    fi
}


if [ $mode != 'dev' ]; then
    deployDir=`mktemp -d '/tmp/scratch-XXXX'`
fi

# build Scratch.swf
./gradlew build -Ptarget=11.6
cp build/11.6/Scratch.swf webapp/scratch/Scratch.swf

# sync webapp files/directories
sync $root/webapp scratchonline

