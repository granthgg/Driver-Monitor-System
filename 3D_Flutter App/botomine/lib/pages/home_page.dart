import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:botomine/components/my_drawer.dart';
import 'package:socket_io_client/socket_io_client.dart' as IO;
import 'package:url_launcher/url_launcher.dart';

class HomePage extends StatefulWidget {
  @override
  _HomePageState createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final user = FirebaseAuth.instance.currentUser!;
  Map<String, dynamic> metrics = {
    "left_eye": "Open",
    "right_eye": "Open",
    "mouth": "Open",
    "direction": "Front",
    "using_phone": "No",
    "talking": "No",
    "yawning": "No",
    "state": "Awake",
  };
  double latitude = 30.7654865; 
  double longitude = 76.6105031; 
  IO.Socket? socket;

  @override
  void initState() {
    super.initState();
    connectToSocket();
  }

  @override
  void dispose() {
    socket?.disconnect();
    super.dispose();
  }

  void connectToSocket() {
    socket = IO.io('http://192.168.1.3:5000', <String, dynamic>{
      'transports': ['websocket'],
      'autoConnect': false,
    });
    socket!.connect();
    socket!.on('metrics_update', (data) {
      setState(() {
        metrics.updateAll((key, value) => data['metrics'][key] ?? value);
        latitude = data['latitude'] ?? 30.7654865; // Use default if null
        longitude = data['longitude'] ?? 76.6105031; // Use default if null
      });
    });
  }

  String formatMetricKey(String key) {
    return key.split('_').map((str) => '${str[0].toUpperCase()}${str.substring(1)}').join(' ');
  }

  void launchMap() async {
    var url = 'https://www.google.com/maps/search/?api=1&query=$latitude,$longitude';
    if (await canLaunch(url)) {
      await launch(url);
    } else {
      throw 'Could not launch $url';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        backgroundColor: Colors.black,
        title: Text(
          'DriveAssure',
          style: TextStyle(
            color: Colors.white,
            fontSize: 25,
            fontWeight: FontWeight.bold,
          ),
        ),
        centerTitle: true,
        leading: Builder(
          builder: (context) => IconButton(
            icon: Icon(Icons.menu, color: Colors.white),
            onPressed: () => Scaffold.of(context).openDrawer(),
          ),
        ),
        elevation: 20.0,
      ),
      drawer: MyDrawer(user: user),
      body: Column(
        mainAxisAlignment: MainAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(top: 10.0, bottom: 10.0),
            child: Image.asset(
              'lib/images/chatbot-icon.png',
              width: 200,
            ),
          ),
          SizedBox(height: 50),
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8.0),
            child: Text(
              'DRIVER STATUS',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Colors.black,
              ),
            ),
          ),
          Expanded(
            child: GridView.count(
              crossAxisCount: 2,
              childAspectRatio: 3,
              padding: EdgeInsets.all(20.0),
              crossAxisSpacing: 20.0,
              mainAxisSpacing: 20.0,
              children: metrics.entries.map((entry) {
                return MetricCard(metricKey: formatMetricKey(entry.key), value: entry.value.toString());
              }).toList(),
            ),
          ),
          Align(
            alignment: Alignment.bottomLeft,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.start,
              children: [
                IconButton(
                  icon: Icon(Icons.location_on),
                  color: Colors.black,
                  onPressed: launchMap,
                ),
                Text(
                  'Driver\'s Location: $latitude, $longitude',
                  style: TextStyle(fontSize: 15, color: Colors.black87),
                ),
                
                
              ],
            ),
          ),
          SizedBox(height: 5),
                Text(
                  'Driver\'s Speed: Stoped',
                  style: TextStyle(fontSize: 15,  color: Colors.black87),
                ),
          SizedBox(height: 20.0),
          
        ],
      ),
    );
  }
}

class MetricCard extends StatelessWidget {
  final String metricKey;
  final String value;

  const MetricCard({
    Key? key,
    required this.metricKey,
    required this.value,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(vertical: 10.0, horizontal: 20.0),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10.0),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.5),
            spreadRadius: 2,
            blurRadius: 3,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            metricKey,
            style: TextStyle(
              fontSize: 14.0,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 5.0),
          Text(
            value,
            style: TextStyle(
              fontSize: 12.0,
            ),
          ),
        ],
      ),
    );
  }
}
