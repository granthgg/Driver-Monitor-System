import 'package:flutter/material.dart';

class MyButtonhp extends StatelessWidget {
  final Function()? onTap;
  final Widget child;

  const MyButtonhp({Key? key, required this.onTap, required this.child}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(20),
        margin: const EdgeInsets.symmetric(horizontal: 20),
        decoration: BoxDecoration(
          color: Colors.black,
          borderRadius: BorderRadius.circular(10), 
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.2), 
              spreadRadius: 5, 
              blurRadius: 5, 
              offset: Offset(5, 5), 
            ),
          ],
        ),
        child: Center(child: child),
      ),
    );
  }
}
