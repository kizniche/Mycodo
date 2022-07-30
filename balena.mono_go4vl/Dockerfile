# sys deps
FROM golang as upgrade-gobase
RUN apt update -y
RUN apt full-upgrade -y

RUN apt install -y fswebcam unzip

RUN curl -L https://github.com/storj/storj/releases/latest/download/uplink_linux_arm64.zip -o uplink_linux_arm64.zip
RUN unzip -o uplink_linux_arm64.zip
RUN install uplink /usr/local/bin/uplink

# golang deps
WORKDIR /app
COPY access.json /root/.config/storj/uplink/access.json

# copy in the example
COPY . .

#### #### ####
# golang stuffs
#### #### ####

# RUN go mod init gcb.io/v4l2-mgmt
# RUN go get github.com/vladimirvivien/go4vl/v4l2


RUN chmod +x /app/start.sh

# RUN NUM=0; fswebcam --device /dev/video$NUM $NUM.jpg
# RUN curl --upload-file $NUM.jpg https://transfer.sh/$NUM.jpg

# CMD ["bash"]
# CMD ["go", "run", "a.go"]
CMD ["/app/start.sh"]