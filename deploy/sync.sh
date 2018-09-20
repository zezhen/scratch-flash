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

# sync webapp files/directories
sync $root/webapp scratchonline

# sync bin-* files 
if [ $mode == 'dev' ]; then
    sync $root/bin-debug scratchonline/scratch
else
    sync $root/bin-release scratchonline/scratch
fi

