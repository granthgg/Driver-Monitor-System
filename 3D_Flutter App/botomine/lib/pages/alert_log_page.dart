import 'package:flutter/material.dart';

class AlertLogsPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    // Placeholder data for log entries
    final List<String> logEntries = List<String>.generate(10, (i) => "Log entry $i");

    return Scaffold(
      backgroundColor: const Color.fromARGB(255, 255, 255, 255),
      appBar: AppBar(
        backgroundColor: Color.fromARGB(255, 0, 0, 0),
        title: Text(
          'Alert Logs',
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
      body: ListView.builder(
        itemCount: logEntries.length,
        itemBuilder: (context, index) {
          return ListTile(
            title: Text(logEntries[index]),
            leading: Icon(Icons.warning, color: Colors.red),
            trailing: Text('Timestamp', style: TextStyle(color: Colors.grey)),
          );
        },
      ),
    );
  }
}
