import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:botomine/pages/about_us.dart';
import 'package:botomine/pages/home_page.dart';
import 'package:botomine/pages/alert_log_page.dart';
import 'package:botomine/pages/driver_monitor.dart';
import 'package:botomine/pages/live_feed.dart';



class MyDrawer extends StatelessWidget {
  final User user;
  final String photoURL;

  MyDrawer({required this.user})
      : photoURL = user.photoURL ?? 'C:/Users/grant/Desktop/Flutter Project/botomine/lib/images/profile_picture.png';

  void signUserOut(BuildContext context) {
    FirebaseAuth.instance.signOut();
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: MediaQuery.of(context).size.width * 0.7,
      child: Drawer(
        child: Container(
          color: Colors.white,
          child: Column(
            children: <Widget>[
              UserAccountsDrawerHeader(
                accountName: Text(user.displayName ?? 'No name', style: TextStyle(color: Colors.white)),
                accountEmail: Text(user.email ?? 'No email', style: TextStyle(color: Colors.white)),
                currentAccountPicture: CircleAvatar(
                  backgroundImage: NetworkImage(photoURL),
                ),
                decoration: BoxDecoration(
                  color: Colors.black,
                ),
              ),
              ListTile(
                leading: Icon(Icons.home, color: Colors.black),
                title: Text('Home', style: TextStyle(color: Colors.black)),
                onTap: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => HomePage()),
                  );
                },
              ),
              ListTile(
                leading: Icon(Icons.crisis_alert, color: Colors.black),
                title: Text('Alert Logs', style: TextStyle(color: Colors.black)),
                onTap: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => AlertLogsPage()),
                  );
                },
              ),
              ListTile(
                leading: Icon(Icons.monitor, color: Colors.black),
                title: Text('Live Video Feed', style: TextStyle(color: Colors.black)),
                onTap: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => LiveFeedPage()),
                  );
                },
              ),
              ListTile(
                leading: Icon(Icons.web, color: Colors.black),
                title: Text('Web Dashboard', style: TextStyle(color: Colors.black)),
                onTap: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => DriverMonitorPage()),
                  );
                },
              ),
              
              Spacer(),
              Divider(),
              ListTile(
                leading: Icon(Icons.info, color: Colors.black),
                title: Text('About Us', style: TextStyle(color: Colors.black)),
                onTap: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => AboutUsPage()),
                  );
                },
              ),
              ListTile(
                leading: Icon(Icons.logout, color: Colors.black),
                title: Text('Log Out', style: TextStyle(color: Colors.black)),
                onTap: () => signUserOut(context),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
