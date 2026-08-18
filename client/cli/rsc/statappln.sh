LINKDIR="{linkdir}"
DATADIR="$LINKDIR-{now}"
KEEP_COUNT=6

cd {homedir} || exit 1
if [ -d $LINKDIR ]; then
  for item in {idlist}; do
    cp -n $LINKDIR/$item-*.json $DATADIR/ 2>/dev/null
  done
fi
ln -sTf $DATADIR $LINKDIR || exit 1
ls -t | grep $LINKDIR- | while read item; do
  [ $KEEP_COUNT -gt 0 ] && KEEP_COUNT=`expr $KEEP_COUNT - 1` || rm -rf $item
done

exit 0
