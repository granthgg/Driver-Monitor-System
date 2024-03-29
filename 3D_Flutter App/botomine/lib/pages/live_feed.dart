import 'package:flutter/material.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';

class LiveFeedPage extends StatefulWidget {
  @override
  _LiveFeedPageState createState() => _LiveFeedPageState();
}

class _LiveFeedPageState extends State<LiveFeedPage> {
  InAppWebViewController? webViewController;
  bool isPlaying = false;
  String errorText = 'No Video Feed Available Now.';
  bool isError = false;

  void startVideoFeed() {
    if (isError) {
      setState(() {
        isError = false;
        errorText = '';
      });
      webViewController?.loadUrl(
        urlRequest: URLRequest(url: WebUri('http://192.168.1.3:5000/video_feed'))
      );
    }
    setState(() {
      isPlaying = true;
    });
  }

  void stopVideoFeed() {
    if (isPlaying) {
      webViewController?.stopLoading();
      setState(() {
        isPlaying = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final videoFeedWidth = MediaQuery.of(context).size.width * 0.8;
    final videoFeedHeight = videoFeedWidth * 9 / 16;

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Color.fromARGB(255, 0, 0, 0),
        title: Text(
          'Live Feed',
          style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
        leading: Builder(
          builder: (context) => IconButton(
            icon: Icon(Icons.arrow_back, color: Colors.white),
            onPressed: () => Navigator.pop(context),
          ),
        ),
        elevation: 20.0,
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: videoFeedWidth,
              height: videoFeedHeight,
              margin: EdgeInsets.symmetric(vertical: 20),
              decoration: BoxDecoration(
                color: Colors.black,
                borderRadius: BorderRadius.circular(10),
                boxShadow: [
                  BoxShadow(
                    color: Colors.grey.withOpacity(0.5),
                    spreadRadius: 6,
                    blurRadius: 8,
                    offset: Offset(0, 3),
                  ),
                ],
              ),
              child: isError
                ? Center(
                    child: Text(
                      errorText,
                      style: TextStyle(color: Colors.white),
                    ),
                  )
                : InAppWebView(
                    initialUrlRequest: URLRequest(url: WebUri('http://192.168.1.3:5000/video_feed')),
                    onWebViewCreated: (controller) {
                      webViewController = controller;
                    },
                    onLoadError: (controller, url, code, message) {
                      setState(() {
                        isError = true;
                        errorText = 'Error loading video feed.';
                      });
                    },
                    onLoadHttpError: (controller, url, statusCode, description) {
                      setState(() {
                        isError = true;
                        errorText = 'HTTP error loading video feed.';
                      });
                    },
                  ),
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton(
                  onPressed: isPlaying ? null : startVideoFeed,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: isPlaying ? Colors.grey : Colors.black,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(5.0),
                    ),
                  ),
                  child: Text('Start Live Feed'),
                ),
                ElevatedButton(
                  onPressed: isPlaying ? stopVideoFeed : null,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: isPlaying ? Colors.black : Colors.grey,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(5.0),
                    ),
                  ),
                  child: Text('Stop Live Feed'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
