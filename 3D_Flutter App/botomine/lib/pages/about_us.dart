import 'package:flutter/material.dart';

class AboutUsPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color.fromARGB(255, 255, 255, 255),
      appBar: AppBar(
        backgroundColor: Color.fromARGB(255, 0, 0, 0),
        title: Text(
          'About Us',
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
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            SizedBox(height: 20),
            Text(
              'Welcome to DriveAssure, the pioneer behind the groundbreaking driver activity monitoring system designed to redefine road safety. At DriveAssure, we are committed to leveraging advanced technology to create safer driving environments and reduce road accidents significantly.',
              style: TextStyle(fontSize: 16),
              textAlign: TextAlign.justify,

            ),
            SizedBox(height: 20),

            Text(
              'Our Project',
              style: TextStyle(fontSize: 25, fontWeight: FontWeight.bold),
              
            ),
            
            SizedBox(height: 20),
            Text(
              'Our flagship project, the DriveAssure, is an innovative solution that utilizes state-of-the-art computer vision and machine learning techniques to monitor driver activities in real-time. This system is engineered to detect and alert for signs of distracted or drowsy driving, ensuring immediate corrective action can be taken to prevent potential accidents.',
              style: TextStyle(fontSize: 16),
              textAlign: TextAlign.justify,
            ),
            SizedBox(height: 20),
            Text(
              'Key Features',
              style: TextStyle(fontSize: 25, fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 20),
            Text(
              '1. Real-Time Monitoring: Continuous observation of driver behavior to detect any signs of distraction or drowsiness instantly.',
              style: TextStyle(fontSize: 16),
              textAlign: TextAlign.justify,
            ),
            SizedBox(height: 10),
            Text(
              '2. Advanced Detection: Utilizes the latest YOLOv8 models and Dlib libraries for accurate and efficient detection of various driver activities.',
              style: TextStyle(fontSize: 16),
              textAlign: TextAlign.justify,
            ),
            SizedBox(height: 10),
            Text(
              '3. Alert System: Immediate feedback and alert mechanism to notify drivers of potential safety risks.',
              style: TextStyle(fontSize: 16),
              textAlign: TextAlign.justify,
            ),
            SizedBox(height: 10),
            Text(
              '4. Comprehensive Analysis: In-depth monitoring and analysis of driving patterns to identify risk factors and improve overall driving behavior.',
              style: TextStyle(fontSize: 16),
              textAlign: TextAlign.justify,
            ),
          ],
        ),
      ),
    );
  }
}
