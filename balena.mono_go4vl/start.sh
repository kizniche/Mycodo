while true
do
  for NUM in 0 2 4 6 8
  do
    vid_id=video$NUM

    data_store_dir=/data/img/$vid_id/`date +%Y-%m-%d`
    mkdir -p $data_store_dir
    dir=$data_store_dir
    mkdir -p $dir
    file=$(date +%s).jpg
    full_path=$dir/$file

    video_device=/dev/video$NUM
    if [ -e "$video_device" ]; then
        echo "Word. $video_device is present.  Moving on."

        fswebcam --device $video_device $full_path
        sleep 1
        #    curl --upload-full_path $full_path https://transfer.sh/$full_path && echo
        #    uplink access save main accessgrant.txt
        echo "uplink cp $full_path sj://stills/$vid_id/$file"
        yes n | uplink cp $full_path sj://stills/$vid_id/$file

        sample=wut
        /usr/bin/mosquitto_pub -t go-mqtt/sample -m "$sample" -h 192.168.0.21
    else
      echo "$video_device MISSING!"
    fi
  done

  SLEEP_AMOUNT=300
  echo "sleep $SLEEP_AMOUNT"
  sleep $SLEEP_AMOUNT

done
# curl --upload-full_path $full_path https://transfer.sh/$full_path

sleep infinity