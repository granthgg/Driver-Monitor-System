import 'package:flutter/material.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';

class DriverMonitorPage extends StatefulWidget {
  @override
  _DriverMonitorPageState createState() => _DriverMonitorPageState();
}

class _DriverMonitorPageState extends State<DriverMonitorPage> {
  InAppWebViewController? webViewController;
  double progress = 0;

  @override
  void initState() {
    super.initState();

  
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.black,
        title: const Text(
          'Driver Monitor',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
        actions: [
          
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white),
            onPressed: () => webViewController?.reload(),
          ),
        ],
        leading: Builder(
          builder: (context) => IconButton(
            icon: Icon(Icons.arrow_back, color: Colors.white),
            onPressed: () => Navigator.pop(context),
          ),
        ),
        elevation: 20.0,
      ),
      body: Column(
        children: <Widget>[
          progress < 1.0
              ? LinearProgressIndicator(value: progress, backgroundColor: Colors.white, color: Colors.blue)
              : Container(),
          Expanded(
            child: InAppWebView(
              initialUrlRequest: URLRequest(url: WebUri('http://192.168.1.3:5000/')),
              onWebViewCreated: (controller) {
                webViewController = controller;
              },
              onProgressChanged: (controller, progress) {
                setState(() {
                  this.progress = progress / 100.0;
                });
              },
              onLoadStart: (controller, url) {
                setState(() {});
              },
              onLoadStop: (controller, url) async {
                setState(() {});
              },
              onLoadError: (controller, url, code, message) {
                setState(() {
                });
              },
              onReceivedServerTrustAuthRequest: (controller, challenge) async {
                return ServerTrustAuthResponse(action: ServerTrustAuthResponseAction.PROCEED);
              },
            ),
          ),
        ],
      ),
    );
  }
}
