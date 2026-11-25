import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vision_x/main.dart';
import 'package:vision_x/theme/app_theme.dart';
import 'package:vision_x/screens/login_screen.dart';

void main() {
  group('VisionX Login UI Tests', () {
    testWidgets('renders all critical UI components', (WidgetTester tester) async {
      await tester.pumpWidget(const VisionXApp());
      await tester.pumpAndSettle();

      // Branding & Headers
      expect(find.text('Vision'), findsOneWidget);
      expect(find.text('X'), findsOneWidget);
      expect(find.text('INTELLIGENCE PLATFORM'), findsOneWidget);
      expect(find.text('Welcome to VisionX'), findsOneWidget);
      expect(
        find.text('Sign in to access your intelligent vision workspace and analytics.'),
        findsOneWidget,
      );

      // Input Fields
      expect(find.text('Email address'), findsOneWidget);
      expect(find.text('Password'), findsOneWidget);
      expect(find.byIcon(Icons.alternate_email_rounded), findsOneWidget);
      expect(find.byIcon(Icons.lock_outline_rounded), findsOneWidget);

      // Actions & Controls
      expect(find.text('Remember me'), findsOneWidget);
      expect(find.byType(Checkbox), findsOneWidget);
      expect(find.text('Forgot password?'), findsOneWidget);
      expect(find.text('Sign In'), findsOneWidget);
      expect(find.text("Don't have an account?"), findsOneWidget);
      expect(find.text('Create account'), findsOneWidget);
      expect(find.text('Protected by VisionX Secure Guard'), findsOneWidget);
    });

    testWidgets('toggles password visibility correctly', (WidgetTester tester) async {
      await tester.pumpWidget(const VisionXApp());
      await tester.pumpAndSettle();

      final textFields = find.byType(EditableText);
      expect(textFields, findsNWidgets(2));

      // Initially password field is obscured
      EditableText passwordEditable = tester.widget<EditableText>(textFields.at(1));
      expect(passwordEditable.obscureText, isTrue);
      expect(find.byIcon(Icons.visibility_outlined), findsOneWidget);

      // Tap toggle button to show password
      await tester.tap(find.byIcon(Icons.visibility_outlined));
      await tester.pumpAndSettle();

      passwordEditable = tester.widget<EditableText>(textFields.at(1));
      expect(passwordEditable.obscureText, isFalse);
      expect(find.byIcon(Icons.visibility_off_outlined), findsOneWidget);

      // Tap again to hide password
      await tester.tap(find.byIcon(Icons.visibility_off_outlined));
      await tester.pumpAndSettle();

      passwordEditable = tester.widget<EditableText>(textFields.at(1));
      expect(passwordEditable.obscureText, isTrue);
      expect(find.byIcon(Icons.visibility_outlined), findsOneWidget);
    });

    testWidgets('toggles remember me checkbox state', (WidgetTester tester) async {
      await tester.pumpWidget(const VisionXApp());
      await tester.pumpAndSettle();

      Checkbox checkbox = tester.widget<Checkbox>(find.byType(Checkbox));
      expect(checkbox.value, isFalse);

      // Tap Remember Me
      await tester.tap(find.text('Remember me'));
      await tester.pumpAndSettle();

      checkbox = tester.widget<Checkbox>(find.byType(Checkbox));
      expect(checkbox.value, isTrue);

      // Tap again to uncheck
      await tester.tap(find.text('Remember me'));
      await tester.pumpAndSettle();

      checkbox = tester.widget<Checkbox>(find.byType(Checkbox));
      expect(checkbox.value, isFalse);
    });

    testWidgets('handles input and basic form validation', (WidgetTester tester) async {
      await tester.pumpWidget(const VisionXApp());
      await tester.pumpAndSettle();

      final signInButton = find.text('Sign In');
      await tester.ensureVisible(signInButton);

      // Tap Sign In with empty fields to trigger validation
      await tester.tap(signInButton);
      await tester.pumpAndSettle();

      expect(find.text('Please enter your email'), findsOneWidget);
      expect(find.text('Please enter your password'), findsOneWidget);

      // Enter invalid email
      final emailField = find.byType(TextFormField).at(0);
      await tester.ensureVisible(emailField);
      await tester.enterText(emailField, 'invalid-email');

      await tester.ensureVisible(signInButton);
      await tester.tap(signInButton);
      await tester.pumpAndSettle();

      expect(find.text('Please enter a valid email address'), findsOneWidget);

      // Enter valid email and password
      await tester.enterText(emailField, 'alex@visionx.io');
      final passwordField = find.byType(TextFormField).at(1);
      await tester.ensureVisible(passwordField);
      await tester.enterText(passwordField, 'secret123');
      await tester.pumpAndSettle();

      // Tap Sign In
      await tester.ensureVisible(signInButton);
      await tester.tap(signInButton);
      await tester.pump();

      // Shows loading indicator during submission
      expect(find.byType(CircularProgressIndicator), findsOneWidget);

      // Advance time for simulated feedback
      await tester.pump(const Duration(milliseconds: 700));
      await tester.pumpAndSettle();

      expect(find.text('Sign in requested for alex@visionx.io'), findsOneWidget);
    });

    testWidgets('renders properly in dark mode', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.darkTheme,
          home: const LoginScreen(),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Welcome to VisionX'), findsOneWidget);
      expect(find.text('Sign In'), findsOneWidget);
    });

    testWidgets('adapts responsively to small mobile viewport without overflow', (
      WidgetTester tester,
    ) async {
      // Simulate compact 320x568 screen (e.g. iPhone SE 1st gen)
      tester.view.physicalSize = const Size(320, 568);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      await tester.pumpWidget(const VisionXApp());
      await tester.pumpAndSettle();

      // Verify no overflow error occurred
      expect(tester.takeException(), isNull);
      expect(find.text('Welcome to VisionX'), findsOneWidget);
    });

    testWidgets('adapts responsively to landscape orientation without overflow', (
      WidgetTester tester,
    ) async {
      // Simulate landscape orientation (e.g. 640x360)
      tester.view.physicalSize = const Size(640, 360);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      await tester.pumpWidget(const VisionXApp());
      await tester.pumpAndSettle();

      expect(tester.takeException(), isNull);
      expect(find.text('Welcome to VisionX'), findsOneWidget);
    });
  });
}
