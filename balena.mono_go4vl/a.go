package main

func main() {
	//test_fsnotify()
	//capture_video()
}

//func capture_video() {
//	println("ohai")
//	// open device
//	device, err := v4l2.Open("/dev/video0")
//	if err != nil {
//		log.Fatalf("failed to open device: %s", err)
//	}
//	defer device.Close()
//
//	// configure device with preferred fmt
//	if err := device.SetPixFormat(v4l2.PixFormat{
//		Width:       480,
//		Height:      270,
//		PixelFormat: v4l2.PixelFmtMJPEG,
//		Field:       v4l2.FieldNone,
//	}); err != nil {
//		log.Fatalf("failed to set format: %s", err)
//	}
//
//	// start a device stream with 3 video buffers
//	if err := device.StartStream(3); err != nil {
//		log.Fatalf("failed to start stream: %s", err)
//	}
//
//	ctx, cancel := context.WithCancel(context.TODO())
//	// capture video data at 15 fps
//	frameChan, err := device.Capture(ctx, 15)
//	if err != nil {
//		log.Fatal(err)
//	}
//
//	// grab 10 frames from frame channel and save them as files
//	totalFrames := 2
//	count := 0
//	for frame := range frameChan {
//		fileName := fmt.Sprintf("capture_%d.jpg", count)
//		file, err := os.Create(fileName)
//		if err != nil {
//			log.Printf("failed to create file %s: %s", fileName, err)
//			continue
//		}
//		if _, err := file.Write(frame); err != nil {
//			log.Printf("failed to write file %s: %s", fileName, err)
//			continue
//		}
//		if err := file.Close(); err != nil {
//			log.Printf("failed to close file %s: %s", fileName, err)
//		}
//		count++
//		if count >= totalFrames {
//			break
//		}
//	}
//
//	for {
//		time.Sleep(time.Duration(1<<63 - 1))
//	}
//
//	cancel() // stop capture
//	if err := device.StopStream(); err != nil {
//		log.Fatal(err)
//	}
//	fmt.Println("Done.")
//}
